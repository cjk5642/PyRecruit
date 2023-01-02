"""
Recruit script to collect group of Players and specific 
players by designated ids from 247sports.com.
"""

from bs4 import BeautifulSoup
import pandas as pd
import requests
from tqdm import tqdm
from .utils import HEADERS
from .recruiting_interest import CollegeRecruitingInterest
from .connections import Connections
from .evaluators import Evaluators
from .collection import CollectPlayers
from .ratings247 import Ratings247
from .datamodels import PlayerCrystalBall, PlayerExtended, PlayerPreview, Expert, \
    AbstractPlayer, CrystalballPlayersDC, PlayersDC
from datetime import datetime

class Players:
    """Collect all players given multiple parameters. This will scrape players from 247sports.com
    that come with multiple attributes per recruit.
    """
    def __init__(self, 
                 year:int = None, 
                 institution:str = "HighSchool", 
                 pos:str = None, 
                 composite_rankings:bool = True, 
                 state:str = None,
                 top:int = 100):

        self.year = int(datetime.now().year) if not year else year
        self.institution = institution
        self.pos = self._check_position(pos) if pos else None
        self.top = top
        self.composite_rankings = composite_rankings
        self.state = state
        self._url = self._create_url()
        self._html_players = CollectPlayers(self._url, self.top).players

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

    def _get_ranking(self, player: BeautifulSoup) -> tuple[str, str]:
        """Method to collect the players ranking from the webpage.

        Args:
            player (BeautifulSoup): Webpage to be scraped.

        Returns:
            tuple[str, str]: Player's ranking
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

    def _get_recruit(self, player: BeautifulSoup) -> tuple[str, str, str, str]:
        """Method to collect the players metadata like name, location, and link.

        Args:
            player (BeautifulSoup): Webpage to be scraped

        Returns:
            tuple[str, str, str]: Recruit link, Name, and Location
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

        city, state = recruit_location.split(", ")
        return recruit_id, recruit_link, recruit_name, recruit_high_school, city, state

    def _get_position(self, player: BeautifulSoup) -> str:
        """Get the player's position

        Args:
            player (BeautifulSoup): Webpage to be scraped

        Returns:
            str: Player's position
        """
        position = player.find("div", class_ = 'position')
        position = position.text.replace("\n", "").replace(" ", "")
        return position

    def _get_metrics(self, player: BeautifulSoup) -> str:
        """Collect the players metrics.

        Args:
            player (BeautifulSoup): Webpage to be scraped

        Returns:
            str: Player's metrics
        """
        metrics = player.find("div", class_ = "metrics").text
        metrics = " ".join(metrics.split())

        height, weight = metrics.split(" / ")

        weight = int(weight) if weight else None
        return height, weight

    def _get_ratings(self, player: BeautifulSoup) -> tuple[str, str, str]:
        """Get the Player's ratings.

        Args:
            player (BeautifulSoup): Webpage to be scraped

        Returns:
            tuple[str, str, str]: Player's ratings
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

    def _get_status(self, player:BeautifulSoup) -> tuple[str, str]:
        """Collect the status of the player. Status would be Signed or None

        Args:
            player (BeautifulSoup): Webpage to be scraped

        Returns:
            tuple[str, str]: Player's status
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
        
    @property
    def players(self) -> list[PlayerPreview]:
        """Method to collect the players and store it in the class method
        .players .

        Returns:
            list[PlayerPreview]: Collection of players
        """
        players = []
        for player in tqdm(self._html_players):
            primary_ranking, other_ranking = self._get_ranking(player)
            recruit_id, recruit_link, recruit_name, recruit_hs, city, state = self._get_recruit(player)
            position = self._get_position(player)
            height, weight = self._get_metrics(player)
            national_rank, position_rank, state_rank = self._get_ratings(player)
            committed_team, committed_team_percentage, committed_team2, committed_team_percentage2 = self._get_status(player)
            
            # establish abstract player
            abstract_player = AbstractPlayer(
                name_id = recruit_id,
                recruit_name=recruit_name,
                url=recruit_link,
                high_school=recruit_hs,
                city=city,
                state=state,
                position=position,
                height=height,
                weight=weight,
                class_year=self.year,
            )
            
            player = PlayerPreview(
                abstract_player=abstract_player,
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

        return PlayersDC(players = players)

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
        page = requests.get(url, headers=HEADERS, timeout=10)
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

        # estbalish abstract player
        abstract_player = AbstractPlayer(
            name_id = self.name_id, 
            url = self.url, 
            recruit_name = recruit_name,
            **details,
            **metrics
        )

        return PlayerExtended(
            abstract_player=abstract_player,
            experts = experts, 
            college_interest = college_interest,
            accolades = accolades,
            evaluators = evaluators,
            background = background, 
            skills = skills, 
            stats = stats,
            connections = connections,
            ratings=ratings_data
        )

    def _find_metrics(self, soup_page: BeautifulSoup) -> dict:
        """Collect the player's metrics

        Args:
            soup_page (BeautifulSoup): Webpage to be scraped

        Returns:
            dict: Player's metrics like position, height and weight
        """
        data = {}
        metrics = soup_page.find("ul", class_ = "metrics-list").find_all("li")
        for m in metrics:
            spans =  m.find_all("span")
            if spans[0].text == 'Pos':
                data['position'] = spans[1].text
            if spans[0].text == "Height":
                data['height'] = spans[1].text
            if spans[0].text == 'Weight':
                data['weight'] = int(spans[1].text)
        return data

    def _find_details(self, soup_page: BeautifulSoup) -> dict:
        """Collect the Players details like high school name and location.

        Args:
            soup_page (BeautifulSoup): Webpage to be scraped

        Returns:
            dict: Player's details
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

    def _get_expert_averages(self, soup: BeautifulSoup) -> dict:
        """Collect the averages from the Experts. This changes the 
        school name and collects from another page.

        Args:
            soup (BeautifulSoup): Webpage to be scraped

        Returns:
            dict: None or dictionary of conversions
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

    def _get_extended_predictions(self, url:str) -> list[Expert]:
        """Collect the predictions from experts

        Args:
            url (str): Url of all experts predictions

        Returns:
            list[Expert]: list of all expert predictions of player
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

    def _find_predictions(self, soup: BeautifulSoup) -> Expert | list[Expert]:
        """Method to collect the predictions for the player based 
        on experts.

        Args:
            soup (BeautifulSoup): Webpage to be scraped

        Returns:
            Union[None, Expert, list[Expert]]: None, Expert or list of experts giving
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
            for expert in lead_experts:
                expert_name = expert.find('a', class_='expert-link').text
                score = expert.find('b', class_ = "confidence-score lock").text
                college = img_conversion[expert.find('img')['src']]
                expert = Expert(name=expert_name, expert_score=score, prediction=college)
                lead_experts_list.append(expert)
            return lead_experts_list[0] if len(lead_experts_list) == 0 else lead_experts_list
        
    def _find_accolades(self, soup: BeautifulSoup) -> list[str]:
        """Method to find players accolades if exists.

        Args:
            soup (BeautifulSoup): Webpage to be scraped

        Returns:
            list[str]: None or list of player's accolades
        """
        accolades = soup.find('section', class_ = 'accolades')
        if not accolades:
            return None
        
        accolades_list = accolades.find("ul").find_all("li")
        accolades_final = [accolade.find('a', class_='event-link').text for i, accolade in enumerate(accolades_list)]
        return accolades_final
        
    def _find_stats(self, soup: BeautifulSoup) -> pd.DataFrame:
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

class CrystalBall:
    """Collects the crystal ball predictions from this recruiting year. For example,
    if the current year is 2022, then football season is the 2022-2023 season. The crystal
    ball predictions will be for the 2023 recruiting class."""
    players = None
    def __init__(self, top: int = 100):
        self._year = datetime.now().year + 1
        self._url = f"https://247sports.com/Season/{self._year}-Football/CurrentTargetPredictions/"

        self.top = top
        if not CrystalBall.players:
            self._players = CollectPlayers(self._url, self.top, players_class="target").players
            CrystalBall.players = self._get_players()
    
    def _get_details(self, player: BeautifulSoup) -> tuple:
        """Collect the details of the recruit in the crystal
        ball predictor

        Args:
            player (BeautifulSoup): soup page to be parsed

        Returns:
            tuple: Details of the recruit
        """
        details = player.find("li", class_='name')
        a_details = details.find("a")

        url = a_details['href'].strip()
        recruit_id = url.split("/")[-2]
        recruit_name = " ".join(a_details.text.split())
        recruit_name, class_year = recruit_name.strip().split("(")
        class_year = int(class_year.rstrip(")"))

        # extract bottom part of details block
        extra_details, ranking = details.findAll('span')[1:3]
        pos, height, weight = extra_details.text.strip().split(" / ")

        # collect stars and rating
        rating = ranking.find("b").text
        rating = None if rating == 'NA' else float(rating)
        if not rating:
            stars = None
        else:
            stars = len(list(ranking.findAll("span", class_="icon-starsolid yellow")))
    
        return recruit_id, url, recruit_name, class_year, pos, height, int(weight), stars, rating

    def _get_predictor(self, player: BeautifulSoup) -> tuple:
        """Collect details on the person predicting 
        on the recruit

        Args:
            player (BeautifulSoup): soup page to be parsed

        Returns:
            tuple: Details of the predictor
        """
        predicted_by = player.find("li", class_="predicted-by")
        info = predicted_by.find("a")
        link = info['href']
        id_predictor = link.strip().split("/")[-3]

        name, affiliation = info.findAll("span")
        name, affiliation = name.text.strip(), affiliation.text.strip()
        
        return id_predictor, name, link, affiliation

    def _get_predictor_accuracy(self, player: BeautifulSoup) -> str:
        """Collect general accuracy of the predictor

        Args:
            player (BeautifulSoup): soup page to be parsed

        Returns:
            str: accuracy of the predictor
        """
        accuracy = player.find("li", class_='accuracy')
        accuracy = accuracy.findAll("span")[1].text.strip().lstrip('(').rstrip(")")
        return accuracy

    def _get_prediction(self, player: BeautifulSoup) -> tuple:
        """Collect prediction of the predictor

        Args:
            player (BeautifulSoup): soup page to be parsed

        Returns:
            tuple: details of the prediction
        """
        prediction = player.find("li", class_='prediction')
        prediction_team = prediction.find('div').find('img')['alt']
        prediction_datetime = prediction.find("span", class_="prediction-date").text.strip()
        return prediction_team, prediction_datetime

    def _get_prediction_confidence(self, player: BeautifulSoup) -> tuple:
        """Collect the confidence of the prediction from the predictor

        Args:
            player (BeautifulSoup): soup page to be parsed

        Returns:
            tuple: details of the prediction
        """
        confidence = player.find("li", class_="confidence")
        confidence_score, confidence_text = confidence.findAll("b")

        confidence_text_value = confidence_text.text if confidence_text.text != 'Med' else 'Medium'

        # check if it is a vip scoop
        scoop = confidence.find("a", class_='scoop-link')
        if not scoop:
            return int(confidence_score.text), confidence_text_value, False
        else:
            return int(confidence_score.text), confidence_text_value, True

    def _get_players(self) -> list[PlayerCrystalBall]:
        """Collect all of the players from the crystal ball

        Returns:
            list[PlayerCrystalBall]: All predicted recruits
        """
        all_players = []

        for player in self._players:
            # get player details
            name_id, url, recruit_name, class_year, \
                pos, height, weight, stars, rating = self._get_details(player)
            
            # get predictor details
            predictor_id, predictor_name, predictor_link, predictor_affiliation = self._get_predictor(player)
            predictor_accuracy = self._get_predictor_accuracy(player)

            # get prediction details
            prediction_team, prediction_datetime = self._get_prediction(player)
            confidence_score, confidence_text, vip_scoop = self._get_prediction_confidence(player)

            # establish abstract player
            abstract_player = AbstractPlayer(
                name_id=name_id,
                url=url,
                recruit_name=recruit_name,
                class_year=class_year,
                position=pos,
                height=height,
                weight=weight
            )

            # store player in the crystal ball dataclass
            player_dc = PlayerCrystalBall(
                abstract_player=abstract_player,
                stars=stars,
                rating=rating,
                predictor_id=predictor_id,
                predictor_name=predictor_name,
                predictor_link=predictor_link,
                predictor_affiliation=predictor_affiliation,
                predictor_accuracy=predictor_accuracy,
                prediction_team=prediction_team,
                prediction_datetime=prediction_datetime,
                confidence_score=confidence_score,
                confidence_text=confidence_text,
                vip_scoop=vip_scoop
            )
            all_players.append(player_dc)
        return CrystalballPlayersDC(players = all_players)