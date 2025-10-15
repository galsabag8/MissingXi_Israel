import json
with open("seasons.json","r",encoding="utf-8") as f:
    seasons = json.load(f)
count=0
for season_name, season in seasons.items():
        for fixture_num, fixture in season["games"].items():
            for game in fixture:
                if "error" in game["home team"]:
                    count+=1
                if "error" in game["away team"]:
                    count+=1
print(f"marked {count} games as fucked")
"""
with open("seasons.json","w",encoding="utf-8") as f:
     json.dump(seasons,f,ensure_ascii=False,indent=2)
"""