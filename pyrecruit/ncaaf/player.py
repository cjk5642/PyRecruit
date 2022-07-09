"""
Recruit script to collect group of Players and specific 
players by designated ids from 247sports.com.
"""

from bs4 import BeautifulSoup
import pandas as pd
import requests
from tqdm import tqdm
from .utils import HEADERS, Ratings247, CollegeRecruitingInterest, Evaluators, Connections, Expert
from .datamodels import PlayerExtended, PlayerPreview
from typing import List, Tuple, Union, Dict
from dataclasses import asdict

union_str_none = Union[str, None]

class Players:
    """Collect all players given multiple parameters. This will scrape players from 247sports.com
    that come with multiple attributes per recruit.
    """
    players = None
    def __init__(self, 
                 year:int = None, 
                 institution:str = "HighSchool", 
                 pos:str = None, 
                 composite_rankings:bool = True, 
                 state:str = None,
                 top:int = 100):

        self.year = 2022 if not year else year
        self.institution = institution
        self.pos = self._check_position(pos) if pos else None
        self.top = top
        self.composite_rankings = composite_rankings
        self.state = state
        if not Players.players:
            self._url = self._create_url()
            self._html_players = self._parse_players()
            Players.players = self._get_players()

    def _check_position(self, pos:str) -> str:
        """Check the players position to see if it
        is a valid position in football.

        Args:
            pos (str): Given position from the page

        Raises:
            ValueError: If the given position is not 
            in the list of valid positions

        Returns:
            str: Returns the valid position
        """
        positions = ["QB", "RB", "WR", "TE", "OT", "IOL", "EDGE", "DL", "LB", "CB", "S", "ATH", "K", "P", "LS", "RET"]
        joined_pos = ', '.join(positions)
        pos = pos.upper()
        if pos not in positions:
            raise ValueError(f"Position '{pos}' is not a valid position. Please use one of the following:\n[{joined_pos}]")
        return pos

    def _create_url(self) -> str:
        """Method to create the url from the given parameters.

        Returns:
            str: Url for the given parameters.
        """
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

    def _parse_players(self) -> list:
        """Method to collect the players from the url.

        Returns:
            List: List of all players.
        """
        all_players = []
        print("Parsing players...")
        new_url = self._url + f"&Page=1"
        page = requests.get(new_url, headers = HEADERS)
        soup = BeautifulSoup(page.content, "html.parser")
        players = soup.findAll("li", class_ = "rankings-page__list-item")[:-1]
        players = [p.find('div', class_ = "wrapper") for p in players]
        
        # add first page of players to all players
        all_players.extend(players)
        num_players = len(players)
        
        # check if the number of requested players is already within the first page
        if num_players >= self.top:
            return all_players[:self.top]

        # if multiple pages are needed then collect the players
        i = 2
        pbar = tqdm(total = self.top - num_players)
        while num_players < self.top:
            new_url = self._url + f"&Page={i}"
            page = requests.get(new_url, headers = HEADERS)
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

    def _get_ranking(self, player: BeautifulSoup) -> Tuple[union_str_none, union_str_none]:
        """Method to collect the players ranking from the webpage.

        Args:
            player (BeautifulSoup): Webpage to be scraped.

        Returns:
            Tuple[Union[str, None], Union[str, None]]: Player's ranking
        """
        ranking = player.find('div', class_ = "rank-column")
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

    def _get_recruit(self, player: BeautifulSoup) -> Tuple[union_str_none, union_str_none, union_str_none, union_str_none]:
        """Method to collect the players metadata like name, location, and link.

        Args:
            player (BeautifulSoup): Webpage to be scraped

        Returns:
            Tuple[union_str_none, union_str_none, union_str_none]: Recruit link, Name, and Location
        """
        
        recruit = player.find('div', class_ = "recruit")
        recruit_meta = recruit.find("a", class_ = "rankings-page__name-link")
        recruit_link = recruit_meta['href']
        recruit_name = recruit_meta.text.replace(" \n", "").strip()
        recruit_id = recruit_link.split("/")[-1].strip()

        recruit_location = recruit.find("span", class_ = "meta").text.replace("\n", "").strip()
        recruit_location = " ".join(recruit_location.split())

        recruit_high_school, recruit_location = recruit_location.split("(")
        recruit_high_school = recruit_high_school.strip()
        recruit_location = recruit_location.rstrip(")")
        return recruit_id, recruit_link, recruit_name, recruit_high_school, recruit_location

    def _get_position(self, player: BeautifulSoup) -> union_str_none:
        """Get the player's position

        Args:
            player (BeautifulSoup): Webpage to be scraped

        Returns:
            union_str_none: Player's position
        """
        position = player.find("div", class_ = 'position')
        position = position.text.replace("\n", "").replace(" ", "")
        return position

    def _get_metrics(self, player: BeautifulSoup) -> union_str_none:
        """Collect the players metrics.

        Args:
            player (BeautifulSoup): Webpage to be scraped

        Returns:
            union_str_none: Player's metrics
        """
        metrics = player.find("div", class_ = "metrics").text
        metrics = " ".join(metrics.split())

        height, weight = metrics.split(" / ")

        weight = int(weight) if weight else None
        return height, weight

    def _get_ratings(self, player: BeautifulSoup) -> Tuple[union_str_none, union_str_none, union_str_none]:
        """Get the Player's ratings.

        Args:
            player (BeautifulSoup): Webpage to be scraped

        Returns:
            Tuple[union_str_none, union_str_none, union_str_none]: Player's ratings
        """
        ratings = player.find("div", class_ = "rating")
        score = ratings.find("div", class_ = "rankings-page__star-and-score")
        score = score.find("span", class_ = "score").text

        rank = ratings.find("div", class_ = "rank")
        national_rank = rank.find("a", class_ = "natrank").text.replace("\n", "").replace(" ", "")
        position_rank = rank.find("a", class_ = "posrank").text.replace("\n", "").replace(" ", "")
        state_rank = rank.find("a", class_ = "sttrank").text.replace("\n", "").replace(" ", "")
        
        national_rank = int(national_rank) if national_rank else None
        position_rank = int(position_rank) if position_rank else None
        state_rank = int(state_rank) if state_rank else None
        
        return national_rank, position_rank, state_rank

    def _get_status(self, player:BeautifulSoup) -> Tuple[union_str_none, union_str_none]:
        """Collect the status of the player. Status would be Signed or None

        Args:
            player (BeautifulSoup): Webpage to be scraped

        Returns:
            Tuple[union_str_none, union_str_none]: Player's status
        """
        status = player.find("div", class_ = "status")

        # if player is committed to team
        team = status.find("a", class_ = "img-link")
        if team:
            team = team.find("img")['alt']
            return team, 'Committed', None, None

        # if player is not committed or almost committed
        team_helper = status.find("div", class_ = "rankings-page__crystal-ball")
        team_helper_sub = team_helper.find("div", class_ = "cb-block")
        team = team_helper_sub.find("img")
        if not team:
            return None, None, None, None
            
        team = team['alt']
        percentage = team_helper_sub.find("span", class_ = "percentage").text.strip()
        
        # check if second crystball team prediction exists
        team_helper2 = team_helper.find("div", class_="cb-block cb-block--bottom")
        if not team_helper2:
            return team, percentage, None, None

        # second team exists
        team2 = team_helper2.find('img')['alt']
        percentage2 = team_helper2.find('span', class_ = 'percentage').text.strip()
        return team, percentage, team2, percentage2
        
    
    def _get_players(self) -> List[PlayerPreview]:
        """Method to collect the players and store it in the class method
        .players .

        Returns:
            List[Dict]: Collection of players
        """
        players = []
        for player in tqdm(self._html_players):
            primary_ranking, other_ranking = self._get_ranking(player)
            recruit_id, recruit_link, recruit_name, recruit_hs, recruit_location = self._get_recruit(player)
            position = self._get_position(player)
            height, weight = self._get_metrics(player)
            national_rank, position_rank, state_rank = self._get_ratings(player)
            committed_team, committed_team_percentage, committed_team2, committed_team_percentage2 = self._get_status(player)
            player = PlayerPreview(
                id = recruit_id,
                name=recruit_name,
                link=recruit_link,
                high_school=recruit_hs,
                location=recruit_location,
                position=position,
                height=height,
                weight=weight,
                primary_ranking=primary_ranking,
                other_ranking=other_ranking,
                national_rank=national_rank,
                position_rank=position_rank,
                state_rank=state_rank,
                commitment1=committed_team,
                committed_team_percentage1=committed_team_percentage,
                commitment2=committed_team2,
                committed_team_percentage2=committed_team_percentage2
            )
            players.append(player)

        # cache player list in class
        Players.players = players
        return players 

    @property
    def dataframe(self) -> pd.DataFrame:
        """Method to extract the players as dataframe.

        Returns:
            pd.DataFrame: Pandas dataframe of all the players.
        """
        if Players.players is None:
            Players.players = self.get_players
        
        return pd.DataFrame.from_dict([asdict(p) for p in Players.players])

