from models import db,Player
from app import app

with app.app_context():
   players =  Player.query.all()
   count=0
   with open("players_db_wo_pos.txt","w",encoding="utf-8") as f:
    for player in players:
        if player.position is None:
            count+=1
            f.write(player.player_name + "\n")
    print(f"{count} players left without position")