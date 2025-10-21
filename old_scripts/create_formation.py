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
TBH_DEF = ["4","26"]
def get_pos(name:str,player_pos:dict,changed:dict):
    pos = ""
    if name in player_pos:
        return player_pos[name]
    if name in changed:
        return player_pos[changed[name]]
    return None

def fix_formation(d,m,a):
    if len(a) > 4:
        a,m=move_attack_midfield(a,m)
    if len(m) > 5:
        if len(d)>=4:
            m,a=move_midfield_attack(m,a)
        else:
            m,d=move_midfield_defence(m,d)
    if len(d) > 5:
        d,m=move_defence_midfield(d,m)
    if len(d) < 3:
        print(f"formation before:{len(d)}-{len(m)}-{len(a)}")
        move_midfield_defence(m,d)
        print(f"formation after:{len(d)}-{len(m)}-{len(a)}")
    if len(a) == 0:
        move_midfield_attack(m,a)
    return d,m,a
    
def move_attack_midfield(a: list, m: list):
    player_to_move = None
    new_pos = None

    # Iterate safely by creating a copy or iterating by index in reverse
    # Easiest way: Find the player first, then modify lists outside the loop.

    # Prioritize finding a winger
    for player in a:
        if player["game_pos"] == "Left Winger":
            player_to_move = player
            new_pos = "Left Midfield"
            break # Found one, stop looking
        elif player["game_pos"] == "Right Winger":
            player_to_move = player
            new_pos = "Right Midfield"
            break # Found one, stop looking

    # If no winger was found AND the attack list is not empty, take the first attacker
    if player_to_move is None and a: # Check if 'a' is not empty
        player_to_move = a[0]
        new_pos = "Attacking Midfield"

    # If we found a player to move
    if player_to_move:
        player_to_move["game_pos"] = new_pos # Correctly assign the new position
        a.remove(player_to_move)       # Now it's safe to remove
        m.append(player_to_move)       # Add to midfield list

    # Return the modified lists (even if no player was moved)
    return a, m

def move_midfield_defence(m: list, d: list):
    player_to_move = None
    new_pos = None

    # Iterate safely by creating a copy or iterating by index in reverse
    # Easiest way: Find the player first, then modify lists outside the loop.

    # Prioritize finding a winger
    for player in m:
        if player["game_pos"] == "Left Midfield":
            player_to_move = player
            new_pos = "Left-Back"
            break # Found one, stop looking
        elif player["game_pos"] == "Right Midfield":
            player_to_move = player
            new_pos = "Right-Back"
            break # Found one, stop looking

    # If no winger was found AND the attack list is not empty, take the first attacker
    if player_to_move is None and m: # Check if 'a' is not empty
        player_to_move = m[0]
        new_pos = "Defender"

    # If we found a player to move
    if player_to_move:
        player_to_move["game_pos"] = new_pos # Correctly assign the new position
        m.remove(player_to_move)       # Now it's safe to remove
        d.append(player_to_move)       # Add to midfield list

    # Return the modified lists (even if no player was moved)
    return m, d


def move_midfield_attack(m: list, a: list):
    player_to_move = None
    new_pos = None

    # Iterate safely by creating a copy or iterating by index in reverse
    # Easiest way: Find the player first, then modify lists outside the loop.

    # Prioritize finding a winger
    for player in m:
        if player["game_pos"] == "Left Midfield":
            player_to_move = player
            new_pos = "Left Winger"
            break # Found one, stop looking
        elif player["game_pos"] == "Right Midfield":
            player_to_move = player
            new_pos = "Right Winger"
            break # Found one, stop looking

    # If no winger was found AND the attack list is not empty, take the first attacker
    if player_to_move is None and m: # Check if 'a' is not empty
        player_to_move = m[0]
        new_pos = "Second Striker"

    # If we found a player to move
    if player_to_move:
        player_to_move["game_pos"] = new_pos # Correctly assign the new position
        m.remove(player_to_move)       # Now it's safe to remove
        a.append(player_to_move)       # Add to midfield list

    # Return the modified lists (even if no player was moved)
    return m, a

