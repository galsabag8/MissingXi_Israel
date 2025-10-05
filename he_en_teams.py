import json

with open("seasons.json", "r", encoding="utf-8") as f:
    data = json.load(f)

teams = {}

for season, season_data in data.items():
        for fixture_id, games in season_data["games"].items():
            for game in games:
                if game["home team"]["name"] not in teams:
                    teams[game["home team"]["name"]] = ""

                if game["away team"]["name"] not in teams:
                    teams[game["away team"]["name"]] = ""


with open("he_en_team_names.json", "w", encoding="utf-8") as f:
    data = json.dump(teams,f,ensure_ascii=False,indent=2)
                    