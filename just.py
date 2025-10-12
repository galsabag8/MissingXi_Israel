from models import db, Player
from sqlalchemy import func
from app import app


with app.app_context():
    duplicate_names_query = db.session.execute(
    db.select(
        Player.player_name, 
        func.count(Player.id).label('name_count') # Count the rows (players) for each name
    )
    .group_by(Player.player_name) # Group all rows with the same name together
    .having(func.count(Player.id) > 1) # Filter for groups (names) that appear more than once
    .order_by(func.count(Player.id).desc()) # Optional: Order by most duplicates first
    ).all()

# 2. Process and print the results
    if duplicate_names_query:
        print("Found duplicate player names:")
        print("----------------------------")
        for name, count in duplicate_names_query:
            print(f"Name: {name} (Count: {count})")
    else:
        print("No duplicate player names found.")

    