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

BASE_URL = "https://www.football.org.il/leagues/league/details/"
PLAYER_BASE_URL = "https://www.football.org.il"
SEASONS = range(23, 27)

# Setup Selenium Chrome driver in headless mode (optional)
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Uncomment to run headless
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)

def scrape_player_image(player_link):
    """Fetch the player's image URL using a temporary Chrome session."""
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    #chrome_options.add_argument("--headless")  # optional

    temp_driver = webdriver.Chrome(options=chrome_options)
    try:
        temp_driver.get(player_link)
        WebDriverWait(temp_driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".new-player-card_img-container img"))
        )
        soup = BeautifulSoup(temp_driver.page_source, "html.parser")
        img_tag = soup.select_one(".new-player-card_img-container img")
        if img_tag and img_tag.get("src"):
            return img_tag["src"]
    except Exception as e:
        print(f"  Could not get image for {player_link}: {e}")
        return None
    finally:
        temp_driver.quit()

with app.app_context():

    for season in SEASONS:
        print(f"Scraping season {season}...")
        driver.get(f"{BASE_URL}?league_id=40&season_id={season}&page_type=player-goals")
        time.sleep(random.uniform(2, 5))  # random delay to mimic human behavior

        # Wait until table rows are loaded
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.table_row.link_url")))
        except:
            print(f"  No players found or page blocked for season {season}")
            continue

        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("a.table_row.link_url")

        for row in rows:
            cols = row.find_all("div", class_="table_col")
            if len(cols) >= 3:
                # Fix "שם שחקן" issue
                for span in cols[1].select("span.sr-only"):
                    span.extract()

                player_name = cols[1].get_text(strip=True)
                team_name = cols[0].get_text(strip=True)
                goals_text = cols[2].get_text(strip=True).replace('\xa0', '')
                match = re.search(r'\d+', goals_text)
                goals = int(match.group()) if match else 0
                if team_name.startswith("שם הקבוצה"):
                    team_name = team_name.replace("שם הקבוצה", "", 1).strip()

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

                stats = PlayerSeasonStats.query.filter_by(player_id=player.id, season_id=season).first()
                if not stats:
                    stats = PlayerSeasonStats(
                        player_id=player.id,
                        season_id=season,
                        team_id=team.id,
                        goals=goals
                    )
                    db.session.add(stats)
        

        db.session.commit()
        print(f"  Season {season} scraped and saved.")

driver.quit()
print("Done.")
