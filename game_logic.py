
import random
from flask import session
import datetime
from sqlalchemy import func
from models import TeamFormation, db, Match, MatchLineup, Player, Team,MatchEvent,DailyGame
import re


# Session Keys
GAME_SESSION_KEY = "current_game_lineup"
EXPOSED_PLAYERS_KEY = "exposed_players"
NUM_MATCHES = 3541

def get_or_create_daily_match():
    """
    Fetches the match and target team for today. If one hasn't been picked,
    it picks a new unused match/team combo and saves it for today.
    """
    today = datetime.date.today()
    
    # 1. Check if a game has already been picked for today
    daily_game_entry = db.session.query(DailyGame).filter_by(date=today).first()
    
    if daily_game_entry:
        # Yes! Return the match and the target team side
        return daily_game_entry.match, daily_game_entry.target_team_side
        
    # 2. No game picked for today. We need to pick one.
    else:
        target_match = None
        target_side = None

        # a) First, try to find a match where 'used_home' is false
        target_match = db.session.query(Match).filter_by(used_home=False).order_by(db.func.random()).first()
        if target_match:
            target_side = 'home'
            target_match.used_home = True
        else:
            # b) If no unused home teams, try to find one where 'used_away' is false
            target_match = db.session.query(Match).filter_by(used_away=False).order_by(db.func.random()).first()
            if target_match:
                target_side = 'away'
                target_match.used_away = True
        
        # c) --- HANDLE RESET ---
        # If target_match is STILL None, it means all home/away are used
        if not target_match:
            print("All matches used! Resetting 'used_home' and 'used_away' for all matches.")
            # Set all matches back to unused
            db.session.query(Match).update({
                Match.used_home: False,
                Match.used_away: False
            })
            db.session.commit() # Commit the reset
            
            # Now, try again to pick a 'home' team (which must exist now)
            target_match = db.session.query(Match).filter_by(used_home=False).order_by(db.func.random()).first()
            target_side = 'home'
            target_match.used_home = True

        # 3. If we STILL don't have a match, the database is empty.
        if not target_match:
            return None, None # Will be caught by the route

        # 4. We found a match! Now let's "lock it in."
        new_daily_game = DailyGame(
            date=today, 
            match=target_match, 
            target_team_side=target_side
        )
        db.session.add(new_daily_game)
        
        # 5. Commit all changes (the new DailyGame and the Match.used_... update)
        db.session.commit()
        
        # 6. Return the newly picked match and side
        return target_match, target_side

def _get_game_data(match_obj:Match,target_side:str):
    today_date_str = datetime.date.today().isoformat()
    
    if not match_obj:
        return {"error": "No matches found in the database. Please seed data."}
    
    # 2. Randomly select the target team (Home or Away)
    if target_side == 'home':
        target_team_id = match_obj.home_team_id
        target_team_name = match_obj.home_team.team_name
    else:
        target_team_id = match_obj.away_team_id
        target_team_name = match_obj.away_team.team_name
    
    target_team = match_obj.home_team if target_side=="home" else match_obj.away_team
    competition_title = match_obj.competition.split(':', 1)[0].strip()

    # 3. Get the starting lineup (MatchLineup joined to Player)
    formation_record = db.session.execute(
        db.select(TeamFormation).filter_by(match_id=match_obj.id, team_id=target_team_id)
    ).scalar_one_or_none()
    
    team_formation_str = formation_record.formation if formation_record else "N/A"
    lineup_query = db.session.execute(
        db.select(MatchLineup)
        .filter_by(match_id=match_obj.id, team_id=target_team_id)
        .join(Player)
        .limit(11) 
    ).scalars().all()

    # 4. Format the data for the session
    lineup_data = []
    for line in lineup_query:
        # We must ensure all related Player data is present (name, position, image)
        if line.player:
            player_events = db.session.execute(
                db.select(MatchEvent).filter_by(match_id=match_obj.id,player_id=line.player.id)).scalars().all()
            lineup_data.append({
                "id": line.player.id,
                "name": line.player.player_name,
                "position": line.player.position,
                "img_url": line.player.player_image_url,
                "player_stats":[event.event_type for event in player_events],
                "jersey_number":line.jersey_number,
                "game_pos": line.game_pos
                
            })
        
    if len(lineup_data) < 1:
        return {"error": f"No lineup data found for Match ID {match_obj.id}. Skipping match."}


    return {
        "today_date":today_date_str,
        "match_id": match_obj.id,
        "match_date": match_obj.date.isoformat(),
        "competition": competition_title,
        "home_team_name": match_obj.home_team.team_name,
        "away_team_name":match_obj.away_team.team_name,
        "home_team_img": match_obj.home_team.team_img_url,
        "away_team_img": match_obj.away_team.team_img_url,
        "score_home": match_obj.score_home,          
        "score_away": match_obj.score_away,
        "target_team_name":target_team_name,
        "shirt_colors": target_team.shirt_colors, # Use the new plural column
        "text_color": target_team.text_color,
        "lineup": lineup_data, # List of player dictionaries
        "lineup_count": len(lineup_data),
        "team_formation":team_formation_str
    }

