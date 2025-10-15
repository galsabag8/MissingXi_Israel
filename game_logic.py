
import random
from flask import session
from datetime import datetime, timezone
from sqlalchemy import func
from models import TeamFormation, db, Match, MatchLineup, Player, Team,MatchEvent # Note: Old riddle models removed!

# Session Keys
GAME_SESSION_KEY = "current_game_lineup"
EXPOSED_PLAYERS_KEY = "exposed_players"

def _utc_today():
    """Returns today's date (UTC)"""
    return datetime.now(timezone.utc).date()

def _get_game_data():
    """
    Fetches a random match, selects a random team, and retrieves the starting lineup.
    """
    # 1. Get a random Match object
    # Requires MatchLineup table to be seeded with data.
    match_obj = db.session.execute(db.select(Match).order_by(func.random())).scalars().first()
    
    if not match_obj:
        return {"error": "No matches found in the database. Please seed data."}
    
    # 2. Randomly select the target team (Home or Away)
    if random.choice([True, False]):
        target_team_id = match_obj.home_team_id
        target_team_name = match_obj.home_team.team_name
    else:
        target_team_id = match_obj.away_team_id
        target_team_name = match_obj.away_team.team_name

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
                "jersey_number":line.jersey_number
                
            })
        
    if len(lineup_data) < 1:
        return {"error": f"No lineup data found for Match ID {match_obj.id}. Skipping match."}


    return {
        "match_id": match_obj.id,
        "match_date": match_obj.date.isoformat(),
        "competition": match_obj.competition,
        "home_team_name": match_obj.home_team.team_name,
        "away_team_name":match_obj.away_team.team_name,
        "target_team_name":target_team_name,
        "lineup": lineup_data, # List of player dictionaries
        "lineup_count": len(lineup_data),
        "team_formation":team_formation_str
    }

def start_new_game():
    """Initializes a new game session with a random match lineup."""
    game_data = _get_game_data()
    
    if "error" in game_data:
        return game_data
    
    # Save the match and lineup details to the session
    session[GAME_SESSION_KEY] = game_data
    
    # Initialize the exposed state: an array of False values matching the lineup size
    session[EXPOSED_PLAYERS_KEY] = [False] * game_data['lineup_count'] 
    
    return get_game_state()

def _normalize_name(name: str):
    """Normalizes names by converting to lowercase and stripping spaces."""
    # We remove spaces to simplify letter comparison for Wordle-style feedback
    return name.strip().replace(' ', '')

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
        
        lineup_presentation.append({
            "index": i + 1,
            "position": player['position'],
            "is_revealed": is_revealed,
            # If revealed, show the name, ID, and image. If not, mask the name length.
            "name": player['name'],
            "revealed_name": player['name'] if is_revealed else None,
            "player_img_url": player['img_url'] if is_revealed else None,
            "name_length": len(player['name']), # Used for the Wordle-style display (boxes)
            "player_id": player['id'] if is_revealed else None,
            "jersey_number":player["jersey_number"]
        })
    
    state = {
        "is_finished": is_finished,
        "match_id": game_data['match_id'],
        "competition": game_data['competition'],
        "match_date": game_data['match_date'],
        "target_team_name": game_data['target_team_name'],
        "lineup": lineup_presentation,
        "message": message or ("Game over!" if is_finished else "Ready to guess.")
    }
    
    return state