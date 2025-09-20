from app import app
from models import db, Category, Player, PlayerAnswer

with app.app_context():  # Needed to access Flask app context
    # --- Step 1: Create a sample category (Hebrew) ---
    cat = Category(category_title="10 הכובשים המובילים בליגת העל")
    db.session.add(cat)
    db.session.commit()  # Commit to get cat.id

    # --- Step 2: Fetch existing players with IDs 1–10 ---
    players = Player.query.filter(Player.id.in_(range(1, 11))).order_by(Player.id).all()

    # Safety check: make sure we found exactly 10 players
    if len(players) < 10:
        raise ValueError(f"Expected 10 players with IDs 1–10, found only {len(players)}")

    # --- Step 3: Insert PlayerAnswer rows with ranks 1–10 ---
    for rank, player in enumerate(players, start=1):
        pa = PlayerAnswer(category_id=cat.id, player_id=player.id, rank=rank)
        db.session.add(pa)

    db.session.commit()
    print("Database setup complete! Category linked to players with IDs 1–10.")
