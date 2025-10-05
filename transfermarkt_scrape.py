from pydoc import plain
import string
from sys import exception
import time
from turtle import position
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
from missing_players.missing_players_url import players_dict



BASE_URL = "https://www.transfermarkt.com/"
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
failed = {}


# Add a list of common User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/118.0",
]



def fetch_staff_profiles(team_name:str,season_id:str,team_uniq,players_dict:dict,seasons_per_team:dict):
    save = team_name
    team_name = team_name.replace(" ","-")
    url = BASE_URL+ f"{team_name}/kader/verein/{team_uniq}/plus/0/galerie/0?saison_id={season_id}"
    soup = safe_get(url,driver)

    if not soup:
        return
    
    seasons_per_team[save].remove(season_id)

    player_blocks = soup.select("table.inline-table")
    print(len(player_blocks))
    
    for block in player_blocks:
        a_tag = block.select_one("td.hauptlink a")
        if a_tag:
            player_name = a_tag.get_text(strip=True)
            if player_name in players_dict:
                continue
            profile_link = a_tag["href"]   # relative link
            full_profile_link = "https://www.transfermarkt.com" + profile_link
        role_tag = block.select_one("tr:nth-of-type(2) td")
        role = role_tag.get_text(strip=True) if role_tag else None
        #print(f"player name:{player_name},position:{position},profile_link:{full_profile_link}")
        players_dict[player_name] = {
            "role": role,
            "profile_link": full_profile_link
        }



def main():
    
    try:

        with open("uniq_num.json","r",encoding="utf-8") as f:
            numbers = json.load(f)
        with open("he_en_team_names.json","r",encoding="utf-8") as f:
            names = json.load(f)
        with open("failed_seasons.json","r",encoding="utf-8") as f:
            seasons_per_team = json.load(f)
        with open("players_tm_info.json","r",encoding="utf-8") as f:
            players_dict=json.load(f)
        
        for team_he, team_en in names.items():
            if len(seasons_per_team[team_en]) == 0:
                continue
            for season in seasons_per_team[team_en]:
                print(f"working on team:{team_en} in season:{season}")
                fetch_staff_profiles(team_en,str(season),numbers[team_en],players_dict,seasons_per_team)
                time.sleep(1)
        """

        for season in seasons_per_team["Hapoel Kfar Saba"]:
            print(f"working on team:Hapoel Kfar Saba in season:{season}")
            fetch_staff_profiles("Hapoel Kfar Saba",str(season),numbers["Hapoel Kfar Saba"],players_dict,seasons_per_team)
            time.sleep(1)
        """

    except Exception as e:
        print(f"❌ Script crashed: {e}")
    
    except KeyboardInterrupt:
        print("gal stopped;saving data")
    finally:

        with open("players_tm_info.json","w",encoding="utf-8") as f:
            json.dump(players_dict,f,ensure_ascii=False,indent=2)

        with open("failed_seasons.json","w",encoding="utf-8") as f:
            json.dump(seasons_per_team,f,ensure_ascii=False,indent=2)
        print("data saved succesfully")
    


    

if __name__=="__main__":
    main()

