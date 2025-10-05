from models import db,Player
from app import app
import json

with open("missing_players_img.json","r",encoding="utf-8") as f:
    missing = json.load(f)

with app.app_context():
    for name , img in missing.items():
        player = Player(player_name=name,player_image_url=img)
        db.session.add(player)
    db.session.commit()