def move_defence_midfield(d: list, m: list):
    player_to_move = None
    new_pos = None

    # Iterate safely by creating a copy or iterating by index in reverse
    # Easiest way: Find the player first, then modify lists outside the loop.

    # Prioritize finding a winger
    for player in d:
        if player["game_pos"] == "Left-Back":
            player_to_move = player
            new_pos = "Left Midfield"
            break # Found one, stop looking
        elif player["game_pos"] == "Right-Back":
            player_to_move = player
            new_pos = "Right Midfield"
            break # Found one, stop looking

    # If no winger was found AND the attack list is not empty, take the first attacker
    if player_to_move is None and d: # Check if 'a' is not empty
        player_to_move = d[0]
        new_pos = "Midfielder"

    # If we found a player to move
    if player_to_move:
        player_to_move["game_pos"] = new_pos # Correctly assign the new position
        d.remove(player_to_move)       # Now it's safe to remove
        m.append(player_to_move)       # Add to midfield list

    # Return the modified lists (even if no player was moved)
    return d, m


    
    
    
    
with app.app_context():
    good,bad=0,0
    players = Player.query.all()
    player_pos = {player.player_name:player.position for player in players}
    for season in seasons.values():
        for fixture in season["games"].values():
            for game in fixture:
                d_home,m_home,a_home=[],[],[]
                d_away,m_away,a_away = [],[],[]
                home_lu,away_lu=game["home team"]["lineup"],game["away team"]["lineup"]
                if len(home_lu) < 11 or len(away_lu) < 11:
                    game["error"] = "one of the teams has invalid lineup amount"
                    continue
                if len(home_lu) > 11 or len(away_lu) > 11:
                    game["check"] = "one of the teams has 12 players"
                    continue
                for playerh,playera in zip(home_lu,away_lu):
                    pos = get_pos(playerh["name"].strip(),player_pos,changed)
                    if playerh["name"] == "טל בן חיים":
                        if playerh["number"] in TBH_DEF:
                            pos = "Centre-Back"
                        else:
                            pos = "Left Winger"

                    if pos and pos in DEFENCE:
                        d_home.append(playerh)
                    elif pos and pos in MIDFIELD:
                        m_home.append(playerh)
                    elif pos and pos in ATTACK:
                        a_home.append(playerh)
                    playerh["game_pos"] = pos
                    pos = get_pos(playera["name"].strip(),player_pos,changed)
                    if playera["name"] == "טל בן חיים":
                        if playera["number"] in TBH_DEF:
                            pos = "Centre-Back"
                        else:
                            pos = "Left Winger"
                    if pos and pos in DEFENCE:
                        d_away.append(playera)
                    elif pos and pos in MIDFIELD:
                        m_away.append(playera)
                    elif pos and pos in ATTACK:
                        a_away.append(playera)
                    playera["game_pos"] = pos
                check = max(len(a_home),len(m_home),len(d_home))
                if check > 5:
                    print(f"home formation before is {len(d_home)}-{len(m_home)}-{len(a_home)}")
                while max(len(a_home),len(m_home),len(d_home))> 5 or len(d_home) < 3 or len(a_home) == 0 or len(a_home) > 4:
                    d_home,m_home,a_home =  fix_formation(d_home,m_home,a_home)
                while max(len(a_away),len(m_away),len(d_away)) > 5 or len(d_away) < 3 or len(a_away) == 0 or len(a_away) > 4:
                    d_away,m_away,a_away =  fix_formation(d_away,m_away,a_away)
                
                if check > 5:
                    print(f"home formation after is {len(d_home)}-{len(m_home)}-{len(a_home)}")
                if len(d_home)+len(m_home)+len(a_home) == 10:
                    game["home team"]["formation"] = f"{len(d_home)}-{len(m_home)}-{len(a_home)}"
                    good+=1
                else:
                    game["home team"]["incomplete_formation"] = f"{len(d_home)}-{len(m_home)}-{len(a_home)}"

                
                if len(d_away)+len(m_away)+len(a_away) == 10:
                    game["away team"]["formation"] = f"{len(d_away)}-{len(m_away)}-{len(a_away)}"
                    good+=1
                else:
                    game["away team"]["incomplete_formation"]=f"{len(d_away)}-{len(m_away)}-{len(a_away)}"


    print(f"found {good} good formations out of {good+bad}")
    with open("seasons.json","w",encoding="utf-8") as f:
        json.dump(seasons,f,ensure_ascii=False,indent=2)

                
                
                



