from pydoc import plain
import string
import bs4
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.common.exceptions import WebDriverException, TimeoutException
import json
import re
from game_scrape import safe_get



BASE_URL = "https://www.football.org.il/leagues/games/game/"
#PLAYER_BASE_URL = "https://www.football.org.il"


# Setup Selenium Chrome driver in headless mode (optional)
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Uncomment to run headless
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)
players_dict = {}



def scrape_info(game_id:int,players_missing:dict,count:int):
    url = BASE_URL + f"?game_id={game_id}"
    soup = safe_get(url,driver,game_id)
    if not soup:
        return
    gid = "gfd_" + str(game_id)
    game_details = soup.find("section",id=gid)
    if not game_details:
        print("page exists, no data")
        return
    block = game_details.find("div",class_="players-cont")
    players = block.find_all("a")
    for i,a_tag in enumerate(players):
        name_span = a_tag.find("span", class_="name")
        if i > 39:
            print("hi1")
        name_b = name_span.find("b") if name_span else None
        name = name_b.get_text(strip=True) if name_b else None
        name = re.sub(r"\d+(\(.*?\))?", "",name).strip() if name else None
        if name and name in players_missing:
            if name in players_dict:
                continue
            players_dict[name]=a_tag["href"]
            count+=1
    
        

 


def main():
    with open("missing_players.txt", "r", encoding="utf-8") as f:
        players_missing = {line.strip() for line in f if line.strip()}

    game_ids = [int(line.strip()) for line in open("game_ids.txt", "r", encoding="utf-8") if line.strip()]
    count = 0
    try:
        for id in game_ids:
            print(f"operating on {id}")
            scrape_info(id,players_missing,count)
    except Exception as e:
        print(f"❌ Script crashed: {e}")
    finally:
        with open("missing_players_info.json", "w", encoding="utf-8") as f:
            json.dump(players_dict, f, ensure_ascii=False, indent=2)
            print("✅ players saved to missing_players_info.json")
            print(f"{count} player out of 1127 were completed")
    
if __name__ == "__main__" :
    main()