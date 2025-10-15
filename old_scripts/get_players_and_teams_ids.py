import json
from models import db,Player,Team
from app import app

with app.app_context():
    players = Player.query.all()
    teams = Team.query.all()
    players_id = {player.player_name:player.id for player in players}
    teams_id = {team.team_name:team.id for team in teams}
    with open("team_ids.json","w",encoding="utf-8") as f:
        json.dump(teams_id,f,ensure_ascii=False,indent=2)
    with open("player_ids.json","w",encoding="utf-8") as f:
        json.dump(players_id,f,ensure_ascii=False,indent=2)