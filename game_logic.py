
# game_logic.py
from flask import session
from datetime import datetime, timezone
from models import db, Category, PlayerAnswer, TeamAnswer, DailyRiddle

_daily_riddle = None


def _utc_today():
    return datetime.now(timezone.utc).date()


def _session_key(prefix):
    return f"{prefix}:{_utc_today().isoformat()}"

def load_daily_riddle():
    """
    Get or create today's daily riddle (UTC), persisted in DB.
    Ensures all users share the same daily riddle.
    """
    global _daily_riddle
    today = _utc_today()

    if _daily_riddle and _daily_riddle.get("riddle_date") == today.isoformat():
        return _daily_riddle

    daily = DailyRiddle.query.filter_by(riddle_date=today).first()
    if not daily:
        category = Category.query.order_by(db.func.random()).first()
        if not category:
            return {"error": "No categories left in DB."}
        daily = DailyRiddle(riddle_date=today, category_id=category.id)
        db.session.add(daily)
        db.session.commit()

    category = daily.category

    # Prefer whichever answer set exists; if both, prefer the one with 10 entries
    player_answers = PlayerAnswer.query.filter_by(category_id=category.id).all()
    team_answers = TeamAnswer.query.filter_by(category_id=category.id).all()

    answers_dict = {}
    images_dict = {}
    chosen = None
    if len(team_answers) >= len(player_answers):
        chosen = team_answers if team_answers else player_answers
        for ans in chosen:
            if hasattr(ans, "team") and ans.team is not None:
                answers_dict[ans.rank] = ans.team.team_name
                images_dict[ans.rank] = getattr(ans.team, "team_image_url", None)
            else:
                answers_dict[ans.rank] = ans.player.player_name
                images_dict[ans.rank] = getattr(ans.player, "player_image_url", None)
    else:
        chosen = player_answers
        for ans in chosen:
            answers_dict[ans.rank] = ans.player.player_name
            images_dict[ans.rank] = getattr(ans.player, "player_image_url", None)
    print(images_dict)

    _daily_riddle = {
        "riddle_date": today.isoformat(),
        "category": category.category_title,
        "answers": answers_dict,
        "images": images_dict
    }
    return _daily_riddle

def check_guess(player_guess):
    """
    Check if the player's guess is correct and update their session state.
    """
    riddle = load_daily_riddle()
    if "error" in riddle:
        return riddle

    finished_key = _session_key("finished")
    exposed_key = _session_key("exposed")

    if session.get(finished_key):
        current_exposed = session.get(exposed_key, [""] * len(riddle["answers"]))
        images = [riddle["images"].get(i+1) for i in range(len(riddle["answers"]))]
        return {
            "correct": False,
            "rank": None,
            "finished": True,
            "riddle_date": riddle["riddle_date"],
            "exposed": current_exposed,
            "images": images,
            "message": "Game already finished! 🎉"
        }

    answers = riddle["answers"]
    normalized_guess = player_guess.strip().lower()

    for rank, answer in answers.items():
        # Match against English or Hebrew forms if present
        answer_low = answer.lower()
        if normalized_guess == answer_low:
            exposed = session.get(exposed_key, [""] * len(answers))
            if exposed[rank - 1]:
                return {
                    "correct": False,
                    "rank": rank,
                    "finished": False,
                    "riddle_date": riddle["riddle_date"],
                    "exposed": exposed,
                    "images": [riddle["images"].get(i+1) for i in range(len(answers))],
                    "message": "This answer was already revealed."
                }

            exposed[rank - 1] = normalized_guess
            session[exposed_key] = exposed

            if sum(1 for x in exposed if x) == len(answers):
                session[finished_key] = True
                return {
                    "correct": True,
                    "rank": rank,
                    "finished": True,
                    "riddle_date": riddle["riddle_date"],
                    "exposed": exposed,
                    "images": [riddle["images"].get(i+1) for i in range(len(answers))],
                    "message": "Congratulations! You revealed all answers! 🎉"
                }

            return {
                "correct": True,
                "rank": rank,
                "finished": False,
                "riddle_date": riddle["riddle_date"],
                "exposed": exposed,
                "images": [riddle["images"].get(i+1) for i in range(len(answers))],
                "message": "Correct guess!"
            }

    current_exposed = session.get(exposed_key, [""] * len(answers))
    return {
        "correct": False,
        "rank": None,
        "finished": False,
        "riddle_date": riddle["riddle_date"],
        "exposed": current_exposed,
        "images": [riddle["images"].get(i+1) for i in range(len(answers))],
        "message": "Wrong guess, try again!"
    }

def get_game_state():
    """
    Get the current game state for the logged-in user.
    """
    riddle = load_daily_riddle()
    if "error" in riddle:
        return riddle

    exposed_key = _session_key("exposed")
    exposed = session.get(exposed_key, [""] * len(riddle["answers"]))
    images = [riddle["images"].get(i+1) for i in range(len(riddle["answers"]))]
    return {
        "riddle_date": riddle["riddle_date"],
        "category": riddle["category"],
        "exposed": exposed,
        "images": images
    }
