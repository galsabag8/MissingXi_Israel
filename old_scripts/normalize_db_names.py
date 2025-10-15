import json
from models import db,Player
from app import app

exclude = {"בן","אל","אבו"}
with open("multi_db.json","r",encoding="utf-8") as f:
    names = json.load(f)


with app.app_context():
    count=0
    players = Player.query.all()
    for player in players:
        if player.player_name in names and names[player.player_name]!="":
            player.player_name = names[player.player_name]
            count+=1
    print(f"updated{count} players out of{len(names)}")
    db.session.commit()
    """
    multi_names = {}
    for player in players:
        player.player_name.strip()
        words = player.player_name.split()
        if len(words) > 2 and words[1] not in exclude:
            multi_names[player.player_name] = ""
    db.session.commit()
    with open("multi_db.json","w",encoding="utf-8") as f:
        json.dump(multi_names,f,ensure_ascii=False,indent=2)
    """

