from app import  app
from models import TeamFormation
with app.app_context():
    team_formations = TeamFormation.query.all()
    formations = {form.formation for form in team_formations}
    print(formations)
    