from models import DailyRiddle, db, Player, Category, PlayerAnswer, PlayerSeasonStats
from sqlalchemy import desc
from datetime import datetime
from app import app 


year_dict = {
    8: "06/07", 9: "07/08", 10: "08/09", 11: "09/10", 12: "10/11",
    13: "11/12", 14: "12/13", 15: "13/14", 16: "14/15", 17: "15/16",
    18: "16/17", 19: "17/18", 20: "18/19", 21: "19/20", 22: "20/21",
    23: "21/22", 24: "22/23", 25: "23/24", 26: "24/25"
}

def reset_top_scorers():
    # 1. Delete old data
    db.session.query(DailyRiddle).delete()
    db.session.query(PlayerAnswer).delete()
    db.session.query(Category).delete()
    db.session.commit()
    print("🗑️ Deleted all old categories and answers.")

    # 2. Loop through seasons and insert fresh categories + answers
    season_ids = db.session.query(PlayerSeasonStats.season_id).distinct().all()
    season_ids = [s[0] for s in season_ids]

    for season_id in season_ids:
        season_name = year_dict.get(season_id, f"Season {season_id}")
        category_title = f"הכובשים המובילים בעונת {season_name}"

        category = Category(category_title=category_title)
        db.session.add(category)
        db.session.commit()  # commit to get category.id

        top_players = (
            db.session.query(PlayerSeasonStats)
            .filter(PlayerSeasonStats.season_id == season_id)
            .order_by(desc(PlayerSeasonStats.goals))
            .limit(10)
            .all()
        )

        for rank, stat in enumerate(top_players, start=1):
            pa = PlayerAnswer(
                category_id=category.id,
                player_id=stat.player_id,
                rank=rank
            )
            db.session.add(pa)

        db.session.commit()
        print(f"✅ Added category {category_title}")


if __name__ == "__main__":
    with app.app_context():
        reset_top_scorers()
