import json
import requests
from bs4 import BeautifulSoup
import time
import re
from itertools import zip_longest

from sqlalchemy.sql.operators import truediv


WIKI_BASE = "https://he.wikipedia.org/wiki/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

def safe_get(url, timeout=10):
    try:
        response = requests.get(url,headers=headers, timeout=timeout)
        response.raise_for_status()  # raises HTTPError for 4xx/5xx
        return response.text
    except (requests.RequestException, requests.Timeout) as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch_player_stats(player_name):
    """Fetch appearances and goals per club from Hebrew Wikipedia."""
    url = WIKI_BASE + player_name.replace(" ", "_")
    res_text = safe_get(url)
    if not res_text:
        return None
    soup = BeautifulSoup(res_text, "html.parser")

    stats = []

    # Find all soccer infobox tables
    tables = soup.find_all("table", class_="infobox-soccer-nowrap")
    
    
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            
            if len(cols) == 3:
                    years_list = [x.get_text(" ", strip=True) for x in cols[0].contents if x.name != "br"]
                    clubs_list = []
                    stats_list = [x.get_text(" ", strip=True) for x in cols[2].contents if x.name != "br"]
                    for a in cols[1].find_all("a", title=True):
                        clubs_list.append(a["title"].strip())
                    #print(clubs_list)


                # Align lengths (zip safely)

                    for y, c, s in zip_longest(years_list, clubs_list, stats_list, fillvalue=""):
                    # Clean club text
                        c = c.replace("←", "").strip()
                        if not c:
                            continue

                        # Extract apps/goals
                        apps, goals = None, None
                        match = re.match(r"(\d+)\s*\((\d+)\)", s)
                        if match:
                            apps, goals = int(match.group(1)), int(match.group(2))

                        stats.append({
                            "years": y.strip(),
                            "club": c,
                            "apps": apps,
                            "goals": goals
                        })

# Filter out rows that are just headers like "שנים"
    stats = [s for s in stats if s["years"] != "שנים"]

    return stats



def main():
    # Load players.json
    with open("players.json", "r", encoding="utf-8") as f:
        players = json.load(f)

    results = {}
    #i = 0
    for player in players:
        #if i == 5:
            #break
        name = player["player_name"]
        print(f"מחפש {name}...")
        stats = fetch_player_stats(name)
        if stats:
            results[name] = stats
        else:
            results[name] = "לא נמצאו נתונים"
        time.sleep(1)
        #i+=1
          # להיות נחמדים לוויקיפדיה

    # Save results
    with open("player_stats.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