def start_new_game():
    """Initializes a new game session with a random match lineup."""
    match_obj,target_side = get_or_create_daily_match()
    game_data = _get_game_data(match_obj,target_side)
    
    if "error" in game_data:
        return game_data
    
    # Save the match and lineup details to the session
    session[GAME_SESSION_KEY] = game_data
    
    # Initialize the exposed state: an array of False values matching the lineup size
    session[EXPOSED_PLAYERS_KEY] = [False] * game_data['lineup_count'] 
    
    return get_game_state()

def _normalize_name(name: str):
    """Normalizes names by converting to lowercase, stripping spaces, and removing apostrophes."""
    return name.strip().replace(' ', '').replace("'", "") # Add .replace("'", "")s

def _get_feedback(correct_name: str, guess: str):
    """
    Compares the normalized guess to the normalized correct name and generates Wordle-style feedback.
    Feedback: 2 (Correct position), 1 (Correct letter, wrong position), 0 (Incorrect).
    """
    
    # Normalize both the guess and the correct name (no spaces, lowercase)
    target = _normalize_name(correct_name)
    normalized_guess = _normalize_name(guess)
    
    feedback = [0] * len(normalized_guess)
    target_list = list(target)
    
    # Clip the guess length to the target name length for comparison
    max_len = min(len(normalized_guess), len(target))
    
    # 1. Check for GREEN (Correct letter and correct position)
    for i in range(max_len):
        if normalized_guess[i] == target[i]:
            feedback[i] = 2 # Green
            target_list[i] = None # Mark letter as used
            
    # 2. Check for YELLOW (Correct letter, wrong position)
    for i in range(max_len):
        if feedback[i] == 0: # Only check letters not yet marked as GREEN
            if normalized_guess[i] in target_list:
                feedback[i] = 1 # Yellow
                # Find and mark the letter as used in the target_list
                try:
                    target_index = target_list.index(normalized_guess[i])
                    target_list[target_index] = None
                except ValueError:
                    pass # Should not happen if logic is correct, but safe guard
                    
    # Pad the feedback if the guess was shorter than the target name
    if len(feedback) < len(target):
         feedback.extend([0] * (len(target) - len(feedback)))

    # Since the client needs feedback based on the guess length,
    # we return the feedback list capped at the input guess length.
    return feedback[:len(normalized_guess)]

