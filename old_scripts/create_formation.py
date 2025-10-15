import json
from os import name
from app import app
from models import db,Player
with open("seasons.json","r",encoding="utf-8") as f:
    seasons = json.load(f)
with open("changed_names.json","r",encoding="utf-8") as f:
    changed = json.load(f)

DEFENCE = {"Right-Back","Left-Back","Centre-Back","Defender"}
MIDFIELD = {"Central Midfield","Right Midfield","Left Midfield","Midfielder","Attacking Midfield","Defensive Midfield"}
ATTACK = {"Second Striker","Left Winger","Centre-Forward","Striker","Right Winger"}

def get_pos(name:str,player_pos:dict,changed:dict):
    pos = ""
    if name in player_pos:
        return player_pos[name]
    if name in changed:
        return player_pos[changed[name]]
    return None

def fix_formation(d,m,a):
    if a > 4:
        a-=1
        m+=1
    if m > 5:
        m-=1
        if d>=4:
            a+=1
        else:
            d+=1
    if d > 5:
        d-=1
        m+=1
    
    
    
    
    return d,m,a
with app.app_context():
    good,bad=0,0
    players = Player.query.all()
    player_pos = {player.player_name:player.position for player in players}
    for season in seasons.values():
        for fixture in season["games"].values():
            for game in fixture:
                d_home,m_home,a_home=0,0,0
                d_away,m_away,a_away = 0,0,0
                home_lu,away_lu=game["home team"]["lineup"],game["away team"]["lineup"]
                for playerh,playera in zip(home_lu,away_lu):
                    pos = get_pos(playerh["name"].strip(),player_pos,changed)
                    if pos and pos in DEFENCE:
                        d_home+=1
                    elif pos and pos in MIDFIELD:
                        m_home+=1
                    elif pos and pos in ATTACK:
                        a_home+=1
                    pos = get_pos(playera["name"].strip(),player_pos,changed)
                    if pos and pos in DEFENCE:
                        d_away+=1
                    elif pos and pos in MIDFIELD:
                        m_away+=1
                    elif pos and pos in ATTACK:
                        a_away+=1
                check = max(a_home,m_home,d_home)
                if check > 5:
                    print(f"home formation before is {d_home}-{m_home}-{a_home}")
                while max(a_home,m_home,d_home) > 5:
                    d_home,m_home,a_home =  fix_formation(d_home,m_home,a_home)
                while max(d_away,m_away,a_away) > 5:
                    d_away,m_away,a_away =  fix_formation(d_away,m_away,a_away)
                check2 = max(a_home,m_home,d_home)

                if check > 5:
                    print(f"home formation after is {d_home}-{m_home}-{a_home}")
                if d_home+m_home+a_home == 10:
                    game["home team"]["formation"] = f"{d_home}-{m_home}-{a_home}"
                    good+=1

                else:
                    game["home team"]["error"] = f"invalid formation:currently {d_home}-{m_home}-{a_home} "
                    bad+=1

                if d_away+m_away+a_away == 10:
                    game["away team"]["formation"] = f"{d_away}-{m_away}-{a_away}"
                    good+=1
                else:
                    game["away team"]["error"] = f"invalid formation:currently {d_away}-{m_away}-{a_away} "
                    bad+=1

    print(f"found {good} good formations out of {good+bad}")
    with open("seasons.json","w",encoding="utf-8") as f:
        json.dump(seasons,f,ensure_ascii=False,indent=2)

                
                
                



