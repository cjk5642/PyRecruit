"""collection script holds collection classes for players
and teams based on url.
"""

from bs4 import BeautifulSoup
import requests
from .utils import HEADERS
from tqdm import tqdm

class CollectPlayers:
    """Collection of Players utility class to select top 
    n players
    """
    def __init__(self, url: str, top: int, players_class: str = "rankings-page__list-item"):
        self._url = url
        self.top = top
        self.players_class = players_class

    def _regular_players(self) -> list:
        """Extract non predictions of players given heuristic
        characteristcs. 

        Returns:
            list: list of all collect players
        """
        print("Parsing Regular players...")
        all_players = []

        new_url = self._url + "&Page=1"
        page = requests.get(new_url, headers = HEADERS, timeout=10)
        soup = BeautifulSoup(page.content, "html.parser")
        players = page.findAll("li", class_ = "rankings-page__list-item")[:-1]
        players = [p.find('div', class_ = "wrapper") for p in players]

        # add first page of players to all players
        all_players.extend(players)
        num_players = len(players)
        
        # check if the number of requested players is already within the first page
        if num_players >= self.top and self.top != 'all':
            return all_players[:self.top]

        # if multiple pages are needed then collect the players
        i = 2
        pbar = tqdm(total = self.top - num_players)
        while num_players < self.top:
            new_url = self._url + f"&Page={i}"
            page = requests.get(new_url, headers = HEADERS, timeout=10)
            soup = BeautifulSoup(page.content, "html.parser")
            players = soup.findAll("li", class_ = "rankings-page__list-item")[:-1]
            for p in players:
                p = p.find('div', class_ = "wrapper")
                if num_players < self.top:
                    num_players += 1
                    pbar.update(1)
                    all_players.append(p)
                else:
                    break
            i += 1
        return all_players

    def _crystal_ball_players(self) -> list:
        """Collect all of the top N crystall ball recruits

        Returns:
            list: crystal ball players
        """
        print("Parsing Crystal ball players...")
        all_players = []
        
        new_url = self._url + "?Page=1"
        page = requests.get(new_url, headers = HEADERS, timeout=10)
        soup = BeautifulSoup(page.content, "html.parser")
        players = soup.findAll("li", class_ = "target")
        players = [p.find('ul') for p in players]
        
        # add first page of players to all players
        all_players.extend(players)
        num_players = len(players)
        
        # check if the number of requested players is already within the first page
        if self.top != 'all' and num_players >= self.top:
            return all_players[:self.top]

        # if multiple pages are needed then collect the players
        i = 2
        pbar = tqdm(total = self.top - num_players)
        while num_players < self.top:
            new_url = self._url + f"?Page={i}"
            page = requests.get(new_url, headers = HEADERS, timeout=10)
            soup = BeautifulSoup(page.content, "html.parser")
            players = soup.findAll("li", class_ = "target")
            for p in players:
                ps = p.find('ul', class_ = "wrapper")
                if num_players < self.top:
                    num_players += 1
                    pbar.update(1)
                    all_players.append(ps)
                else:
                    break
            i += 1
        return all_players
    
    @property
    def players(self):
        """Method to collect the players from the url.

        Returns:
            List: List of all players.
        """
        if self.players_class == "rankings-page__list-item":
            return self._regular_players()
        if self.players_class == 'target':
            return self._crystal_ball_players()
        raise ValueError("Incorrect selection")

class CollectTeams:
    """Class to collect all of the teams based on top N teams
    """
    def __init__(self, url: str, top: int, teams_class:str = "rankings-page__list-item"):
        self._url = url + r"?ViewPath=~%2FViews%2FSkyNet%2FInstitutionRanking%2F_SimpleSetForSeason.ascx"
        self.top = top
        self.teams_class = teams_class

    def _regular_teams(self):
        print("Parsing Regular teams...")
        all_teams = []

        new_url = self._url + "&Page=1"
        page = requests.get(new_url, headers = HEADERS, timeout=10)
        soup = BeautifulSoup(page.content, "html.parser")
        teams = soup.findAll("li", class_ = "rankings-page__list-item")
        teams = [p.find('div', class_ = "wrapper") for p in teams]

        # add first page of teams to all teams
        all_teams.extend(teams)
        num_teams = len(teams)
        
        # check if the number of requested teams is already within the first page
        if self.top != 'all' and num_teams >= self.top:
            return all_teams[:self.top]

        # if multiple pages are needed then collect the players
        i = 2
        pbar = tqdm(total = self.top - num_teams)
        while num_teams < self.top:
            new_url = self._url + f"&Page={i}"
            page = requests.get(new_url, headers = HEADERS, timeout=10)
            soup = BeautifulSoup(page.content, "html.parser")
            players = soup.findAll("li", class_ = "rankings-page__list-item")
            for p in players:
                p = p.find('div', class_ = "wrapper")
                if num_teams < self.top:
                    num_teams += 1
                    pbar.update(1)
                    all_teams.append(p)
                else:
                    break
            i += 1
        return all_teams
    
    @property
    def teams(self):
        """Method to collect the teams from the url.

        Returns:
            List: List of all teams.
        """
        if self.teams_class == "rankings-page__list-item":
            return self._regular_teams()
        if self.teams_class == 'target':
            raise NotImplementedError