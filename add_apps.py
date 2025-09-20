import requests
from bs4 import BeautifulSoup
import psycopg2
import json

HEADERS = {
    "User-Agent": "Kaduregel11Bot/1.0 (https://yourwebsite.com)",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
}

def get_connection():
    return psycopg2.connect(
        dbname="Top10Game",
        user="postgres",
        password="Sabigo11!!",
        host="localhost",
        port=5432
    )

def get_player_infobox(player_name):
    url = f"https://he.wikipedia.org/wiki/{player_name.replace(' ', '_')}"
    print(player_name.replace(' ', '_'))
    r = requests.get(url,headers=HEADERS)
    if r.status_code != 200:
        print(f"❌ Could not fetch {url}")
        return None
    return r.text

def parse_appearances(html):
    soup = BeautifulSoup(html, "html.parser")
    infobox = soup.find("table", {"class": "infobox-soccer-nowrap"})
    if not infobox:
        return []

    # Get all rows
    rows = infobox.find_all("tr")
    appearances = []

    years_col = None
    teams_col = None
    apps_col = None

    # Find the correct <td> for years and teams
    for row in rows:
        tds = row.find_all("td")
        if not tds:
            continue

        # Look for appearances header
        if any("הופעות" in td.get_text() for td in tds):
            apps_col = tds[0]  # maybe the next td contains numbers
            continue

        # Assume first two columns in main row are years/teams
        if len(tds) >= 2:
            years_col = tds[0]
            teams_col = tds[1]

    if not years_col or not teams_col:
        return []

    years_list = [y.strip() for y in years_col.decode_contents().split("<br") if y.strip()]
    teams_list = [BeautifulSoup(t, "html.parser").get_text(strip=True) for t in teams_col.decode_contents().split("<br") if t.strip()]

    # Zip years and teams
    for i in range(min(len(years_list), len(teams_list))):
        appearances.append({
            "team": teams_list[i],
            "apps": None,   # you can try to parse if stats exist
            "goals": None
        })

    return appearances


def update_db(player_id, appearances):
    conn = get_connection()
    cur = conn.cursor()

    for rec in appearances:
        team_name = rec["team"]
        apps = rec["apps"]
        # Insert team if not exists
        cur.execute("""
            INSERT INTO teams (team_name)
            VALUES (%s)
            ON CONFLICT (team_name) DO NOTHING
            RETURNING id
        """, (team_name,))
        team_id = cur.fetchone()[0] if cur.rowcount > 0 else None

        if team_id is None:
            # If already exists, fetch it
            cur.execute("SELECT id FROM teams WHERE team_name=%s", (team_name,))
            team_id = cur.fetchone()[0]

        # Insert or update appearances
        cur.execute("""
            INSERT INTO player_appearances (player_id, team_id, amount)
            VALUES (%s, %s, %s)
            ON CONFLICT (player_id, team_id)
            DO UPDATE SET amount = EXCLUDED.amount
        """, (player_id, team_id, apps))

    conn.commit()
    cur.close()
    conn.close()

def main():
    with open("players.json", "r", encoding="utf-8") as f:
        players = json.load(f)

    for player in players:
        player_id = player["id"]
        player_name = player["player_name"]

        print(f"🔍 Scraping {player_name}")
        html = get_player_infobox(player_name)
        if not html:
            continue

        appearances = parse_appearances(html)
        if appearances:
            update_db(player_id, appearances)
            print(f"✅ Updated {player_name}: {len(appearances)} records")
        else:
            print(f"⚠️ No appearances found for {player_name}")

if __name__ == "__main__":
    main()
