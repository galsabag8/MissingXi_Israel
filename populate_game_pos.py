# populate_game_pos_and_formations.py

import json
from app import app
# === Import TeamFormation ===
from models import db, MatchLineup, TeamFormation
from sqlalchemy import case, update, tuple_

# Define a batch size for updates
CHUNK_SIZE = 500
TBH_DEF = ["4","26"]

with app.app_context():
    # --- Load necessary JSON files ---
    print("Loading JSON data...")
    with open("seasons.json", "r", encoding="utf-8") as f:
        seasons = json.load(f)
    with open("match_ids.json", "r", encoding="utf-8") as f:
        match_ids = json.load(f)
    with open("player_ids.json", "r", encoding="utf-8") as f:
        player_ids = json.load(f)
    with open("changed_names.json", "r", encoding="utf-8") as f:
        changed = json.load(f)
    # === Add team_ids.json for formation updates ===
    with open("team_ids.json", "r", encoding="utf-8") as f:
        teams_ids = json.load(f)
    print("JSON data loaded.")

    # --- Prepare update data in memory ---
    lineup_updates = []
    # === Create list for formation updates ===
    formation_updates = []
    problems = []
    processed_count = 0

    print("Processing games and preparing updates...")
    for season_name, season in seasons.items():
        for fixture_num, fixture in season["games"].items():
            for game in fixture:
                processed_count += 1
                if processed_count % 100 == 0:
                    print(f"  Processed {processed_count} games...")
                if ("error" in game)  or "check" in game:
                    continue

                home_team, away_team = game["home team"]["name"], game["away team"]["name"]
                competition = f"ליגת ווינר עונה {season_name} מחזור {fixture_num}: {home_team}-{away_team}"
                match_id = match_ids.get(competition)

                if not match_id:
                    problems.append(f"Missing match_id for: {competition}")
                    continue

                home_team_id = teams_ids.get(home_team)
                away_team_id = teams_ids.get(away_team)

                # Process lineup for both teams
                for team_key, team_id in [("home team", home_team_id), ("away team", away_team_id)]:
                    if not team_id: # Check if team ID was found
                        problems.append(f"Missing team_id for: {game[team_key]['name']} in match {match_id}")
                        continue

                    team_data = game[team_key]

                    # --- Prepare lineup updates (game_pos) ---
                    if "lineup" in team_data:
                        for player_dict in team_data["lineup"]:
                            player_name = player_dict.get("name")
                            game_pos = player_dict.get("game_pos")
                            if not player_name or not game_pos: continue

                            player_id = player_ids.get(player_name) or player_ids.get(changed.get(player_name))
                            if player_name == "טל בן חיים":
                                player_id = 1 if player_dict["number"] in TBH_DEF else 193
                            if player_id:
                                lineup_updates.append({
                                    "match_id": match_id,
                                    "player_id": player_id,
                                    "game_pos": game_pos
                                })
                            else:
                                problems.append(f"Missing player_id for: {player_name} in match {match_id}")

                    # --- Prepare formation updates ---
                    formation_str = team_data.get("formation")
                    if formation_str:
                        formation_updates.append({
                            "match_id": match_id,
                            "team_id": team_id,
                            "formation": formation_str
                        })
                    else:
                        problems.append(f"Missing formation for team {team_id} in match {match_id}")


    print(f"Finished processing. Prepared {len(lineup_updates)} lineup updates and {len(formation_updates)} formation updates.")
    if problems:
        print("\nEncountered some problems:")
        # Limit printed problems for brevity
        for problem in problems[:min(len(problems), 10)]:
            print(f"  - {problem}")
        if len(problems) > 10:
            print(f"  ... and {len(problems) - 10} more.")

    # --- Execute lineup updates in efficient batches ---
    if lineup_updates:
        print(f"\nExecuting bulk UPDATE for {len(lineup_updates)} MatchLineup records in batches of {CHUNK_SIZE}...")
        for i in range(0, len(lineup_updates), CHUNK_SIZE):
            chunk = lineup_updates[i:i + CHUNK_SIZE]
            print(f"  Processing lineup chunk {i // CHUNK_SIZE + 1}...")

            case_statement = case(
                {(item['match_id'], item['player_id']): item['game_pos'] for item in chunk},
                value=tuple_(MatchLineup.match_id, MatchLineup.player_id)
            )
            stmt = update(MatchLineup).where(
                tuple_(MatchLineup.match_id, MatchLineup.player_id).in_(
                    [(item['match_id'], item['player_id']) for item in chunk]
                )
            ).values(game_pos=case_statement)

            db.session.execute(stmt)
            db.session.commit()
        print("✅ Done updating game_pos in MatchLineup.")
    else:
        print("\nNo MatchLineup updates were needed.")

    # --- Execute formation updates in efficient batches ---
    if formation_updates:
        print(f"\nExecuting bulk UPDATE for {len(formation_updates)} TeamFormation records in batches of {CHUNK_SIZE}...")
        for i in range(0, len(formation_updates), CHUNK_SIZE):
            chunk = formation_updates[i:i + CHUNK_SIZE]
            print(f"  Processing formation chunk {i // CHUNK_SIZE + 1}...")

            # Build CASE statement for formation updates
            # NOTE: TeamFormation likely has a composite primary key (match_id, team_id) or a single 'id' key.
            # We assume a composite key (match_id, team_id) here based on typical structure.
            # If your primary key is just 'id', this needs modification.
            case_statement = case(
                {
                    (item['match_id'], item['team_id']): item['formation']
                    for item in chunk
                },
                value=tuple_(TeamFormation.match_id, TeamFormation.team_id)
            )

            # Build UPDATE statement for formation
            stmt = update(TeamFormation).where(
                tuple_(TeamFormation.match_id, TeamFormation.team_id).in_(
                    [(item['match_id'], item['team_id']) for item in chunk]
                )
            ).values(formation=case_statement)

            db.session.execute(stmt)
            db.session.commit()
        print("✅ Done updating formation in TeamFormation.")
    else:
        print("\nNo TeamFormation updates were needed.")

    print("\nScript finished successfully!")
