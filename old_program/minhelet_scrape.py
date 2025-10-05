import requests
from bs4 import BeautifulSoup
import json
import time
import random 


BASE_URL = "https://www.football.co.il/"  # מנהלת הליגות site
OUTPUT_FILE = "players.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_html(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/127.0.0.1 Safari/537.36"
    }
    for i in range(3):  # retry up to 3 times
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.text
        print(f"⚠️ Attempt {i+1}: status {resp.status_code}, retrying...")
        time.sleep(random.uniform(2, 5))
    resp.raise_for_status()


def get_teams(home_url):
    """Extract all teams and their links from homepage."""
    soup = BeautifulSoup(get_html(home_url), "html.parser")
    teams = []
    for a in soup.select("a[href^='/']"):
        href = a.get("href")
        if href and href.count("-") >= 1:
            full_url = "https://www.football.co.il" + href
            teams.append((a.get("title") or a.get_text(strip=True), full_url))

    #print(teams, len(teams))
    return teams
"""
def get_squad_url(team_url):
    
    soup = BeautifulSoup(get_html(team_url), "html.parser")
    squad_link = soup.find("a", string="סגל")
    if squad_link:
        href = squad_link["href"]
        if not href.startswith("http"):
            href = BASE_URL + href
        return href
    return None
"""
def scrape_team(team_url: str, team_name: str) -> list[dict]:
    players = []
    print(team_url)
    resp = requests.get(team_url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    members = soup.select(".sc_team_member_inner")
    for m in members:
        img_tag = m.find("img")
        name = img_tag["alt"].strip() if img_tag and "alt" in img_tag.attrs else None
        img_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else None

        name_tag = m.select_one(".sc_team_member_name a")
        profile_url = BASE_URL + name_tag["href"] if name_tag else None

        players.append({
            "name_heb": name,
            "profile_url": profile_url,
            "image_url": img_url
        })

    return players


def main():
    home_url = BASE_URL  # homepage
    teams = get_teams(home_url)
    
    data = []

    for team_name, team_url in teams:
        print(team_url)
        print(f"Scraping {team_name} ...")
        """
        squad_url = get_squad_url(team_url)
        if not squad_url:
            print("  No squad page found")
            continue
        """

        players = scrape_team(team_url, team_name)
        print(len(players))
        data.append({"team": team_name, "players": players})
        time.sleep(1)  # be polite

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
if __name__ == "__main__":
    main()
