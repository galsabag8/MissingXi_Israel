import os
import time
import random
import json
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from bs4 import BeautifulSoup

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
# --------------------------------------------

def create_driver(user_agent=None, profile_dir=None, headless=HEADLESS):
    opts = Options()
    if headless:
        # newer headless flag to be closer to full browser
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    if profile_dir:
        # using a persistent profile helps preserve accepted cookies
        opts.add_argument(f"--user-data-dir={os.path.abspath(profile_dir)}")
    if user_agent:
        opts.add_argument(f"--user-agent={user_agent}")
    # reduce noisy logs
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=opts)

    # small stealth tweaks
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
            """
        })
    except Exception:
        pass

    return driver

def human_like_actions(driver):
    """Small scrolling to let JS run and look human."""
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/6);")
        time.sleep(random.uniform(0.15, 0.6))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(0.2, 0.8))
    except Exception:
        pass

def safe_get(url, driver, expect_css=EXPECT_CSS, retries=RETRIES, timeout=12, record_failed=None):
    """
    Load URL using Selenium and return BeautifulSoup or None.
    Ensures the expected element exists before returning.
    """
    attempt = 0
    backoff = 1.5
    while attempt < retries:
        attempt += 1
        try:
            driver.get(url)
        except (WebDriverException, TimeoutException) as e:
            print(f"[safe_get] driver.get error (attempt {attempt}): {e}")
            if record_failed is not None:
                record_failed.add(url)
            time.sleep(random.uniform(2, 4) * backoff)
            backoff *= 2
            continue

        # Wait for the expected element to appear
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, expect_css))
            )
            human_like_actions(driver)
            # small settle time
            time.sleep(random.uniform(0.4, 1.1))
        except TimeoutException:
            # page doesn't show the expected element within timeout
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            page_text = soup.get_text(" ", strip=True)[:1000].lower()
            # detect likely real blocks/captchas
            if any(k in page_text for k in ("access denied", "you have been blocked", "captcha", "403 forbidden")):
                print(f"[safe_get] Access blocked or captcha detected for {url}")
                if record_failed is not None:
                    record_failed.add(url)
                time.sleep(random.uniform(5, 10) * backoff)
                backoff *= 2
                continue
            # otherwise, retry lightly (maybe JS delayed)
            print(f"[safe_get] expected selector not found (attempt {attempt}) for {url}; retrying...")
            time.sleep(random.uniform(1.5, 3.5))
            continue

        # final check: parse and verify element exists in parsed HTML
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        if not soup.select_one(expect_css):
            print(f"[safe_get] After wait, parsed HTML still missing expected selector for {url}")
            if record_failed is not None:
                record_failed.add(url)
            time.sleep(random.uniform(1.0, 3.0))
            continue

        return soup

    # all attempts failed
    print(f"[safe_get] Failed to get page after {retries} attempts: {url}")
    return None

# ----------------- Scraping logic using your pattern -----------------
def fetch_heb_name(driver,players_dict:dict,player_name:str,):
    url = players_dict[player_name]["profile_link"]
    soup = safe_get(url,driver)
    if not soup:
        return False
    heb_name = soup.find("span",class_="info-table__content info-table__content--bold").get_text()
    if len(heb_name) > 0:
        players_dict[player_name]["name_in_home_country"] = heb_name
    return True

def main():
    try:
        ua = random.choice(USER_AGENTS)
        driver = create_driver(user_agent=ua, profile_dir=PROFILE_DIR, headless=HEADLESS)

        with open("players_tm_info.json","r",encoding="utf-8") as f:
            players_dict=json.load(f)

        for player in players_dict.keys():
            if "name_in_home_country" in players_dict[player]:
                continue
            print(f"operating on {player}")
            success = fetch_heb_name(driver, players_dict,player)
                    # sleep to be polite
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