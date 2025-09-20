import json
from models import db, Player, Team, PlayerAnswer, Category
from app import app

def insert_to_db() -> None:
    with app.app_context():
        db.drop_all()
        db.create_all()
        with open("players.json", "r", encoding="utf-8") as f:
            players = json.load(f)
            #print(players)
        for player in players:
            team_name = player["team"]
            t = Team(team_name=team_name)
            db.session.add(t)
            for p in player["players"]:
                player_name = p["name_heb"]
                player_image_url = p["image_url"]
                p = Player(player_name=player_name,player_image_url=player_image_url)
                db.session.add(p)
        db.session.commit()

if __name__ == "__main__":
    insert_to_db()