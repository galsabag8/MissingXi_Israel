import json
from models import db,Match
from app import app

with app.app_context():
    matches = Match.query.all()
    matches_dict = {match.competition:match.id for match in matches}
    with open("match_ids.json","w",encoding="utf-8") as f:
        json.dump(matches_dict,f,ensure_ascii=False,indent=2)
    