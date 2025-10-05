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


MAX_ID = 1060404
CURRENT = 211774
START = 211774

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

class Player():
    def __init__(self,name,number,) -> None:
        self.name = name
        self.number = number
        self.yellow = False
        self.red = False
        self.goals = 0
    def to_dict(self):
        return {
            "name": self.name,
            "number": self.number,
            "yellow": self.yellow,
            "red": self.red,
            "goals": self.goals,
        }
    def print_player(self):
        print(f"player name:{self.name}")
        print(f"player number:{self.number}")
        print(f"goals scored:{self.goals}")
        if self.yellow:
            print("concieved a yellow card")
        if self.red:
            print("concieved a red card")

class Team():
    def __init__(self,name,lineup,subs,img,score) -> None:
        self.name = name
        self.team_img = img
        self.lineup = lineup
        self.subs = subs
        self.score = score
    
    def print_team(self):
        print(f"team name:{self.name}")
        print("team starters:")
        for starter in self.lineup:
            starter.print_player()
        print("team subs:")
        for sub in self.subs:
            sub.print_player()
    
    def to_dict(self):
        return {
            "name": self.name,
            "team_img": self.team_img,
            "lineup": [p.to_dict() for p in self.lineup],
            "subs": [p.to_dict() for p in self.subs],
            "score": self.score,
        }
    
    


class Game():
    def __init__(self,id,date,fixture,home_team:Team,away_team:Team) -> None:
        self.home_team = home_team
        self.away_team = away_team
        self.date = date
        self.fixture = fixture
        self.score = str(away_team.score) + "-" + str(home_team.score)
    
    def to_dict(self):
        return {
            "fixture": self.fixture,
            "date": self.date,
            "home team": self.home_team.to_dict(),
            "away team": self.away_team.to_dict(),
        }
    

class Season():
    def __init__(self,season_id) -> None:
        self.id = season_id
        self.games = {}


    def insert_game(self,game:Game):
        if game.fixture in self.games:
            self.games[game.fixture].append(game)
        else:
            self.games[game.fixture] = [game]
    
    def to_dict(self):
        return {
            "season": self.id,
            "games": {
                fixture: [g.to_dict() for g in games]
                for fixture, games in self.games.items()
            },
        }


start_year_to_season = {
    2009: "09/10",
    2010: "10/11",
    2011: "11/12",
    2012: "12/13",
    2013: "13/14",
    2014: "14/15",
    2015: "15/16",
    2016: "16/17",
    2017: "17/18",
    2018: "18/19",
    2019: "19/20",
    2020: "20/21",
    2021: "21/22",
    2022: "22/23",
    2023: "23/24",
    2024: "24/25",
    2025: "25/26"
}

BAD_WORDS = set(["נוער","לנוער","נשים","לנשים","נערים","לנערים",
                 "לאומית","הלאומית","ילדים","לילדים","א","ב","ג"
                 ,"א'","ב'","ג'","אולמות","באולמות","ותיקים","לותיקים"])


seasons = {season_str: Season(season_str) for season_str in start_year_to_season.values()}
problem_ids = set()
domestic_cup_ids = set()
shoko_cup_ids = set()

def safe_get(url, driver,game_id=0):
    try:
        driver.get(url)
    except (WebDriverException, TimeoutException) as e:
        print(f"Error loading {url}: {e}")
        problem_ids.add(game_id)
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")

    if not soup.find("span",class_="info-table__content info-table__content--bold"):
        print(f"Main content not found (possible 403/404) for {url}")
        return None

    # check if page shows a 404/500 message
    """
    #if "404" in soup.text or "לא נמצא" in soup.text:  # adjust to site language
        print(f"Page returned 404/Not Found: {url}")
        return None

    if "403" in soup.text or "Access denied" in soup.text:
        print(f"403 detected  for {url}")
        return None
    """

    return soup

def date_to_season(date:string)-> Season:
    date_parts = date.split('/')
    month = int(date_parts[1])
    if month >= 7 :
        start_year = int(date_parts[2])
    else:
        start_year = int(date_parts[2])-1
    return seasons[start_year_to_season[start_year]]

def normalize_name(name: str) -> str:
    # split into words, sort alphabetically, join back
    return " ".join(sorted(name.split()))

def find_fixture(game_details):
    h1=(game_details.find("h1").get_text(strip=True))
    text = h1.replace("פרטי המשחק", "") # remove the extra span text
    text = text.strip()
    match = re.search(r"מחזור\s+(\d+)", text)
    fixture_number = int(match.group(1)) if match else None
    return fixture_number

def get_scorers(team_name : bs4.element.Tag ):
    goals_text = team_name.find("span",class_="goalers").get_text(" ",strip=True)
    goals_text = goals_text.replace("שערים:", "").strip()
    goals = [g.strip() for g in goals_text.split(",")]
    goal_counts = {}
    for g in goals:
        name = re.sub(r"\d+(\(.*?\))?", "", g).strip()
        name = normalize_name(name)
        if name:
            if name in goal_counts:
                goal_counts[name]+=1
            else:
                goal_counts[name] = 1
    return goal_counts


