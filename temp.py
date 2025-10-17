from models import db, MatchLineup, MatchSubs,Player
import json
from app import app

with app.app_context():
    players = Player.query.all()
    print(len(players))
    for i in range(5):
        print(players[i].player_name)