class Player:
    """Player class that extracts all of the details according to the player.
    """
    def __init__(self, name_id:str):
        """Name_id found from 247 sports player page like Travis-Hunter-46084728"""
        self.name_id = name_id
        self.url = f"https://247sports.com/Player/{self.name_id}/"

    def _get_page(self, url: str) -> BeautifulSoup:
        """Method to collect the page given the players name_id

        Args:
            url (str): Url of the player from name_id

        Returns:
            BeautifulSoup: Webpage to be scraped of the player
        """

        if not url.startswith("https:"):
            url = "https:" + url
        page = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(page.content, "html.parser")
        return soup

    @property  
    def player(self) -> PlayerExtended:
        """Main method to extract the player details given the name_id.

        Returns:
            PlayerDC: The player's data class with multiple data features.
        """
        soup = self._get_page(self.url)

        # determine if older or current recruit
        as_a_prospect = soup.find("section", class_="as-a-prospect")
        if as_a_prospect:
            profile_link = as_a_prospect.find("a", class_='view-profile-link')['href']
            soup = self._get_page(profile_link)

        print("Recruit name...")
        recruit_name = soup.find("h1", class_ = "name").text 

        # find metrics
        print("Getting metrics...")
        metrics = self._find_metrics(soup)

        # find details
        print("Getting details...")
        details = self._find_details(soup)
        
        # get rankings
        print("Getting rankings...")
        ratings_data = Ratings247(soup, metrics['pos'], details['state']).ratings

        # get expert predictions
        print("Getting predictions...")
        experts = self._find_predictions(soup)

        # get college interest
        print("Getting College Interests...")
        college_interest = CollegeRecruitingInterest(soup).college_interest

        # get accolades
        print("Getting Accolades...")
        accolades = self._find_accolades(soup)

        # get evaluators, background and skills
        print("Getting Evaluators, Background, and Skills...")
        evaluators, background, skills = Evaluators(soup).evaluator

        # get stats
        print("Getting stats...")
        stats = self._find_stats(soup)

        # get Connections
        print("Getting Connections...")
        connections = Connections(soup).connections

        return PlayerExtended(
            name_id = self.name_id, 
            url = self.url, 
            recruit_name = recruit_name, 
            experts = experts, 
            college_interest = college_interest,
            accolades = accolades,
            evaluators = evaluators,
            background = background, 
            skills = skills, 
            stats = stats,
            connections = connections,
            ratings=ratings_data,
            **metrics,
            **details
        )

    def _find_metrics(self, soup_page: BeautifulSoup) -> Dict:
        """Collect the player's metrics

        Args:
            soup_page (BeautifulSoup): Webpage to be scraped

        Returns:
            Dict: Player's metrics like position, height and weight
        """
        data = {}
        metrics = soup_page.find("ul", class_ = "metrics-list").find_all("li")
        for m in metrics:
            spans =  m.find_all("span")
            if spans[0].text == 'Pos':
                data['pos'] = spans[1].text
            if spans[0].text == "Height":
                data['height'] = spans[1].text
            if spans[0].text == 'Weight':
                data['weight'] = int(spans[1].text)
        return data

    def _find_details(self, soup_page: BeautifulSoup) -> Dict:
        """Collect the Players details like high school name and location.

        Args:
            soup_page (BeautifulSoup): Webpage to be scraped

        Returns:
            Dict: Player's details
        """
        details = soup_page.find("ul", class_ = "details").find_all("li")
        data = {}
        for d in details:
            spans = d.find_all("span")
            if spans[0].text == 'High School':
                data['high_school'] = spans[1].find("a").text.strip()
            elif spans[0].text == 'City':
                data['city'], data['state'] = spans[1].text.strip().split(", ")
            elif spans[0].text.lower().strip() == "class":
                data['class_year'] = int(spans[1].text.strip())
        return data

    def _get_expert_averages(self, soup: BeautifulSoup) -> Union[None, Dict]:
        """Collect the averages from the Experts. This changes the 
        school name and collects from another page.

        Args:
            soup (BeautifulSoup): Webpage to be scraped

        Returns:
            Union[None, Dict]: None or dictionary of conversions
        """
        expert_averages = soup.find("ul", class_ = "prediction-list long")
        if not expert_averages:
            return None

        list_ea = expert_averages.find_all('li')[1:]
        list_ea_dict = {}
        for lea in list_ea:
            link = lea.find('a').find('img', class_ = 'team-image')['src']
            name = lea.find("span").text
            list_ea_dict[link] = name
        return list_ea_dict

    def _get_extended_predictions(self, url:str) -> List[Expert]:
        """Collect the predictions from experts

        Args:
            url (str): Url of all experts predictions

        Returns:
            List[Expert]: List of all expert predictions of player
        """
        soup = self._get_page(url)
        lead_experts = soup.find("ul", class_='cb-list no-border').find_all('li')
        other_experts = soup.find("ul", class_='cb-list no-margin').find_all('li')
        total_experts = lead_experts + other_experts
        expert_list = []
        for expert in total_experts:

            # get name and title
            exp = expert.find("div", class_='name')
            name = exp.find("a").text.strip()
            title = exp.find_all("span")[-1].text.strip()

            # get accuracy for this year
            acc_year = expert.find("div", class_="accuracy year").find_all('span')[-1].text
            acc_year = float(acc_year.translate(str.maketrans("", "", "()%"))) / 100

            # get accuracy for all time
            acc_all = expert.find("div", class_="accuracy all-time").find_all('span')[-1].text
            acc_all = float(acc_all.translate(str.maketrans("", "", "()%"))) / 100

            # get prediction
            prediction = expert.find('div', class_='prediction')
            pred = prediction.find("img")['alt']
            pred_date = prediction.find("div", class_='date-time')
            if pred_date:
                date_time = ' '.join([tag.text.strip() for tag in pred_date.find_all("span")])
            else:
                date_time = None

            # get expert score
            score = expert.find("div", class_='confidence')
            expert_score = int(score.find("div", class_="confidence-wrap").find("b").text.strip())


            new_exp = Expert(
                name = name, title = title, accuracy_year=acc_year, 
                accuracy_all_time=acc_all, prediction=pred, 
                prediction_datetime=date_time, expert_score=expert_score
            )

            expert_list.append(new_exp)
        return expert_list

    def _find_predictions(self, soup: BeautifulSoup) -> Union[None, Expert, List[Expert]]:
        """Method to collect the predictions for the player based 
        on experts.

        Args:
            soup (BeautifulSoup): Webpage to be scraped

        Returns:
            Union[None, Expert, List[Expert]]: None, Expert or list of experts giving
            predictions on the recruit.
        """
        experts = soup.find("ul", class_ = "prediction-list long expert")
        if not experts:
            return None
        
        # see if there are extended experts 
        link_block = soup.find("ul", class_='link-block')
        if link_block:
            link = link_block.find('a')['href']
            return self._get_extended_predictions(link)

        img_conversion = self._get_expert_averages(soup)
        if img_conversion:
            lead_experts = experts.find_all("li")[1:]
            lead_experts_list = []
            for i, expert in enumerate(lead_experts):
                expert_name = expert.find('a', class_='expert-link').text
                score = expert.find('b', class_ = "confidence-score lock").text
                college = img_conversion[expert.find('img')['src']]
                expert = Expert(name=expert_name, expert_score=score, prediction=college)
                lead_experts_list.append(expert)
            return lead_experts_list[0] if len(lead_experts_list) == 0 else lead_experts_list
        
    def _find_accolades(self, soup: BeautifulSoup) -> Union[None, List[str]]:
        """Method to find players accolades if exists.

        Args:
            soup (BeautifulSoup): Webpage to be scraped

        Returns:
            Union[None, List[str]]: None or list of player's accolades
        """
        accolades = soup.find('section', class_ = 'accolades')
        if not accolades:
            return None
        
        accolades_list = accolades.find("ul").find_all("li")
        accolades_final = [accolade.find('a', class_='event-link').text for i, accolade in enumerate(accolades_list)]
        return accolades_final
        
    def _find_stats(self, soup: BeautifulSoup) -> Union[None, pd.DataFrame]:
        """Method to find the players stats over their
        high school career.

        Args:
            soup (BeautifulSoup): Webpage to be scraped

        Returns:
            Union[None, pd.DataFrame]: None or dataframe of players stats
        """
        stats = soup.find('section', class_="profile-stats")
        if not stats:
            return None

        left_table_html = str(stats.find("table", class_='left-table'))
        right_table_html = str(stats.find('table', class_='right-table'))
        left_table = pd.read_html(left_table_html)[0]
        right_table = pd.read_html(right_table_html)[0]
        total = pd.concat([left_table, right_table], axis = 1)
        return total