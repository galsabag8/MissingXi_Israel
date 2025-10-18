import json
from app import app
from models import db, Team

def populate():
    with app.app_context():
        with open('team_colors.json', 'r', encoding='utf-8') as f:
            team_colors_data = json.load(f)
            
        print("Starting to update team colors...")
        updated_count = 0
        
        for team_name, colors_list in team_colors_data.items():
            team = Team.query.filter_by(team_name=team_name).first()
            
            if team:
                # === THE KEY CHANGE IS HERE ===
                # Convert the list of colors into a single comma-separated string
                # e.g., ["#FFFF00", "#0000FF"] becomes "#FFFF00,#0000FF"
                team.shirt_colors = ",".join(colors_list)
                
                # We'll set a default text color for now
                team.text_color = "#FFFFFF" 
                
                updated_count += 1
                print(f"  -> Updated colors for {team_name} to {team.shirt_colors}")
            else:
                print(f"  -> WARNING: Team '{team_name}' not found in the database.")
        
        db.session.commit()
        print(f"\n✅ Successfully updated colors for {updated_count} teams.")

if __name__ == "__main__":
    populate()