def check_guess(slot_index: int, player_guess: str):
    """
    Checks the player's guess against a specific slot in the lineup (1-based index).
    Returns letter-by-letter feedback if the name is incorrect, or reveals the player if correct.
    """
    game_data = session.get(GAME_SESSION_KEY)
    exposed = session.get(EXPOSED_PLAYERS_KEY)
    
    lineup_index = slot_index - 1
    
    if not game_data or not exposed:
        return {"error": "No active game found. Please start a new game."}
    
    if exposed[lineup_index] is not False:
        return get_game_state(message="Slot already revealed.")
        
    if lineup_index < 0 or lineup_index >= len(game_data['lineup']):
        return {"error": "Invalid slot index provided."}

    target_player = game_data['lineup'][lineup_index]
    
    # === THE FIX: Compare the NORMALIZED names for a perfect match ===
    # This correctly compares "קאלהדרשלר" to "קאלהדרשלר"
    perfect_match = (_normalize_name(player_guess) == _normalize_name(target_player['name']))

    if perfect_match:
        # Player found and is correct - REVEAL
        exposed[lineup_index] = target_player['name']
        session[EXPOSED_PLAYERS_KEY] = exposed
        
        message = f"Correct! {target_player['name']} revealed."
        
        if all(exposed):
            message = "Congratulations! Lineup complete! 🎉"
        
        return get_game_state(message=message)
        
    else:
        # Not a perfect match: Return Wordle-style feedback
        feedback = _get_feedback(target_player['name'], player_guess)
        
        state = get_game_state(message="Incorrect name. See letter feedback.")
        state['feedback'] = {
            "slot_index": slot_index,
            "guess": player_guess,
            "feedback": feedback
        }
        return state
        
def get_game_state(message: str = None):
    """Returns the current game state and lineup presentation data."""
    game_data = session.get(GAME_SESSION_KEY)
    """
    print("---------debug info here----------")
    for key,value in game_data.items():
        print(key, " : ",value)
    """
    exposed = session.get(EXPOSED_PLAYERS_KEY)
    
    if not game_data or not exposed:
        return {"error": "No active game found."}
    
    # Prepare the lineup array for the client
    lineup_presentation = []
    is_finished = all(exposed)
    
    for i, player in enumerate(game_data['lineup']):
        is_revealed = bool(exposed[i])
        player_name = player['name']
        name_parts_list = re.split(r"([ '])", player_name)
        name_parts_filtered = [part for part in name_parts_list if len(part) > 0]

        # 2. Create the "secure" parts
        secure_name_parts = []
        for part in name_parts_filtered:
            if part == ' ' or part == "'":
                secure_name_parts.append(part)
            else:
                secure_name_parts.append("X" * len(part)) # Replaces "Lionel" with "XXXXXX"

        # 3. Get the guess_length
        apostrophe_indices = [idx for idx, char in enumerate(player_name) if char == "'"]

        
        lineup_presentation.append({
            "index": i + 1,
            "position": player['position'],
            "is_revealed": is_revealed,
            # If revealed, show the name, ID, and image. If not, mask the name length.
            "name_parts": secure_name_parts,
            "revealed_name": player['name'] if is_revealed else None,
            "player_img_url": player['img_url'] if is_revealed else None,
            "player_stats" : player['player_stats'],
            "guess_length": len(_normalize_name(player_name)),
            "apostrophe_indices": apostrophe_indices, # Used for the Wordle-style display (boxes)
            "player_id": player['id'] if is_revealed else None,
            "jersey_number":player["jersey_number"],
            "game_pos": player['game_pos']
        })
    
    state = {
        "is_finished": is_finished,
        "match_id": game_data['match_id'],
        "match_date": game_data['match_date'],
        "competition_title": game_data['competition'],
        "home_team_name": game_data['home_team_name'],
        "home_team_img_url": game_data['home_team_img'],
        "away_team_name": game_data['away_team_name'],
        "away_team_img_url": game_data['away_team_img'],
        "score_home": game_data['score_home'],
        "score_away": game_data['score_away'], 
        "target_team_name": game_data['target_team_name'],
        "team_formation": game_data['team_formation'],
        "shirt_colors":game_data['shirt_colors'],
        "text_color":game_data['text_color'],
        "lineup": lineup_presentation,
        "message": message or ("Game over!" if is_finished else "Ready to guess.")
    }
    
    return state