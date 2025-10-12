from os import name

from jinja2.utils import missing
from models import db,Player,PlayerSeasonStats,PlayerAnswer,TeamAnswer,Category,DailyRiddle
from app import app
import json

from translate import is_hebrew

with open("players_tm_info.json","r",encoding="utf-8") as f:
    players_tm = json.load(f)

with open("final_dict.json","r",encoding="utf-8") as f:
    rev_matcher = json.load(f)
matcher = {val:key for key,val in rev_matcher.items()}
def find_name(name:str,names:dict):
    if name in names:
        return name
    parts = name.split()
    if len(parts) > 2:
        temp_name = parts[0] + " " + parts[2]
        if temp_name in names:
            print(f"found {temp_name} in db")
            return temp_name
    return None


with app.app_context():
    
    players_db = Player.query.all()
    missing_info = {player.player_name:player  for player in players_db if player.position is None}
    print(len(missing_info))
    count = 0
    for eng_name,player in players_tm.items():
        if player["name_in_home_country"] in matcher:
            (missing_info[matcher[player["name_in_home_country"]]]).eng_name = eng_name
            (missing_info[matcher[player["name_in_home_country"]]]).position = player["role"]
            count+=1
    print(f"found {count} players out of {len(missing_info)}")
    db.session.commit()
    players_db = Player.query.all()
    missing_info = {player.player_name:player  for player in players_db if player.position is None}
    print(len(missing_info))
    with open("bad_players.txt","w",encoding="utf-8") as f:
        for player in missing_info.keys():

            f.write(player + "\n")

    
        
