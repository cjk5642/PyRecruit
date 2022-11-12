from bs4 import BeautifulSoup
import pandas as pd
import requests
from tqdm import tqdm
from .utils import HEADERS, CollegeRecruitingInterest, Connections, Evaluators, Expert, CollectTeams, Ratings247
from .datamodels import PlayerCrystalBall, PlayerExtended, PlayerPreview
from typing import List, Tuple, Union, Dict
from dataclasses import asdict
from datetime import datetime

union_str_none = Union[str, None]

class Teams:
    """Collect all teams with given parameters. 
    This will scrape teams that come with multiple attributes per recruit.
    """
    teams = None
    def __init__(self, 
                 year:int = None,
                 top: int or str = 'all'):
        self.year = int(datetime.now().year) if not year else year
        self.top = top
        if not Teams.teams:
            self._url = self._create_url()
            self._html_teams = CollectTeams(self._url, self.conf, self.top).teams
            Teams.teams = self._get_teams()
    
    def _create_url(self):
        base_url = "https://247sports.com/Season/"
        year_part = f"{self.year}-Football/CompositeTeamRankings/"
        
        # join parts to create url
        join_base_str = base_url + year_part

        return join_base_str

    def _get_ranking(self, team: BeautifulSoup):
        ranking = team.find('div', class_='rank-column')

        # collect primary ranking
        primary = ranking.find('div', class_ = "primary")
        if not primary:
            primary = None
        else:
            primary = primary.text.replace("\n", "").replace(" ", "")
        
        # collect other ranking
        other = ranking.find("div", class_ = "other")
        if not other:
            other = None
        else:
            other = other.text.replace("\n", "").replace(" ", "")
        
        primary = int(primary) if primary else None
        other = int(other) if other else None

        return primary, other

    def _get_team_name(self, team:BeautifulSoup):
        team_block = team.find("div", class_="team").find("a", class_="rankings-page__name-list")
        team_name = team_block.text.replace("\n", "").replace(" ","")
        team_id = team_block['href'].split(r"college/")[1].split("/")[0]
        return team_name, team_id
    
    def _get_total_commits(self, team:BeautifulSoup):
        total_commits = team.find('div', class_="total")
        number = total_commits.find('a').text.replace("\n", "").replace(" ", "")
        return int(number)

    def _get_teams(self):
        teams = []
        for team in tqdm(self._html_teams):
            #team = TeamPreview()
            teams.append(team)
            break
        Teams.teams = teams
        return teams

    @property
    def dataframe(self) -> pd.DataFrame:
        """Method to extract the teams as dataframe.

        Returns:
            pd.DataFrame: Pandas dataframe of all the teams
        """
        return pd.DataFrame.from_dict([asdict(p) for p in Teams.teams])

class Team:
    def __init__(self):
        pass

class CrystalBall:
    def __init__(self):
        pass