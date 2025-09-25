from flask import Flask, jsonify, request, session, render_template
import os
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from models import db, Player, Team
from game_logic import load_daily_riddle, check_guess, get_game_state

app = Flask(__name__)

# Secret key (required for sessions)
# In production, set this in Render's environment variables
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable not set!")

# Database config
# DATABASE_URL should be set in Render environment variables
# Fallback to local dev DB if running locally
database_url = os.getenv("DATABASE_URL")
if not database_url:
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

# -----------------------------
# Routes
# -----------------------------

@app.route("/")
def home():
    return "שלום, זה האתר שלי!"


@app.before_request
def _make_session_permanent():
    session.permanent = True

@app.route("/about")
def about():
    return "זה יהיה משחק הטופ 10 בכדורגל הישראלי."

@app.route("/play_temp")
def play():
    return render_template("play_temp.html")

@app.route("/start_game", methods=["GET"])
def start_game():
    riddle = load_daily_riddle()
    if "error" in riddle:
        return jsonify(riddle), 400
    today_iso = datetime.now(timezone.utc).date().isoformat()
    exposed_key = f"exposed:{today_iso}"
    finished_key = f"finished:{today_iso}"
    session[exposed_key] = [0] * len(riddle["answers"])
    session[finished_key] = False
    return jsonify({
        "message": "Game started!",
        "riddle_date": riddle["riddle_date"],
        "category": riddle["category"],
        "exposed": session[exposed_key],
        "finished": session[finished_key]
    })

@app.route("/guess", methods=["POST"])
def guess():
    data = request.json
    player_guess = data.get("player")
    if not player_guess:
        return jsonify({"error": "No player submitted."}), 400

    result = check_guess(player_guess)
    return jsonify(result)

@app.route("/state", methods=["GET"])
def state():
    """
    Returns current game state for this user
    """
    result = get_game_state()
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

    # Case-insensitive contains search; for Hebrew consider adding unaccent/normalization later
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
