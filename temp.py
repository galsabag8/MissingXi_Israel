from sqlalchemy import event
from models import db,Team,Match,Player,MatchLineup,MatchSubs,MatchEvent
from app import app

with app.app_context():
    # Find the team with ID 14
    
    players = Player.query.all()
    tbh_striker = Player.query.filter_by(player_name="טל בן חיים",position="Left Winger").first()
    tbh_defender = Player.query.filter_by(player_name="טל בן חיים",position="Centre-Back").first()
    count = 0
    all_lu = MatchLineup.query.filter_by(player_id=tbh_defender.id).all()
    all_subs = MatchSubs.query.filter_by(player_id=tbh_defender.id).all()
    print(len(all_lu),len(all_subs))
    
    


    
    