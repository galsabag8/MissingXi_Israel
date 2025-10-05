from models import db, Team
from app import app
import json

with open("seasons.json","r",encoding="utf-8") as f:
    seasons = json.load(f)

teams = {}

for season in seasons.values():
    for fixture in season["games"].values():
        for game in fixture:
            if game["home team"]["name"] not in teams:
                teams[game["home team"]["name"]] = game["home team"]["team_img"]
            if game["away team"]["name"] not in teams:
                teams[game["away team"]["name"]] = game["away team"]["team_img"]

with app.app_context():
    count = 0
    for team,img in teams.items():
        if len(img) == 0:
            continue
        team_db = Team.query.filter_by(team_name=team).first()
        if team_db:
            team_db.team_img_url = img
            print(f"{team} successfully updated")
            count+=1
    db.session.commit()
    print(count)

