import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

class Players:
    def __init__(self, 
                 year:int = None, 
                 institution:str = "HighSchool", 
                 pos:str = None, 
                 composite_rankings:bool = True, 
                 state:str = None):

        self.year = 2022 if not year else year
        self.institution = institution
        self.pos = self._check_position(pos) if pos else None
        self.composite_rankings = composite_rankings
        self.state = state
        self.url = self._create_url()
        self.html_players = self._parse_players()
        self.players = self._filter_players()

    def _check_position(self, pos:str):
        positions = ["QB", "RB", "WR", "TE", "OT", "IOL", "EDGE", "DL", "LB", "CB", "S", "ATH", "K", "P", "LS", "RET"]
        joined_pos = ', '.join(positions)
        pos = pos.upper()
        if pos not in positions:
            raise ValueError(f"Position '{pos}' is not a valid position. Please use one of the following:\n[{joined_pos}]")
        return pos

    def _create_url(self):
        base_url = "https://247sports.com/Season/"
        year_part = f"{self.year}-Football/"
        rankings_part = "CompositeRecruitRankings/?" if self.composite_rankings else "RecruitRankings/?"
        
        # queries
        institution_part = f"InstitutionGroup={self.institution}"

        # join the strings for url
        join_base_str = base_url + year_part + rankings_part + institution_part

        # check if any additional patterns are matched
        if self.pos:
            join_base_str += f"&PositionGroup={self.pos}"
        
        if self.state:
            join_base_str += f"&State={self.state}"

        return join_base_str

    def _parse_players(self):
        HEADERS = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
        }
        page = requests.get(self.url, headers=HEADERS)
        soup = BeautifulSoup(page.content, 'html.parser')
        players = soup.findAll("li", class_ = "rankings-page__list-item")
        players = [p.find('div', class_ = "wrapper") for p in players]
        return players

    def _get_ranking(self, player: str):
        try:
            ranking = player.find('div', class_ = "rank-column")
            primary = ranking.find('div', class_ = "primary").text.replace("\n", "").replace(" ", "")
            other = ranking.find("div", class_ = "other").text.replace("\n", "").replace(" ", "")
            return primary, other
        except (ValueError, AttributeError):
            return None, None

    def _get_recruit(self, player: str):
        try:
            recruit = player.find('div', class_ = "recruit")
            recruit_meta = recruit.find("a", class_ = "rankings-page__name-link")
            recruit_link = recruit_meta['href']
            recruit_name = recruit_meta.text.replace(" \n", "").strip()

            recruit_location = recruit.find("span", class_ = "meta").text.replace("\n", "").strip()
            recruit_location = " ".join(recruit_location.split())
            return recruit_link, recruit_name, recruit_location
        except AttributeError:
            return None, None, None

    def _get_position(self, player: str):
        try:
            return player.find("div", class_ = 'position').text.replace("\n", "").replace(" ", "")
        except AttributeError:
            return None

    def _get_metrics(self, player: str):
        try:
            metrics = player.find("div", class_ = "metrics").text
            return " ".join(metrics.split())
        except AttributeError:
            return None

    def _get_ratings(self, player: str):
        try:
            ratings = player.find("div", class_ = "rating")
            score = ratings.find("div", class_ = "rankings-page__star-and-score")
            score = score.find("span", class_ = "score").text

            rank = ratings.find("div", class_ = "rank")
            national_rank = rank.find("a", class_ = "natrank").text.replace("\n", "").replace(" ", "")
            position_rank = rank.find("a", class_ = "posrank").text.replace("\n", "").replace(" ", "")
            state_rank = rank.find("a", class_ = "sttrank").text.replace("\n", "").replace(" ", "")
            return national_rank, position_rank, state_rank
        except AttributeError:
            return None, None, None


    def _get_status(self, player:str):
        try:
            status = player.find("div", class_ = "status")
        except AttributeError:
            return None, None

        # if player is commited to team
        try: 
            team = status.find("a", class_ = "img-link").find("img")['alt']
            return team, None
        except:
            pass

        # if player is not committed or almost committed
        team_helper = status.find("div", class_ = "rankings-page__crystal-ball").find("div", class_ = "cb-block")
        try:
            team = team_helper.find("img")['alt']
            percentage = team_helper.find("span", class_ = "percentage").text.strip()
            return team, percentage
        
        except:
            return None, None

    def _filter_players(self):
        players = []
        for player in tqdm(self.html_players):
            p_dict = {}
            p_dict['primary_ranking'], p_dict['other_ranking'] = self._get_ranking(player)
            p_dict['recruit_link'], p_dict['recruit_name'], p_dict['recruit_location'] = self._get_recruit(player)
            p_dict['position'] = self._get_position(player)
            p_dict['metrics'] = self._get_metrics(player)
            p_dict['national_rank'], p_dict['position_rank'], p_dict['state_rank'] = self._get_ratings(player)
            p_dict['commited_team'], p_dict['commited_team_percentage'] = self._get_status(player)
            players.append(p_dict)
        return pd.DataFrame.from_dict(players)

class Player:
    def __init__(self):
        pass