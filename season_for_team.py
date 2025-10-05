import json

with open("seasons.json", "r", encoding="utf-8") as f:
    data = json.load(f)

teams = {}

season_to_start_year = {
     "09/10":2009,
     "10/11":2010,
     "11/12":2011,
     "12/13":2012,
     "13/14":2013,
     "14/15":2014,
     "15/16":2015,
     "16/17":2016,
     "17/18":2017,
     "18/19":2018,
     "19/20":2019,
     "20/21":2020,
     "21/22":2021,
     "22/23":2022,
     "23/24":2023,
     "24/25":2024,
     "25/26":2025
}

for season, season_data in data.items():
        for fixture_id, games in season_data["games"].items():
            for game in games:
                if game["home team"]["name"] in teams:
                    if teams[game["home team"]["name"]][-1] != season_to_start_year[season]:
                        teams[game["home team"]["name"]].append(season_to_start_year[season])
                else:
                    teams[game["home team"]["name"]] = [season_to_start_year[season]]

                if game["away team"]["name"] in teams:
                    if teams[game["away team"]["name"]][-1] != season_to_start_year[season]:
                        teams[game["away team"]["name"]].append(season_to_start_year[season])
                else:
                    teams[game["away team"]["name"]] = [season_to_start_year[season]]

#print(type(teams))

with open("season-teams.json","w",encoding="utf-8") as f:
    json.dump(teams,f,ensure_ascii=False,indent=2)
