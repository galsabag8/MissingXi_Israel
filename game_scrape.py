from pydoc import plain
import bs4
from flask import request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from models import db, Player, Team, PlayerSeasonStats
from app import app
import time
import random
import re

BASE_URL = "https://www.football.org.il/leagues/games/game/"
#PLAYER_BASE_URL = "https://www.football.org.il"
SEASONS = range(23, 27)

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
            print(f"player name:{starter.name},"f"player number:{starter.number}",f"player scored {starter.goals} goals")
        print("team subs:")
        for sub in self.subs:
            print(f"player name:{sub.name},"f"player number:{sub.number}",f"player scored {sub.goals} goals")


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
    away_starters_tag = away_starters_tag.find_all("a",title="קבוצה אורחת")
    home_subs_tag =  game_details.find("div",class_="home Replacement")
    home_subs_tag = home_subs_tag.find_all("a",title="קבוצה - ביתית")
    away_subs_tag = game_details.find("div" , class_="guest Replacement")
    away_subs_tag = away_subs_tag.find_all("a",title="קבוצה אורחת")
    home_team =find_team_details(home_team_tag,home_starters_tag,home_subs_tag)
    away_team = find_team_details(away_team_tag,away_starters_tag,away_subs_tag)
    home_team.print_team()
    away_team.print_team()
    
def get_players(players_tag:bs4.element.Tag):
    players = []

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
            players.append(Player(name, number))

    # Example: print all players
    return players
    

def scrape_game_details(game_id):
    url = BASE_URL + f"?game_id={game_id}"
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    gid = "gfd_" + str(game_id)
    game_details = soup.find("section",id=gid)
    gtime_div = game_details.find("div", id="gTimeHolder")
    date_text = gtime_div.find("span", class_="date").get_text(strip=True).split("|")[0] #works
    find_teams(game_details)
    fixture_number = find_fixture(game_details)
    
    
    
    

def main():
    scrape_game_details(1060404)

if __name__ == "__main__":
    main()