def find_team_details(team_tag : bs4.element.Tag,lineups_tag : bs4.element.Tag,subs_tag:bs4.element.Tag):
    team_name = team_tag.find("span").get_text() #works
    a_tag = team_tag.find("a")
    img_tag = a_tag.find("img")
    team_img=img_tag["src"] #works
    goal_scorers = get_scorers(team_tag) #works
    home_team_score = sum(goal_scorers.values())
    lineup = get_players(lineups_tag)
    subs = get_players(subs_tag)
    for starter in lineup:
        normalized = normalize_name(starter.name)
        if normalized in goal_scorers:
            starter.goals = goal_scorers[normalized]
    for sub in subs:
        normalized = normalize_name(sub.name)
        if normalized in goal_scorers:
            sub.goals = goal_scorers[normalized]
    return Team(team_name,lineup,subs, team_img,home_team_score)



def find_teams(game_details : bs4.element.Tag ):
    home_team_tag = game_details.find("div",class_="team-home")
    away_team_tag = game_details.find("div",class_="team-guest")
    home_starters_tag = game_details.find("div",class_="home Active clearfix")
    away_starters_tag = game_details.find("div",class_="guest Active clearfix")
    home_starters_tag = home_starters_tag.find_all("a",title="קבוצה - ביתית") 
    if not home_starters_tag:
        return None,None
    away_starters_tag = away_starters_tag.find_all("a",title="קבוצה אורחת")
    home_subs_tag =  game_details.find("div",class_="home Replacement")
    home_subs_tag = home_subs_tag.find_all("a",title="קבוצה - ביתית") if home_subs_tag else None
    away_subs_tag = game_details.find("div" , class_="guest Replacement")
    away_subs_tag = away_subs_tag.find_all("a",title="קבוצה אורחת") if away_subs_tag else None
    home_team =find_team_details(home_team_tag,home_starters_tag,home_subs_tag)
    away_team = find_team_details(away_team_tag,away_starters_tag,away_subs_tag)
    return home_team,away_team
    
def get_players(players_tag:bs4.element.Tag):
    players = []
    if not players_tag:
        return players

    for a_tag in players_tag:
        # The number is inside <span class="number">מס' XX</span>
        number_span = a_tag.find("span", class_="number")
        number = number_span.get_text(strip=True).replace("מס' ", "") if number_span else None

        # The name is inside <span class="name"><b>Player Name</b></span>
        name_span = a_tag.find("span", class_="name")
        name_b = name_span.find("b") if name_span else None
        name = name_b.get_text(strip=True) if name_b else None
        name = re.sub(r"\d+(\(.*?\))?", "",name).strip()

        if name and number:
            player = Player(name, number)
            yellow = a_tag.find("span",class_="yellow")
            red = a_tag.find("span",class_="red")
            if yellow:
                player.yellow=True
            if red:
                player.red=True
            
            players.append(player)
            
                

    # Example: print all players
    return players


def validate_league(game_details:bs4.element.Tag,game_id):
    h1 = game_details.find("h1")
# remove span
    for span in h1.find_all("span"):
        span.extract()

    title_text = h1.get_text(strip=True)
    words = title_text.split()
    if "גביע" in words and "המדינה" in words:
        print("domestic cup game")
        domestic_cup_ids.add(game_id)
        return False
    if "גביע" in words and "הטוטו" in words:
        print("shoko cup game")
        shoko_cup_ids.add(game_id)
        return False

    for word in words:
        if word in BAD_WORDS:
            return False
    return True 

def scrape_game_details(game_id):
    url = BASE_URL + f"?game_id={game_id}"
    soup = safe_get(url,driver,game_id)
    if not soup:
        return
    gid = "gfd_" + str(game_id)
    game_details = soup.find("section",id=gid)
    if not game_details:
        print("page exists, no data")
        return
    if not validate_league(game_details,game_id):
        print("Not major league")
        return 

    home_team,away_team = find_teams(game_details)
    if not home_team or not away_team:
        print("irrelevant game: no lineups")
        return
    gtime_div = game_details.find("div", id="gTimeHolder")
    date_text = gtime_div.find("span", class_="date").get_text(strip=True).split("|")[0] #works
    fixture_number = find_fixture(game_details)
    game = Game(game_id%MAX_ID,date_text,fixture_number,home_team,away_team)
    season = date_to_season(game.date)
    season.insert_game(game)
    print("game scraped succesfully")

    
    
    
    

def save_data():
    """Helper to save all collected data safely."""
    # Save seasons.json
    seasons_dict = {s: season.to_dict() for s, season in seasons.items()}

    try:
        with open("seasons.json", "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = {}

    existing_data.update(seasons_dict)

    with open("seasons.json", "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    print("✅ Seasons saved to seasons.json")

    # Save problem ids
    with open("problem_ids.txt", "w", encoding="utf-8") as f:
        for pid in problem_ids:
            f.write(str(pid) + "\n")

    """

    # Save domestic cup ids
    with open("domestic_ids.txt", "w", encoding="utf-8") as f:
        for pid in domestic_cup_ids:
            f.write(str(pid) + "\n")

    # Save shoko cup ids
    with open("shoko_ids.txt", "w", encoding="utf-8") as f:
        for pid in shoko_cup_ids:
            f.write(str(pid) + "\n")
    """


def main():
    game_ids = [int(line.strip()) for line in open("game_ids.txt", "r", encoding="utf-8") if line.strip()]
    try:
        for id in game_ids:
            print(f"operating on {id}")
            scrape_game_details(id)
    except Exception as e:
        print(f"❌ Script crashed: {e}")
    finally:
        # Always save progress, even if crash
        save_data()


if __name__ == "__main__":
    main()

