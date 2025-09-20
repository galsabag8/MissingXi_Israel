from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from models import db, Player, Team, PlayerSeasonStats
from app import app
import time
import random
import re
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://www.football.org.il/leagues/league/details/"
PLAYER_BASE_URL = "https://www.football.org.il"
SEASONS = range(8, 9)  # Adjust the range as needed

# Setup Selenium Chrome driver
chrome_options = Options()
chrome_options.add_argument("--headless=new")  # headless mode
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--log-level=3")
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)

def scrape_player_image(player_link):
    """Fetch the player's image URL using the main driver."""
    try:
        driver.get(player_link)
        # Wait for image to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".new-player-card_img-container img"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        img_tag = soup.select_one(".new-player-card_img-container img")
        if img_tag and img_tag.get("src"):
            return img_tag["src"]
    except Exception as e:
        print(f"  Could not get image for {player_link}: {e}")
    return None

def process_player(row, season):
    """Process a single player row: get or create player/team, add stats."""
    cols = row.find_all("div", class_="table_col")
    if len(cols) < 3:
        return

    # Remove "sr-only" spans in player name
    for span in cols[1].select("span.sr-only"):
        span.extract()

    player_name = cols[1].get_text(strip=True)
    team_name = cols[0].get_text(strip=True)
    goals_text = cols[2].get_text(strip=True).replace('\xa0', '')
    match = re.search(r'\d+', goals_text)
    goals = int(match.group()) if match else 0

    with app.app_context():
        # Get or create Player
        player = Player.query.filter_by(player_name=player_name).first()
        if not player:
            player_link = PLAYER_BASE_URL + row['href']
            player_image_url = scrape_player_image(player_link)
            player = Player(player_name=player_name, player_image_url=player_image_url)
            db.session.add(player)
            db.session.flush()

        # Get or create Team
        team = Team.query.filter_by(team_name=team_name).first()
        if not team:
            team = Team(team_name=team_name)
            db.session.add(team)
            db.session.flush()

        # Add stats if not exists
        stats = PlayerSeasonStats.query.filter_by(player_id=player.id, season_id=season).first()
        if not stats:
            stats = PlayerSeasonStats(
                player_id=player.id,
                season_id=season,
                team_id=team.id,
                goals=goals
            )
            db.session.add(stats)

def scrape_season(season):
    """Scrape a single season's player-goals page."""
    print(f"Scraping season {season}...")
    try:
        driver.get(f"{BASE_URL}?league_id=40&season_id={season}")
        time.sleep(random.uniform(2, 4))  # mimic human delay
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.table_row.link_url")))
    except:
        print(f"  No players found or page blocked for season {season}")
        return

    soup = BeautifulSoup(driver.page_source, "html.parser")
    rows = soup.select("a.table_row.link_url")

    # Process players in threads for faster image fetching
    with ThreadPoolExecutor(max_workers=5) as executor:
        for row in rows:
            executor.submit(process_player, row, season)

    # Commit after processing all players in the season
    with app.app_context():
        db.session.commit()
    print(f"  Season {season} scraped and saved.")

with app.app_context():
    db.drop_all()
    db.create_all()
    for season in SEASONS:
        scrape_season(season)

driver.quit()
print("Done.")
