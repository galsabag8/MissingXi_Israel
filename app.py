from flask import Flask, jsonify, request, session, render_template
import os
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, Player, Team
# Import the new game logic functions (start_new_game, check_guess, get_game_state)
from game_logic import start_new_game, check_guess, get_game_state,NUM_MATCHES 

app = Flask(__name__)

# Secret key (required for sessions)
# In production, set this in Render's environment variables
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    # NOTE: Set a strong SECRET_KEY in your environment variables for production!
    raise ValueError("SECRET_KEY environment variable not set!")

# Database config
# DATABASE_URL should be set in Render environment variables
# Fallback to local dev DB if running locally
database_url = os.getenv("DATABASE_URL")
if not database_url:
    # NOTE: Remember to remove this exposed local DB URI before any final push!
    database_url = "postgresql://postgres:password@localhost:5432/top10game" 
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Session config
app.config["PERMANENT_SESSION_LIFETIME"] = int(
    os.getenv("SESSION_TTL_SECONDS", str(7 * 24 * 60 * 60))
)
app.config["SESSION_COOKIE_SAMESITE"] = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
app.config["SESSION_COOKIE_SECURE"] = (
    os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
)

# Initialize SQLAlchemy
db.init_app(app)
migrate = Migrate(app, db)

# -----------------------------
# Routes
# -----------------------------

@app.route("/")
def home():
    return render_template("play.html")


@app.before_request
def _make_session_permanent():
    session.permanent = True

@app.route("/about")
def about():
    # Updated text for the new game concept
    return "This is a prediction game based on Israeli soccer data and starting lineups."



@app.route("/start_game", methods=["GET"])
def start_game():
    """
    Starts a new game session by choosing a random match and lineup.
    """
    game_state = start_new_game()
    if "error" in game_state:
        # Returns 400 if no matches or lineups are found in the database
        return jsonify(game_state), 400
    
    return jsonify(game_state)

@app.route("/guess", methods=["POST"])
def guess():
    """
    Submits a player guess and checks it against the lineup for a specific slot.
    """
    data = request.json
    player_guess = data.get("player")
    slot_index = data.get("slot_index") # NEW: Receive the target slot index (1-based)

    if not player_guess:
        return jsonify({"error": "No player name submitted."}), 400
    if not isinstance(slot_index, int) or slot_index < 1 or slot_index > 11:
         return jsonify({"error": "Invalid slot index submitted."}), 400

    # Pass BOTH the index and the guess to the updated check_guess function
    result = check_guess(slot_index=slot_index, player_guess=player_guess)
    return jsonify(result)

@app.route("/state", methods=["GET"])
def state():
    """
    Returns current game state for this user (including exposed players and metadata).
    """
    result = get_game_state()
    if "error" in result:
        # If no game is active, prompt the user to start one
        return jsonify(result), 400
        
    return jsonify(result)

@app.route("/search", methods=["GET"])
def search():
    """
    Autocomplete search for players/teams. Requires q>=3 characters.
    Returns up to 10 of each type.
    """
    q = request.args.get('q', '').strip()
    if len(q) < 3:
        return jsonify({"players": [], "teams": []})

    # Case-insensitive contains search
    pattern = f"%{q}%"
    players = Player.query.filter(
        (Player.player_name.ilike(pattern)) 
    ).limit(10).all()
    teams = Team.query.filter(
        (Team.team_name.ilike(pattern))
    ).limit(10).all()

    return jsonify({
        "players": [{"id": p.id, "name":  p.player_name} for p in players],
        "teams": [{"id": t.id, "name": t.team_name} for t in teams]
    })

# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)