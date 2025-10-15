from models import db, MatchLineup, MatchSubs
import json
from app import app
from sqlalchemy import case, update, tuple_

# === FIX 1: Reduce the batch size to a safer number ===
CHUNK_SIZE = 500

with app.app_context():
    # --- Load your JSON data as before ---
    with open("seasons.json", "r", encoding="utf-8") as f:
        seasons = json.load(f)
    with open("match_ids.json", "r", encoding="utf-8") as f:
        match_ids = json.load(f)
    with open("player_ids.json", "r", encoding="utf-8") as f:
        player_ids = json.load(f)
    with open("changed_names.json", "r", encoding="utf-8") as f:
        changed = json.load(f)

    # --- Step 1: Prepare lists of all required updates in memory ---
    lineup_updates = []
    subs_updates = []
    problems = []
    count = 1

    print("Preparing update data from JSON files...")
    # This part of your logic for gathering data is correct and remains the same.
    for season_name, season in seasons.items():
        for fixture_num, fixture in season["games"].items():
            for game in fixture:
                count += 1
                if "error" in game and game["error"]:
                    continue
                home_team, away_team = game["home team"]["name"], game["away team"]["name"]
                competition = f"ליגת ווינר עונה {season_name} מחזור {fixture_num}: {home_team}-{away_team}"
                match_id = match_ids.get(competition)

                if not match_id or len(game["home team"]["lineup"]) != 11 or len(game["away team"]["lineup"]) != 11:
                    problems.append(count)
                    continue
                
                for team_key in ["home team", "away team"]:
                    for player_dict in game[team_key]["lineup"]:
                        player_id = player_ids.get(player_dict["name"]) or player_ids.get(changed.get(player_dict["name"]))
                        if player_id:
                            lineup_updates.append({"match_id": match_id, "player_id": player_id, "jersey_number": player_dict["number"]})
                    for player_dict in game[team_key]["subs"]:
                        player_id = player_ids.get(player_dict["name"]) or player_ids.get(changed.get(player_dict["name"]))
                        if player_id:
                            subs_updates.append({"match_id": match_id, "player_id": player_id, "jersey_number": player_dict["number"]})

    # --- Step 2: Execute the updates in smaller, committed batches. ---
    
    if lineup_updates:
        print(f"Executing bulk UPDATE for {len(lineup_updates)} lineup records...")
        for i in range(0, len(lineup_updates), CHUNK_SIZE):
            chunk = lineup_updates[i:i + CHUNK_SIZE]
            print(f"  Processing lineup chunk {i // CHUNK_SIZE + 1}...")
            
            case_statement = case(
                {(item['match_id'], item['player_id']): item['jersey_number'] for item in chunk},
                value=tuple_(MatchLineup.match_id, MatchLineup.player_id)
            )
            stmt = update(MatchLineup).where(
                tuple_(MatchLineup.match_id, MatchLineup.player_id).in_(
                    [(item['match_id'], item['player_id']) for item in chunk]
                )
            ).values(jersey_number=case_statement)
            
            db.session.execute(stmt)
            # === FIX 2: Commit after each successful chunk ===
            db.session.commit() 
        print("Done with lineup updates.")

    if subs_updates:
        print(f"Executing bulk UPDATE for {len(subs_updates)} substitute records...")
        for i in range(0, len(subs_updates), CHUNK_SIZE):
            chunk = subs_updates[i:i + CHUNK_SIZE]
            print(f"  Processing subs chunk {i // CHUNK_SIZE + 1}...")
            
            case_statement = case(
                {(item['match_id'], item['player_id']): item['jersey_number'] for item in chunk},
                value=tuple_(MatchSubs.match_id, MatchSubs.player_id)
            )
            stmt = update(MatchSubs).where(
                tuple_(MatchSubs.match_id, MatchSubs.player_id).in_(
                    [(item['match_id'], item['player_id']) for item in chunk]
                )
            ).values(jersey_number=case_statement)
            
            db.session.execute(stmt)
            # === FIX 2: Commit after each successful chunk ===
            db.session.commit()
        print("Done with subs updates.")

    print("Script finished successfully! ✅")
    print("\nGames with problems:")
    print(problems)