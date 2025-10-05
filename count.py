import json

with open("players_tm_info.json","r",encoding="utf-8") as f:
    players = json.load(f)

count = 0
for player in players.keys():
    if "name_in_home_country"  not in players[player] or players[player]["name_in_home_country"] == "":
        count+=1

print(f"there are {count} players without name in home country")