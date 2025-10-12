import json
from models import db,Player
from app import app
from translate import is_hebrew
from collections import Counter
import itertools


HEBREW_LETTERS = [
    'א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט',
    'י', 'כ', 'ך', 'ל', 'מ', 'ם', 'נ', 'ן', 'ס',
    'ע', 'פ', 'ף', 'צ', 'ץ', 'ק', 'ר', 'ש', 'ת'
]
def make_hist(name:str):
    counts = Counter(ch for ch in name if ch in HEBREW_LETTERS)

# Build a fixed-length array (27 positions)
    histogram = [counts.get(letter, 0) for letter in HEBREW_LETTERS]
    return histogram


def percentage(name1:str,name2:str,check=False):
    name1_arr = name1.split()
    name2_arr = name2.split()
    if len(name1_arr) != len(name2_arr):
        arr1,arr2 = [],[]
        for i in range(1,len(name1_arr),1):
            arr1.append(name1_arr[0] + " " + name1_arr[i])
        for i in range(1,len(name2_arr),1):
            arr2.append(name2_arr[0] + " " + name2_arr[i])
        per = 0
        for n1,n2 in itertools.product(arr1,arr2):
            per = max(per,percentage(n1,n2))

    idx,sumo,rev_per = 0,0,0
    if len(name1_arr) == 2 and not check:
        rev1 = name1_arr[1] + " " + name1_arr[0]
        rev_per = percentage(rev1,name2,check=True)
    for n1 , n2 in zip(name1_arr,name2_arr):
        penalty = 0
        idx+=1
        hist1,hist2 = make_hist(n1),make_hist(n2)
        orig_len = len(n2)
        for i,j in zip(hist1,hist2):
            penalty+=abs(i-j)
        sumo+=(1-(penalty/orig_len))
    return max(rev_per,sumo/idx)
    

def find_closest_name(name:str,names:set):
    maxi = float('-inf')
    curr = None
    for n in names:
        per = percentage(name,n)
        if n == "בלו ירו" and name == "ירו בלו":
            print(per)
        if per > maxi:
            maxi = per
            curr = n
    return curr,maxi

with open("players_tm_info.json","r",encoding="utf-8") as f:
    players_tm = json.load(f)

with open("english_names.json","r",encoding="utf-8") as f:
    eng_heb = json.load(f)


with open("players_db_wo_pos.txt","r",encoding="utf-8") as f:
    players_wo_pos = set(line.strip() for line in f)

with app.app_context():
    matcher = {}
    players_db = Player.query.all()
    names = {player.player_name:player  for player in players_db}
    for name,player_tm in players_tm.items():
        if (player_tm["name_in_home_country"] in names and (names[player_tm["name_in_home_country"]]).position is not None):
            continue
        save,per = find_closest_name(player_tm["name_in_home_country"],players_wo_pos)
        json_name= player_tm["name_in_home_country"]
        if per < 0.6666666666666667:
            continue
        if save not in matcher:
            matcher[save] = (json_name,per)
        else:
            if per > matcher[save][1]:
                matcher[save] = (json_name,per)
    print(f"found match for {len(matcher)} out of {len(players_wo_pos)} players")
    reverse_matcher = {val[0]:key for key,val in matcher.items()}
    with open("matcher.json","w",encoding="utf-8") as f:
        json.dump(matcher,f,ensure_ascii=False,indent=2)
    
    with open("reverse_matcher.json","w",encoding="utf-8") as f:
        json.dump(reverse_matcher,f,ensure_ascii=False,indent=2)

    with open("players_tm_info.json","w",encoding="utf-8") as f:
         json.dump(players_tm,f,ensure_ascii=False,indent=2)