import os
import time
import random
import json
import re
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from bs4 import BeautifulSoup
from name_in_home_country import create_driver, safe_get,human_like_actions

# ------------------ Config ------------------
BASE_URL = "https://www.transfermarkt.com"
PROFILE_DIR = "tm_profile"        # reuse profile to keep cookies (helps)
HEADLESS = False                  # start with headful while debugging
RETRIES = 3
EXPECT_CSS = "span.info-table__content.info-table__content--bold"  # element that must exist on player/team page
MIN_SLEEP = 2.5
MAX_SLEEP = 6.0
RESTART_AFTER_ERRORS = 6          # restart webdriver after N consecutive failures
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/118.0",
]

def find_role(driver,players_dict:dict,player_name:str):
    url = players_dict[player_name]["profile_link"]
    soup = safe_get(url,driver)
    if not soup:
        return False
    pos_li = None
    for li in soup.find_all("li", class_="data-header__label"):
        # get only the li's own text (including label), ignore nested <span> content if needed
        label_text = li.get_text(" ", strip=True)
        # match "Position" (case-insensitive) — adjust if your site is localized
        if re.search(r"\bPosition\b", label_text, flags=re.I):
            pos_li = li
            break

    position = None
    if pos_li:
        span = pos_li.find("span", class_="data-header__content")
        if span:
            position = span.get_text(strip=True)

    players_dict[player_name]["role"] = position
    print(f"managed to find role:{position} for {player_name}")
    return True

def main():
    try:
        ua = random.choice(USER_AGENTS)
        driver = create_driver(user_agent=ua, profile_dir=PROFILE_DIR, headless=HEADLESS)

        with open("players_tm_info.json","r",encoding="utf-8") as f:
            players_dict=json.load(f)

        for player in players_dict.keys():
            if "role" in players_dict[player] and players_dict[player]["role"] != "":
                continue
            print(f"operating on {player}")
            success = find_role(driver,players_dict,player)
            time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
            if not success:
                consecutive_errors += 1
            else:
                consecutive_errors = 0

            # restart driver if too many consecutive failures (fresh fingerprint)
            if consecutive_errors >= RESTART_AFTER_ERRORS:
                print("[main] too many consecutive failures, restarting driver...")
                try:
                    driver.quit()
                except Exception:
                    pass
                time.sleep(random.uniform(3, 6))
                ua = random.choice(USER_AGENTS)
                driver = create_driver(user_agent=ua, profile_dir=PROFILE_DIR, headless=HEADLESS)
                consecutive_errors = 0
    
    except Exception as e:
        print(f"❌ Script crashed: {e}")
    
    except KeyboardInterrupt:
        print("gal stopped;saving data")
    finally:
        
        with open("players_tm_info.json","w",encoding="utf-8") as f:
            players_dict=json.dump(players_dict,f,ensure_ascii=False,indent=2)
        
        
if __name__ == "__main__":
    main()
