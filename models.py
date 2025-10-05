from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Team(db.Model):
    __tablename__ = "teams"
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), nullable=True)
    team_img_url = db.Column(db.String(200),nullable=True)
    # unique=True → no duplicate team names


class Player(db.Model):
    __tablename__ = "players"
    id = db.Column(db.Integer, primary_key=True)
    player_name =db.Column(db.String(100), nullable=False)
    player_image_url = db.Column(db.String(300), nullable=True)
    position = db.Column(db.String(100), nullable=True)
    english_name = db.Column(db.String(100), nullable=True)

    # If you want to allow duplicate names (e.g. 2 "David Cohen"s), 
    # don’t set unique=True here. Each will differ by team_id or id.


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    category_title = db.Column(db.String(200), nullable=False)


class TeamAnswer(db.Model):
    __tablename__ = "team_answers"
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    __table_args__ = (
        db.UniqueConstraint("category_id", "rank", name="uq_team_answer_category_rank"),
    )

    category = db.relationship("Category", backref="team_answers")
    team = db.relationship("Team", backref="answers")


class PlayerAnswer(db.Model):
    __tablename__ = "player_answers"
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    __table_args__ = (
        db.UniqueConstraint("category_id", "rank", name="uq_player_answer_category_rank"),
    )

    category = db.relationship("Category", backref="player_answers")
    player = db.relationship("Player", backref="answers")

class PlayerSeasonStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    season_id = db.Column(db.Integer, nullable=False)
    goals = db.Column(db.Integer, default=0)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)

    __table_args__ = (db.UniqueConstraint("player_id", "season_id", name="_player_season_uc"),)

class DailyRiddle(db.Model):
    __tablename__ = "daily_riddles"
    id = db.Column(db.Integer, primary_key=True)
    riddle_date = db.Column(db.Date, nullable=False, unique=True, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    category = db.relationship("Category")
