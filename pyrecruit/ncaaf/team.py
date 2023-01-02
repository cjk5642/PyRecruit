import pandas as pd
from tqdm import tqdm
from .collection import CollectTeams
from .datamodels import TeamPreview
from dataclasses import asdict
from datetime import datetime
from bs4 import BeautifulSoup


class Teams:
    """Collect all teams with given parameters. 
    This will scrape teams that come with multiple attributes per recruit.
    """
    teams = None
    def __init__(self, 
                 year:int = 2023,
                 top: int = 100):
        self.year = int(datetime.now().year) if not year else year
        self.top = top
        if not Teams.teams:
            self._url = self._create_url()
            self._html_teams = CollectTeams(self._url, self.top).teams
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
        team_block = team.find("div", class_="team").find("a", class_="rankings-page__name-link")
        team_name = team_block.text.replace("\n", "").replace(" ","")
        team_id = team_block['href'].split(r"college/")[1].split("/")[0]
        return team_name, team_id
    
    def _get_total_commits(self, team:BeautifulSoup):
        total_commits = team.find('div', class_="total")
        number = total_commits.find('a').text.replace("\n", "").strip().split(" ")[0]
        return int(number)

    def _get_team_average(self, team:BeautifulSoup):
        team_avg = team.find('div', class_="avg")
        avg = team_avg.text.replace("\n", "").strip()
        return float(avg)

    def _get_team_stars(self, team:BeautifulSoup):
        conv = {"5": 'five', "4": 'four', '3': 'three'}

        team_stars = team.find('ul', class_='star-commits-list').find_all('li')
        team_data = {}
        for team_li in team_stars:
            star_type = team_li.find('h2').text.replace("\n", "").strip().split('-')[0]
            conv_star = conv[star_type] + '_star'
            num_stars = team_li.find('div').text.replace("\n", "").strip()
            team_data[conv_star] = num_stars
        return team_data

    def _get_team_points(self, team:BeautifulSoup):
        point_numbers = team.find('div', class_='points').find('a', class_='number')
        return float(point_numbers.text.strip().replace("\n", ""))

    def _get_teams(self):
        teams = []
        for team in tqdm(self._html_teams):
            primary_ranking, other_ranking = self._get_ranking(team)
            team_name, team_id = self._get_team_name(team)
            total_commits = self._get_total_commits(team)
            team_average = self._get_team_average(team)
            team_stars = self._get_team_stars(team)
            team_points = self._get_team_points(team)
            teams.append(
                TeamPreview(
                    team_id=team_id,
                    team_name=team_name,
                    primary_ranking=primary_ranking,
                    other_ranking=other_ranking,
                    total_commiits=total_commits,
                    team_avg=team_average,
                    team_points=team_points,
                    **team_stars
                )
            )
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