import json
from app import app
from models import db,TeamFormation
with open("seasons.json","r",encoding="utf-8") as f:
    seasons = json.load(f)
with open("team_ids.json","r",encoding="utf-8") as f:
    teams_ids=json.load(f)
with open("match_ids.json","r",encoding="utf-8") as f:
    match_ids=json.load(f)
with app.app_context():
    count=0
    formations = TeamFormation.query.all()
    formations_dict = {}
    for formation in formations:
        # If the match_id is not yet a key, add it with an empty dictionary
        if formation.match_id not in formations_dict:
            formations_dict[formation.match_id] = {}
        # Add the team_id and the formation object
        formations_dict[formation.match_id][formation.team_id] = formation
    for season_name, season in seasons.items():
            for fixture_num, fixture in season["games"].items():
                for game in fixture:
                    if "error" in game and game["error"]:
                        continue
                    if "error" in game["home team"] or "error" in game["away team"]:
                        continue
                    home_team, away_team = game["home team"]["name"], game["away team"]["name"]
                    home_team_id,away_team_id= teams_ids[home_team],teams_ids[away_team]
                    competition = f"ליגת ווינר עונה {season_name} מחזור {fixture_num}: {home_team}-{away_team}"
                    match_id = match_ids.get(competition)
                    #print(match_id,home_team_id)
                    home_team_formation = formations_dict[match_id][home_team_id]
                    away_team_formation = formations_dict[match_id][away_team_id]
                    if home_team_formation.formation != game["home team"]["formation"]:
                        home_team_formation.formation = game["home team"]["formation"]
                        count+=1
                    if away_team_formation.formation != game["away team"]["formation"]:
                        away_team_formation.formation = game["away team"]["formation"]
                        count+=1
    print(f"changed {count} tuples")
    db.session.commit()             

