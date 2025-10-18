import json
from models import db,MatchEvent,MatchLineup,MatchSubs,Player
from app import app

with open("seasons.json","r",encoding="utf-8") as f:
    seasons=json.load(f)

with open("match_ids.json","r",encoding="utf-8") as f:
    match_ids=json.load(f)

with open("team_ids.json","r",encoding="utf-8") as f:
    teams_ids=json.load(f)

striker_nums = ["14","11","7","12"]
defender_nums = ["4","26"]
TBH = "טל בן חיים"


def add_event(id:int,match_id:int,player_dict:dict,team_id:id):
    count=0
    if "yellow" in player_dict and player_dict["yellow"] == True:
        db.session.add(MatchEvent(match_id=match_id,player_id=id,team_id=team_id,event_type="yellow card"))
        count+=1
    if "red" in player_dict and player_dict["red"] == True:
        db.session.add(MatchEvent(match_id=match_id,player_id=id,team_id=team_id,event_type="red card"))
        count+=1
    if "goals" in player_dict and player_dict["goals"] > 0:
        num = player_dict["goals"]
        db.session.add(MatchEvent(match_id=match_id,player_id=id,team_id=team_id,event_type=f"{num} goals"))
        count+=1
    return count


with app.app_context():
    count=0
    event_count=0
    tbh_striker = Player.query.filter_by(player_name="טל בן חיים",position="Left Winger").first()
    tbh_defender = Player.query.filter_by(player_name="טל בן חיים",position="Centre-Back").first()
    striker_id,def_id=tbh_striker.id,tbh_defender.id
    for season_name, season in seasons.items():
            for fixture_num, fixture in season["games"].items():
                for game in fixture:
                    if "error" in game and game["error"]:
                        continue
                    home_team, away_team = game["home team"]["name"], game["away team"]["name"]
                    competition = f"ליגת ווינר עונה {season_name} מחזור {fixture_num}: {home_team}-{away_team}"
                    match_id = match_ids.get(competition)
                    for team_key in ["home team", "away team"]:
                        for player_dict in game[team_key]["lineup"]:
                            team_id = teams_ids[game[team_key]["name"]]
                            if player_dict["name"] == TBH:
                                if player_dict["number"] in defender_nums:
                                    db.session.add(MatchLineup(player_id=def_id,match_id=match_id,jersey_number=player_dict["number"],team_id=team_id))
                                    count+=1
                                    event_count+=add_event(def_id,match_id,player_dict,team_id)
                                elif player_dict["number"] in striker_nums:
                                    db.session.add(MatchLineup(player_id=striker_id,match_id=match_id,jersey_number=player_dict["number"],team_id=team_id))
                                    count+=1
                                    event_count+=add_event(def_id,match_id,player_dict,team_id)
                                else:
                                    number=player_dict["number"]
                                    print(f"didnt find match for number {number}")
                            
                        for player_dict in game[team_key]["subs"]:
                            team_id = teams_ids[game[team_key]["name"]]
                            if player_dict["name"] == TBH:
                                if player_dict["number"] in defender_nums:
                                    db.session.add(MatchSubs(player_id=def_id,match_id=match_id,jersey_number=player_dict["number"],team_id=team_id))
                                    count+=1
                                    event_count+=add_event(def_id,match_id,player_dict,team_id)
                                elif player_dict["number"] in striker_nums:
                                    db.session.add(MatchSubs(player_id=striker_id,match_id=match_id,jersey_number=player_dict["number"],team_id=team_id))
                                    count+=1
                                    event_count+=add_event(def_id,match_id,player_dict,team_id)
                                else:
                                    number=player_dict["number"]
                                    print(f"didnt find match for number {number}")
    
    print(f"added {count} subs,lineup")
    print(f"added {event_count} events")
    db.session.commit()


