from pydoc import plain
import requests
import html
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

chrome_options = Options()
#chrome_options.add_argument("--headless")  # Uncomment to run headless
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)

BASE = "https://www.football.org.il/Components.asmx/League_AllTables"

LEAGUE_ID = 40
SEASON_IDS = list(range(11, 28))  # 09/10 up to 25/26
all_game_ids = set()



for season in SEASON_IDS:
    # You’ll need to know how many boxes and rounds exist.
    # For now let’s just try 0..3 boxes and 1..40 rounds as an upper bound.
      
    for rnd in range(1, 38):
        if season!=12 and rnd == 37:
            continue
        url = BASE + f"?league_id=40&season_id={season}&box=0&round_id={rnd}"
        driver.get(url)
        time.sleep(1)  
        soup = BeautifulSoup(driver.page_source, "lxml-xml")  # parse as XML
        html_data_tag = soup.find("HtmlData")  # get the <HtmlData> element
        html_content = html_data_tag.get_text()  # get its content
        html_content = html.unescape(html_content)  # convert &lt; &gt; &amp; to real < > &
        html_soup = BeautifulSoup(html_content, "html.parser")
        with open("debug_response.html", "w", encoding="utf-8") as f:
            f.write(str(html_soup))
        if not html_soup:
            print("fuck")
        
        links = html_soup.find_all("a", class_="table_row link_url")
        for a in links:
            href = a.get("href")
            if href and "game_id=" in href:
                gid = href.split("game_id=")[-1]
                print(gid)
                all_game_ids.add(gid)
        

with open("game_ids.txt", "w", encoding="utf-8") as f:
    for gid in sorted(all_game_ids):
        f.write(gid + "\n")

print(f"Total collected: {len(all_game_ids)} game ids")
