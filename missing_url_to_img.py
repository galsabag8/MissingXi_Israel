import json

from sqlalchemy.sql.coercions import expect
from models import db, Player
from app import app
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from game_scrape import safe_get

BASE_URL = "https://www.football.org.il"

chrome_options = Options()
#chrome_options.add_argument("--headless")  # Uncomment to run headless
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)

with open("missing_players_url.json","r",encoding="utf-8") as f:
    missing = json.load(f)


try:

    for name,url in missing.items():
        print(name)
        URL = BASE_URL + url
        soup = safe_get(URL,driver)
        if not soup:
            print(f"failed to get img for {name}")
            continue
        fig = soup.find("figure")
        if not fig:
            missing[name] = None
            continue
        img_src = fig.find("img")
        if not img_src:
            missing[name] = None
            continue
        missing[name] = img_src["src"]
except Exception as e:
        print(f"❌ Script crashed: {e}")
finally:

        with open("missing_players_img.json","w",encoding="utf-8") as f:
            missing = json.dump(missing,f,ensure_ascii=False,indent=2)





