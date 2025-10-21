from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class Team(db.Model):
    __tablename__ = "teams"
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), nullable=True)
    team_img_url = db.Column(db.String(200),nullable=True)
    shirt_colors = db.Column(db.String(50), nullable=True)
    text_color = db.Column(db.String(7), nullable=True)

#relationships

    home_matches = db.relationship("Match", foreign_keys="[Match.home_team_id]", back_populates="home_team")
    away_matches = db.relationship("Match", foreign_keys="[Match.away_team_id]", back_populates="away_team")
    lineups = db.relationship("MatchLineup", back_populates="team", cascade="all, delete-orphan")
    subs = db.relationship("MatchSubs", back_populates="team", cascade="all, delete-orphan")
    events = db.relationship("MatchEvent", back_populates="team", cascade="all, delete-orphan")
    formations = db.relationship("TeamFormation", back_populates="team", cascade="all, delete-orphan")


class Player(db.Model):
    __tablename__ = "players"
    id = db.Column(db.Integer, primary_key=True)
    player_name =db.Column(db.String(100), nullable=False)
    player_image_url = db.Column(db.String(300), nullable=True)
    position = db.Column(db.String(100), nullable=True)
    eng_name = db.Column(db.String(100), nullable=True)

#relationships

    lineups = db.relationship("MatchLineup", back_populates="player", cascade="all, delete-orphan")
    subs = db.relationship("MatchSubs", back_populates="player", cascade="all, delete-orphan")
    events = db.relationship("MatchEvent", back_populates="player", cascade="all, delete-orphan")


    # If you want to allow duplicate names (e.g. 2 "David Cohen"s), 
    # don’t set unique=True here. Each will differ by team_id or id.

class Match(db.Model):
    __tablename__ = "matches"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    competition = db.Column(db.String(255), nullable=True)
    score_home = db.Column(db.Integer, default=0)
    score_away = db.Column(db.Integer, default=0)

    # Relationships
    home_team = db.relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = db.relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    lineups = db.relationship("MatchLineup", back_populates="match", cascade="all, delete-orphan")
    subs = db.relationship("MatchSubs", back_populates="match", cascade="all, delete-orphan")
    events = db.relationship("MatchEvent", back_populates="match", cascade="all, delete-orphan")
    formations = db.relationship("TeamFormation", back_populates="match", cascade="all, delete-orphan")

class MatchLineup(db.Model):
    __tablename__ = "match_lineups"
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    jersey_number =db.Column(db.String(50), nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    game_pos = db.Column(db.String(50), nullable=True)

    #relationships
    match = db.relationship("Match", back_populates="lineups")
    player = db.relationship("Player", back_populates="lineups")
    team = db.relationship("Team", back_populates="lineups")

class MatchSubs(db.Model):
    __tablename__ = "match_subs"
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    jersey_number =db.Column(db.String(50), nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)

    #relationships
    match = db.relationship("Match", back_populates="subs")
    player = db.relationship("Player", back_populates="subs")
    team = db.relationship("Team", back_populates="subs")
    

class MatchEvent(db.Model):
    __tablename__ = "match_events"
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # e.g. 'goal', 'yellow', 'red', 'sub_in', 'sub_out'
    
    match = db.relationship("Match", back_populates="events")
    player = db.relationship("Player", back_populates="events")
    team = db.relationship("Team", back_populates="events")

class TeamFormation(db.Model):
    __tablename__ = "team_formation"
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    formation = db.Column(db.String(50), nullable=False)

    match = db.relationship("Match", back_populates="formations")
    team = db.relationship("Team", back_populates="formations")
    