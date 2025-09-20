import os
import sys
import json
import argparse
import urllib.parse
import urllib.request
import re
import gzip
from bs4 import BeautifulSoup
from datetime import datetime

# Optional DB update imports are done lazily only if --update-db is passed

TRANSFERMARKT_ISRAEL_URL = "https://www.transfermarkt.com/laliga-israel/startseite/wettbewerb/ISR1"
TRANSFERMARKT_BASE_URL = "https://www.transfermarkt.com"


def http_get_html(url: str) -> str:
    """Download HTML content with proper headers and gzip decompression."""
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
    req.add_header('Accept-Language', 'en-US,en;q=0.5')
    req.add_header('Accept-Encoding', 'gzip, deflate')
    req.add_header('Connection', 'keep-alive')
    req.add_header('Upgrade-Insecure-Requests', '1')
    
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
        # Check if content is gzipped
        if resp.info().get('Content-Encoding') == 'gzip':
            data = gzip.decompress(data)
        return data.decode('utf-8')


def download_file(url: str, dest_path: str) -> None:
    """Download file with validation."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
        # Validate it's actually an image
        if data.startswith(b'\xff\xd8\xff') or data.startswith(b'\x89PNG') or data.startswith(b'RIFF'):
            with open(dest_path, "wb") as out:
                out.write(data)
        else:
            raise Exception("Downloaded file is not a valid image format")


def sanitize_filename(name: str) -> str:
    """Create safe filename."""
    name = name.replace("/", "-").replace("\\", "-").strip()
    name = name.replace(" ", "_")
    # Remove special characters that might cause issues
    name = re.sub(r'[^\w\-_.]', '', name)
    return name


def get_player_profile_info(profile_url: str) -> tuple[str, str]:
    """
    Scrape player profile page to get image URL and 'Name in home country'.
    Returns (image_url, name_home_country).
    """
    html = http_get_html(profile_url)
    soup = BeautifulSoup(html, "html.parser")

    # Default values
    image_url = None
    name_home_country = None

    # Get player image
    img_tag = soup.find("img", class_="data-header__profile-image")
    if img_tag:
        image_url = img_tag.get("src")

    # Find "Name in home country"
    fact_rows = soup.find_all("tr")
    for row in fact_rows:
        header = row.find("th")
        if header and "Name in home country" in header.get_text():
            value = row.find("td")
            if value:
                name_home_country = value.get_text(strip=True)
            break

    return image_url, name_home_country


def scrape_team_players(team_url: str, team_name: str) -> list[dict]:
    """Scrape all players from a team's squad page."""
    players = []
    
    try:
        print(f"  Scraping team: {team_name}")
        html = http_get_html(team_url)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the squad table
        squad_table = soup.find('table', class_='items')
        if not squad_table:
            print(f"    No squad table found for {team_name}")
            return players
        
        # Get all player rows
        rows = squad_table.find_all('tr', class_=re.compile(r'.*odd.*|.*even.*'))
        
        for row in rows:
            try:
                # Get player name and profile link
                name_cell = row.find('td', class_='hauptlink')
                if not name_cell:
                    continue
                    
                name_link = name_cell.find('a')
                if not name_link:
                    continue
                
                player_name = name_link.get_text().strip()
                player_url = name_link.get('href')
                
                if not player_url.startswith('http'):
                    player_url = TRANSFERMARKT_BASE_URL + player_url
                
                # Get position
                position_cell = row.find('td', class_='zentriert')
                position = position_cell.get_text().strip() if position_cell else "Unknown"
                
                # Get player image
                print(f"    Getting image for {player_name}")
                image_url, name_home_country = get_player_profile_info(player_url)
                
                players.append({
                    'name_eng': player_name,
                    'position': position,
                    'team': team_name,
                    'profile_url': player_url,
                    'image_url': image_url,
                    'name_home_country': name_home_country
                })
                
                print(f"    Added: {player_name} ({position})")
                
            except Exception as e:
                print(f"    Error processing player row: {e}")
                continue
                
    except Exception as e:
        print(f"  Error scraping team {team_name}: {e}")
    
    return players


