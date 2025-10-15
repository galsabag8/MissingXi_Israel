import re
import json


def detect_languages(text):
    langs = set()
    if re.search(r'[\u0590-\u05FF]', text):  # Hebrew range
        langs.add("hebrew")
    if re.search(r'[A-Za-z]', text):         # English letters
        langs.add("english")
    if re.search(r'[\u0600-\u06FF]', text):  # Arabic
        langs.add("arabic")
    if re.search(r'[\u0400-\u04FF]', text):  # Cyrillic
        langs.add("cyrillic")
    # Add more ranges if needed
    return langs

def has_multiple_languages(text):
    langs = detect_languages(text)
    return len(langs) > 1
def keep_hebrew_only(text):
    # Keep only Hebrew letters (Unicode \u0590–\u05FF) and spaces
    return re.sub(r'[^א-ת\s]', '', text)

with open("players_tm_info.json","r",encoding="utf-8") as f:
    players_tm = json.load(f)
with open("multi_lang.txt","w",encoding="utf-8") as f:
    for player in players_tm.values():
        if has_multiple_languages(player["name_in_home_country"]):
            f.write(player["name_in_home_country"]+"\n")
            player["name_in_home_country"] = keep_hebrew_only(player["name_in_home_country"])
            f.write(player["name_in_home_country"]+"\n")
