import json
from models import db,Player
from app import app



# --- Load JSON ---
with open("seasons.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# --- Load team names from txt (strip whitespace) ---
with app.app_context():

    players = Player.query.order_by(Player.player_name).all()
    db_names = {player.player_name for player in players}

# --- Extract all team names from JSON ---
    json_players = set()
    for season, season_data in data.items():
        for fixture_id, games in season_data["games"].items():
            for game in games:
                home_lu = game["home team"]["lineup"]
                home_subs = game["home team"]["subs"]
                away_lu = game["away team"]["lineup"]
                away_subs = game["away team"]["subs"]
                for playerh,playera in zip(home_lu,away_lu):
                    json_players.add(playera["name"])
                    json_players.add(playerh["name"])

                for player in home_subs:
                    json_players.add(player["name"])
                for player in away_subs:
                    json_players.add(player["name"])


    # --- Find missing ---
    missing = json_players - db_names
    print(len(missing))

    with open("missing_players.txt","w",encoding="utf-8") as f:
        for player in missing:
            f.write(player + "\n")
    