def scrape_israeli_league_players() -> list[dict]:
    """Scrape all players from Israeli Premier League teams."""
    all_players = []
    
    try:
        print("Scraping Israeli Premier League teams...")
        html = http_get_html(TRANSFERMARKT_ISRAEL_URL)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the teams table
        teams_table = soup.find('table', class_='items')
        if not teams_table:
            print("No teams table found")
            return all_players
        
        # Get all team rows
        team_rows = teams_table.find_all('tr', class_=re.compile(r'.*odd.*|.*even.*'))
        
        for row in team_rows:
            try:
                # Get team name and squad link
                team_cell = row.find('td', class_='hauptlink')
                if not team_cell:
                    continue
                    
                team_link = team_cell.find('a')
                if not team_link:
                    continue
                
                team_name = team_link.get_text().strip()
                squad_url = team_link.get('href')
                
                if not squad_url.startswith('http'):
                    squad_url = TRANSFERMARKT_BASE_URL + squad_url
                
                # Replace 'startseite' with 'kader' to get squad page
                squad_url = squad_url.replace('/startseite/', '/kader/')
                
                # Scrape players from this team
                team_players = scrape_team_players(squad_url, team_name)
                all_players.extend(team_players)
                
            except Exception as e:
                print(f"Error processing team row: {e}")
                continue
                
    except Exception as e:
        print(f"Error scraping Israeli league: {e}")
    
    return all_players


def insert_players_to_db(app_module_path: str, players: list[dict], download_images: bool = False) -> None:
    """Insert players into database."""
    sys.path.insert(0, os.path.dirname(app_module_path))
    from app import app
    from models import db, Player, Team, PlayerAnswer, Category
    
    with app.app_context():
        # Create or get the current season category
        
        # Create teams
        teams = {}
        for player_data in players:
            team_name = player_data['team']
            if team_name not in teams:
                team = Team.query.filter_by(team_name=team_name).first()
                if not team:
                    team = Team(team_name=team_name)
                    db.session.add(team)
                    db.session.commit()
                teams[team_name] = team
        
        # Insert players
        inserted_count = 0
        for i, player_data in enumerate(players, 1):
            try:
                # Check if player already exists
                existing_player = Player.query.filter_by(player_name_eng=player_data['name_eng']).first()
                if existing_player:
                    print(f"  Player {player_data['name_eng']} already exists, skipping")
                    continue
                
                # Create player
                player = Player(
                    player_name_eng=player_data['name_eng'],
                    position=player_data['position']
                )
                db.session.add(player)
                db.session.commit()
                
                # Download image if requested
                if download_images and player_data['image_url']:
                    try:
                        fname = sanitize_filename(player_data['name_eng']) + ".jpg"
                        dest_path = os.path.join("static", "players", fname)
                        download_file(player_data['image_url'], dest_path)
                        player.player_image_url = f"/static/players/{fname}"
                        db.session.commit()
                        print(f"  Downloaded image for {player_data['name_eng']}")
                    except Exception as e:
                        print(f"  Failed to download image for {player_data['name_eng']}: {e}")
                
                inserted_count += 1
                print(f"  Inserted player {i}/{len(players)}: {player_data['name_eng']}")
                
            except Exception as e:
                print(f"  Error inserting player {player_data['name_eng']}: {e}")
                continue
        
        print(f"\nSuccessfully inserted {inserted_count} players into database")


def main():
    parser = argparse.ArgumentParser(description="Scrape Israeli Premier League players from Transfermarkt.")
    parser.add_argument("--project-root", default=os.path.dirname(__file__), help="Project root (where static/ lives)")
    parser.add_argument("--download-images", action="store_true", help="Download player images to static/players")
    parser.add_argument("--output-file", help="Save player data to JSON file")
    args = parser.parse_args()

    # Scrape players
    players = scrape_israeli_league_players()
    
    if not players:
        print("No players found!")
        return
    
    print(f"\nFound {len(players)} players")
    
    # Save to JSON if requested
    if args.output_file:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(players, f, indent=2, ensure_ascii=False)
        print(f"Saved player data to {args.output_file}")
    
    # Insert to database
    insert_players_to_db(os.path.join(args.project_root, "app.py"), players, args.download_images)


if __name__ == "__main__":
    main()
