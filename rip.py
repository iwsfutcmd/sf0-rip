import requests
from bs4 import BeautifulSoup
import re
from time import sleep
import json
from dotenv import load_dotenv
import os
from tqdm import tqdm

load_dotenv()
SF0_URL = "http://sf0.org/"
RATE_LIMIT = 0.5
COOKIE = os.getenv("SF0_COOKIE")
HIGHEST_TASK_ID = 7000
HIGHEST_EVENT_ID = 500


def get_player_list():
    un_extractor = re.compile(r"http://sf0.org/(.+)/")
    players = []
    url = SF0_URL + "score/?order=oldest&t=forever"
    while True:
        print(url)
        soup = BeautifulSoup(requests.get(url).text)
        player_list = soup.select_one("#playerThumbs")
        for li in player_list("li"):
            a = li.a
            try:
                username = un_extractor.search(a["href"]).group(1)
            except AttributeError:
                username = ""
            id_n = a["id"]
            thumb = li.img["src"]
            players.append({"username": username, "id": id_n, "thumbnail_url": thumb})
        try:
            url = soup.select_one(".paginate").find(text="Next >>").parent["href"]
            sleep(RATE_LIMIT)
        except AttributeError:
            break
    with open("extracted_data/player_list.json", "w") as file:
        json.dump(players, file)
    return players


def get_task_list():
    task_name_extractor = re.compile(r"http://sf0.org/tasks/(.+)/")
    id_extractor = re.compile(r"get_task\((.+), this\)")
    base_url = SF0_URL + "tasks/?order=oldest"
    headers = {"cookie": COOKIE}
    tasks = {"act": [], "ret": [], "unscored": []}
    for status in tasks:
        url = base_url + f"&status={status}"
        print(url)
        soup = BeautifulSoup(requests.get(url, headers=headers).text)
        task_list = soup.select_one(".taskList")
        for li in task_list("li"):
            a = li.a
            try:
                task_name = task_name_extractor.search(a["href"]).group(1)
            except AttributeError:
                task_name = ""
            try:
                id_n = id_extractor.search(li.select_one(".tscore2")["onclick"]).group(
                    1
                )
            except (KeyError, AttributeError) as e:
                id_n = ""
            tasks[status].append({"task_name": task_name, "id": id_n})
        sleep(RATE_LIMIT)
    with open("extracted_data/task_list.json", "w") as file:
        json.dump(tasks, file)
    return tasks


def get_team_list():
    team_name_extractor = re.compile(r"http://sf0.org/teams/(.+)/")
    color_extractor = re.compile(r"\#[0-9A-F]+")
    teams = []
    url = SF0_URL + "teams/?order=oldest"
    while True:
        print(url)
        soup = BeautifulSoup(requests.get(url).text)
        player_list = soup.select_one("#playerThumbs")
        for li in player_list("li"):
            a = li.a
            try:
                team_name = team_name_extractor.search(a["href"]).group(1)
            except AttributeError:
                team_name = ""
            color = color_extractor.search(li["style"]).group()
            thumb = li.img["src"]
            teams.append(
                {"team_name": team_name, "color": color, "thumbnail_url": thumb}
            )
        try:
            url = soup.select_one(".paginate").find(text="Next >>").parent["href"]
            sleep(RATE_LIMIT)
        except AttributeError:
            break
    with open("extracted_data/team_list.json", "w") as file:
        json.dump(teams, file)
    return teams


def get_praxis_list():
    praxeis = []
    url = SF0_URL + "completedTasks/?disp=list&order=oldest&t=forever"
    while True:
        print(url)
        soup = BeautifulSoup(requests.get(url).text)
        praxis_list = soup.select_one("#praxis_list")
        for div in praxis_list.find_all("div", {"class": "praxis_l"}):
            a = div.a
            praxis_url = a["href"]
            thumb = a.img["src"]
            praxeis.append({"praxis_url": praxis_url, "thumbnail_url": thumb})
        try:
            url = soup.select_one(".paginate").find(text="Next >>").parent["href"]
            sleep(RATE_LIMIT)
        except AttributeError:
            break
    with open("extracted_data/praxis_list.json", "w") as file:
        json.dump(praxeis, file)
    return praxeis


def get_term_list():
    terms = []
    url = SF0_URL + "terms/?order=oldest"
    while True:
        print(url)
        soup = BeautifulSoup(requests.get(url).text)
        for term_list in soup.select(".term_list"):
            for li in term_list("li"):
                a = li.a
                term_url = a["href"]
                terms.append(term_url)
        try:
            url = soup.select_one(".paginate").find(text="Next >>").parent["href"]
            sleep(RATE_LIMIT)
        except AttributeError:
            break
    with open("extracted_data/term_list.json", "w") as file:
        json.dump(terms, file)
    return terms


