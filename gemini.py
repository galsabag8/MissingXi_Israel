from models import db, Player, Team, Match, MatchEvent, MatchLineup, MatchSubs
from app import app
import json
from datetime import datetime
from sqlalchemy.exc import IntegrityError

# Load data files
# NOTE: Using 'changed' and 'player_ids' for player mapping, 
# and 'team_ids' for team mapping.
with open("seasons.json","r",encoding="utf-8") as f:
    seasons = json.load(f)
with open("changed_names.json","r",encoding="utf-8") as f:
    changed = json.load(f)
with open("player_ids.json","r",encoding="utf-8") as f:
    player_ids = json.load(f)
with open("team_ids.json","r",encoding="utf-8") as f:
    team_ids = json.load(f)


def get_player_id(player_name, changed_map, id_map):
    """
    Retrieves the player ID, handling name changes and missing IDs.
    Returns the player ID or None if the player is not found.
    """
    # 1. Check for name changes
    name_to_check = changed_map.get(player_name, player_name)
    
    # 2. Get the ID
    player_id = id_map.get(name_to_check)
    
    if player_id is None:
        # Log or handle players without an ID if necessary
        print(f"Warning: Player ID not found for: {player_name} (checking: {name_to_check})")
    
    return player_id


def process_match_data(game_data, season_name, fixture_num, team_id_map, player_id_map, changed_map):
    """
    Creates Match object and collects Lineups, Subs, and Events for batch insertion.
    Returns (Match object, list of MatchLineup objects, list of MatchSubs objects, list of MatchEvent objects)
    """
    # --- 1. Create the Match object (Base Data) ---
    
    home_team_name = game_data["home team"]["name"]
    away_team_name = game_data["away team"]["name"]
    
    home_id = team_id_map.get(home_team_name)
    away_id = team_id_map.get(away_team_name)

    if home_id is None or away_id is None:
        print(f"Skipping match due to missing team ID: {home_team_name} vs {away_team_name}")
        return None, [], [], []

    # Assuming game_data["date"] is a string that needs conversion
    # Ensure date format matches 'YYYY-MM-DD HH:MM:SS' or adjust strptime accordingly
    try:
        match_date = datetime.strptime(game_data["date"], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        # Attempt to parse date in case of different format
        print(f"Warning: Could not parse date string: {game_data['date']}. Trying date-only format.")
        try:
            match_date = datetime.strptime(game_data["date"], "%Y-%m-%d")
        except:
             print(f"Error: Failed to parse date for match {home_team_name} vs {away_team_name}")
             return None, [], [], []
    
    
    match = Match(
        date=match_date,
        home_team_id=home_id,
        away_team_id=away_id,
        score_home=game_data["home team"]["score"],
        score_away=game_data["away team"]["score"],
        competition=f"ליגת ווינר עונה {season_name} מחזור {fixture_num}",
    )
    
    # Lists for batch insertion
    lineups_list = []
    subs_list = []
    events_list = []

    # Map team names to IDs for easier lookup inside the loop
    team_map = {home_team_name: home_id, away_team_name: away_id}
    
    # --- 2. Process Lineups, Subs, and Events ---
    
    for team_data_key in ["home team", "away team"]:
        team_data = game_data[team_data_key]
        current_team_id = team_map[team_data["name"]]

        # a. Lineups
        for player_name in team_data.get("lineup", []):
            p_id = get_player_id(player_name, changed_map, player_id_map)
            if p_id:
                lineups_list.append(
                    MatchLineup(
                        match=match, # Use the match object directly for relationship binding
                        player_id=p_id,
                        team_id=current_team_id
                    )
                )

        # b. Substitutions
        for sub_data in team_data.get("subs", []):
            # Assuming 'sub_data' is the player name who was substituted (out)
            # The structure of sub data is not fully known, assuming it contains the player name (IN or OUT)
            # Adjust the following logic based on your actual data structure
            
            # Example assumption: sub_data is the name of the player who came IN
            p_id = get_player_id(sub_data, changed_map, player_id_map) 
            if p_id:
                 subs_list.append(
                    MatchSubs(
                        match=match,
                        player_id=p_id,
                        team_id=current_team_id
                    )
                )

        # c. Events (Goals, Cards, etc.)
        for event_data in team_data.get("events", []):
            # Assuming event_data is a dictionary with 'player' and 'type' keys
            player_name = event_data.get("player")
            event_type = event_data.get("type")
            
            p_id = None
            if player_name:
                p_id = get_player_id(player_name, changed_map, player_id_map)
                
            if event_type:
                # Event creation succeeds even if player_id is None (e.g., team events like penalty)
                events_list.append(
                    MatchEvent(
                        match=match,
                        player_id=p_id, # Can be None
                        team_id=current_team_id,
                        event_type=event_type
                    )
                )

    return match, lineups_list, subs_list, events_list


# --- Main Execution Block ---

# Lists to store objects for final batch insertion
all_lineups = []
all_subs = []
all_events = []

with app.app_context():
    # Loop over all matches to prepare data
    for season_name, season in seasons.items():
        for fixture_num, fixture in season["games"].items():
            for game in fixture:
                match_obj, lineups, subs, events = process_match_data(
                    game, 
                    season_name, 
                    fixture_num, 
                    team_ids, 
                    player_ids, 
                    changed
                )
                
                if match_obj:
                    # Stage the match for initial commit to get its ID
                    db.session.add(match_obj)
                    
                    # Extend the master lists for batch insertion later
                    all_lineups.extend(lineups)
                    all_subs.extend(subs)
                    all_events.extend(events)

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
        
