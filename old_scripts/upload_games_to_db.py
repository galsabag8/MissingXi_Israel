from models import db,Match,MatchEvent,MatchLineup,MatchSubs,TeamFormation
from app import app
import json
from sqlalchemy.exc import IntegrityError
from datetime import datetime


with open("seasons.json","r",encoding="utf-8") as f:
    seasons = json.load(f)
with open("changed_names.json","r",encoding="utf-8") as f:
    changed = json.load(f)
with open("player_ids.json","r",encoding="utf-8") as f:
    player_ids = json.load(f)
with open("team_ids.json","r",encoding="utf-8") as f:
    team_ids = json.load(f)


def get_player_id(name:str,player_ids:dict,changed:dict):
    if name in player_ids:
        return player_ids[name]
    elif name in changed:
        return player_ids[changed[name]]
    return None

def get_events(player:dict):
    ret = []
    if player["yellow"]:
        ret.append("yellow card")
    if player["red"]:
        ret.append("red card")
    if player["goals"] > 0:
        goals = player["goals"]
        ret.append(f"{goals} goals")
    return ret


def get_game_data(game:dict,season_name:str,fixture_num:str,player_ids:dict,team_ids:dict,changed:dict):
    home_team = game["home team"]["name"].strip()
    home_score = game["home team"]["score"]
    away_score = game["away team"]["score"]
    away_team = game["away team"]["name"].strip()
    home_team_id = team_ids[home_team]
    away_team_id = team_ids[away_team]
    date_str = game["date"].strip() # ניקוי רווחים מהתאריך
    
    try:
        # 1. ניסיון פורמט מלא (YYYY-MM-DD HH:MM:SS)
        match_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            # 2. ניסיון פורמט יום-חודש-שנה (DD/MM/YYYY) + שעה
            match_date = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
        except ValueError:
            try:
                # 3. ניסיון פורמט יום-חודש-שנה (DD/MM/YYYY) ללא שעה
                match_date = datetime.strptime(date_str, "%d/%m/%Y")
            except ValueError:
                try:
                    # 4. ניסיון פורמט שנה-חודש-יום ללא שעה (הפורמט הישן)
                    match_date = datetime.strptime(date_str, "%Y-%m-%d")
                except:
                    # print(f"Error: Failed to parse date for match {home_team} vs {away_team} with date string: '{date_str}'")
                    return None, [], [], []
    match = Match(date=match_date,home_team_id=home_team_id,away_team_id=away_team_id)
    match.score_home=home_score
    match.score_away=away_score
    match.competition = f"ליגת ווינר עונה {season_name} מחזור {fixture_num}"
    formation_list = []
    lineups_list = []
    subs_list = []
    events_list = []
    formation_list.append(TeamFormation(match=match,team_id=home_team_id,formation=game["home team"]["formation"]))
    formation_list.append(TeamFormation(match=match,team_id=away_team_id,formation=game["away team"]["formation"]))
    home_lu,away_lu = game["home team"]["lineup"],game["away team"]["lineup"]
    home_subs,away_subs=game["home team"]["subs"],game["away team"]["subs"]
    for playerh,playera in zip(home_lu,away_lu):
        home_player_id,away_player_id=get_player_id(playerh["name"],player_ids,changed),get_player_id(playera["name"],player_ids,changed)
        lineups_list.append(MatchLineup(match=match,player_id=home_player_id,team_id=home_team_id))
        lineups_list.append(MatchLineup(match=match,player_id=away_player_id,team_id=away_team_id))
        home_events = get_events(playerh)
        away_events = get_events(playera)
        for event in home_events:
            events_list.append(MatchEvent(match=match,player_id=home_player_id,team_id=home_team_id,event_type=event))
        for event in away_events:
            events_list.append(MatchEvent(match=match,player_id=away_player_id,team_id=away_team_id,event_type=event))
    for playerh in home_subs:
        home_player_id = get_player_id(playerh["name"],player_ids,changed)
        subs_list.append(MatchSubs(match=match,player_id=home_player_id,team_id=home_team_id))
        home_events = get_events(playerh)
        for event in home_events:
            events_list.append(MatchEvent(match=match,player_id=home_player_id,team_id=home_team_id,event_type=event))
    for playera in away_subs:
        away_player_id=get_player_id(playera["name"],player_ids,changed)
        subs_list.append(MatchSubs(match=match,player_id=away_player_id,team_id=away_team_id))
        away_events = get_events(playera)
        for event in away_events:
            events_list.append(MatchEvent(match=match,player_id=away_player_id,team_id=away_team_id,event_type=event))
    return match,formation_list, lineups_list,subs_list,events_list

all_formations = []
all_lineups = []
all_subs = []
all_events = []

with app.app_context():
    # Loop over all matches to prepare data
    count = 1
    db.session.rollback() 
    print("Database session rolled back to ensure a clean start.")
    for season_name, season in seasons.items():
        for fixture_num, fixture in season["games"].items():
            for game in fixture:
                if "error" in game:
                    continue
                print(f"fetching info for game number {count}")
                match_obj,formations, lineups, subs, events = get_game_data(
                    game, 
                    season_name, 
                    fixture_num, 
                    player_ids, 
                    team_ids, 
                    changed
                )
                
                if match_obj:
                    # Stage the match for initial commit to get its ID
                    db.session.add(match_obj)
                    
                    # Extend the master lists for batch insertion later
                    all_formations.extend(formations)
                    all_lineups.extend(lineups)
                    all_subs.extend(subs)
                    all_events.extend(events)
                count+=1

    try:
        # First commit: Save all Match objects to the database.
        # This is CRITICAL because the related objects (Lineup, Subs, Event) 
        # need a 'match_id' which is generated upon the Match object being committed.
        print(f"Staging {len(db.session.new)} Match objects...")
        db.session.commit()
        print("Successfully committed all Match objects.")
        
        # Second commit: Insert all child objects in batches.
        # SQLAlchemy is smart enough to use the new match.id for the relationships.
        
        # This step uses efficient batch insertion (add_all)

        print(f"Staging {len(all_formations)} formation objects...")
        db.session.add_all(all_formations)

        print(f"Staging {len(all_lineups)} Lineup objects...")
        db.session.add_all(all_lineups)
        
        print(f"Staging {len(all_subs)} Subs objects...")
        db.session.add_all(all_subs)
        
        print(f"Staging {len(all_events)} Event objects...")
        db.session.add_all(all_events)
        
        db.session.commit()
        
        print("\n--- Seeding Complete ---")
        print(f"Total Matches: {len(seasons['2022-2023']['games']['1']) * len(seasons['2022-2023']['games']) * len(seasons)}") # Rough estimate
        print(f"Total Lineups Inserted: {len(all_lineups)}")
        print(f"Total Substitutions Inserted: {len(all_subs)}")
        print(f"Total Events Inserted: {len(all_events)}")
        
    except IntegrityError as e:
        db.session.rollback()
        print("\n!!! ERROR !!! Database Integrity Error occurred.")
        print("This usually means a required foreign key (player or team ID) was missing or a unique constraint was violated.")
        print(e)
    except Exception as e:
        db.session.rollback()
        print(f"\n!!! FATAL ERROR !!! An unexpected error occurred: {e}")
        

                
                