def get_all_tasks(start_on=0, end_on=HIGHEST_TASK_ID):
    base_url = SF0_URL + "taskDetail/"
    for i in tqdm(range(start_on, end_on + 1)):
        url = base_url + f"?id={i}"
        soup = BeautifulSoup(requests.get(url).text)
        task_content = soup.select_one("#content")
        if task_content.h2.text == "Oops!":
            continue
        else:
            with open(f"extracted_data/tasks/{i}.html", "w") as file:
                file.write(str(task_content))
        sleep(RATE_LIMIT)


def get_all_events(start_on=1, end_on=HIGHEST_EVENT_ID):
    base_url = SF0_URL + "events/"
    for i in tqdm(range(start_on, end_on + 1)):
        url = base_url + f"?id={i}"
        r = requests.get(url, allow_redirects=False)
        if r.status_code == 302:
            continue
        else:
            soup = BeautifulSoup(r.text)
            task_content = soup.select_one("#content")
            with open(f"extracted_data/events/{i}.html", "w") as file:
                file.write(str(task_content))
        sleep(RATE_LIMIT)


def get_all_teams():
    base_url = SF0_URL + "teams/"
    team_list = json.load(open("extracted_data/team_list.json"))
    for team in tqdm(team_list):
        team_name = team["team_name"]
        url = base_url + team_name + "/"
        r = requests.get(url)
        soup = BeautifulSoup(r.text)
        team_content = soup.select_one("#c_wrap")
        os.makedirs(f"extracted_data/teams/{team_name}/", exist_ok=True)
        with open(f"extracted_data/teams/{team_name}/index.html", "w") as file:
            file.write(str(team_content))
        sleep(RATE_LIMIT)

        discourse_url = url + "discourse/"
        r = requests.get(discourse_url)
        soup = BeautifulSoup(r.text)
        discourse_content = soup.select_one("#content")
        os.makedirs(f"extracted_data/teams/{team_name}/discourse", exist_ok=True)
        with open(
            f"extracted_data/teams/{team_name}/discourse/index.html", "w"
        ) as file:
            file.write(str(discourse_content))
        sleep(RATE_LIMIT)


def get_all_players():
    base_url = SF0_URL
    subpages = [
        ("grouposis", "grouposis"),
        ("relations/?type=friends", "relations/friends"),
        ("relations/?type=foes", "relations/foes"),
        ("favorites", "favorites"),
        ("terms", "terms"),
    ]
    player_list = json.load(open("extracted_data/player_list.json"))
    for player in tqdm(player_list):
        username = player["username"]
        if not username:
            continue
        url = base_url + username + "/"
        r = requests.get(url)
        soup = BeautifulSoup(r.text)
        player_content = soup.select_one("#c_wrap")
        os.makedirs(f"extracted_data/players/{username}/", exist_ok=True)
        with open(f"extracted_data/players/{username}/index.html", "w") as file:
            file.write(str(player_content))
        sleep(RATE_LIMIT)

        for subpage_url_bit, save_location in subpages:
            subpage_url = url + subpage_url_bit
            r = requests.get(subpage_url)
            soup = BeautifulSoup(r.text)
            subpage_content = soup.select_one("#content")
            os.makedirs(
                f"extracted_data/players/{username}/{save_location}", exist_ok=True
            )
            with open(
                f"extracted_data/players/{username}/{save_location}/index.html", "w"
            ) as file:
                file.write(str(subpage_content))
            sleep(RATE_LIMIT)


def get_all_praxis():
    save_location_extractor = re.compile(r"http://sf0.org/(.+)")
    praxis_list = json.load(open("extracted_data/praxis_list.json"))
    for praxis in tqdm(praxis_list):
        praxis_url = praxis["praxis_url"]
        save_location = save_location_extractor.search(praxis_url).group(1)
        r = requests.get(praxis_url)
        soup = BeautifulSoup(r.text)
        praxis_content = soup.select_one("#content")
        os.makedirs(f"extracted_data/praxis/{save_location}/", exist_ok=True)
        with open(f"extracted_data/praxis/{save_location}/index.html", "w") as file:
            file.write(str(praxis_content))
        sleep(RATE_LIMIT)


def get_all_terms():
    save_location_extractor = re.compile(r"http://sf0.org/(.+)")
    term_list = json.load(open("extracted_data/term_list.json"))
    for term_url in tqdm(term_list):
        save_location = save_location_extractor.search(term_url).group(1)
        r = requests.get(term_url)
        soup = BeautifulSoup(r.text)
        term_content = soup.select_one("#content")
        os.makedirs(f"extracted_data/{save_location}/", exist_ok=True)
        with open(f"extracted_data/{save_location}/index.html", "w") as file:
            file.write(str(term_content))
        sleep(RATE_LIMIT)
