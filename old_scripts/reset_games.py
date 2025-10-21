import json
with open("seasons.json","r",encoding="utf-8") as f:
    seasons = json.load(f)
for season in seasons.values():
        for fixture in season["games"].values():
            for game in fixture:
                if "formation" in game["home team"]:
                    game["home team"].pop("formation")
                if "formation" in game["away team"]:
                    game["away team"].pop("formation")
                if "error" in game["home team"]:
                    game["home team"].pop("error")
                if "error" in game["away team"]:
                    game["away team"].pop("error")
                if "error" in game:
                    game.pop("error")

with open("seasons.json","w",encoding="utf-8") as f:
        json.dump(seasons,f,ensure_ascii=False,indent=2)
