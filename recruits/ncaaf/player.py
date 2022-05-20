from bs4 import BeautifulSoup
import pandas as pd
import requests
from tqdm import tqdm
from collections import defaultdict
from .datamodels import *
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
}

class Players:
    def __init__(self, 
                 year:int = None, 
                 institution:str = "HighSchool", 
                 pos:str = None, 
                 composite_rankings:bool = True, 
                 state:str = None,
                 top:int = 1000):

        self.year = 2022 if not year else year
        self.institution = institution
        self.pos = self._check_position(pos) if pos else None
        self.top = top
        self.composite_rankings = composite_rankings
        self.state = state
        self.url = self._create_url()
        self.html_players = self._parse_players()
        self.dataframe = self._filter_players()

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
        all_players = []
        print("Parsing players...")
        new_url = self.url + f"&Page=1"
        page = requests.get(new_url, headers = HEADERS)
        soup = BeautifulSoup(page.content, "html.parser")
        players = soup.findAll("li", class_ = "rankings-page__list-item")[:-1]
        players = [p.find('div', class_ = "wrapper") for p in players]
        all_players.extend(players)

        num_players = len(players)
        i = 2
        pbar = tqdm(total = self.top - num_players)
        while num_players < self.top:
            new_url = self.url + f"&Page={i}"
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
    def __init__(self, name_id:str):
        """name_id found from 247 sports player page like Travis-Hunter-46084728"""
        self.name_id = name_id
        self.url = f"https://247sports.com/Player/{self.name_id}/"

    @property  
    def player(self):
        page = requests.get(self.url, headers=HEADERS)
        soup = BeautifulSoup(page.content, "html.parser")

        print("Recruit name...")
        recruit_name = soup.find("h1", class_ = "name").text 

        # find metrics
        print("Getting metrics...")
        pos, height, weight = self._find_metrics(soup)

        # find details
        print("Getting details...")
        high_school, city, state, class_year = self._find_details(soup)
        
        # get rankings
        print("Getting rankings...")
        ratings_data = self._find_ratings(soup, pos, state)

        # get expert predictions
        print("Getting predictions...")
        experts = self._find_predictions(soup)

        # get college interest
        print("Getting College Interests...")
        college_interest = self._find_college_interest(soup)

        # get accolades
        print("Getting Accolades...")
        accolades = self._find_accolades(soup)

        # get evaluators, background and skills
        print("Getting Evaluators, Background, and Skills...")
        evaluators, background, skills = self._find_scouting_report(soup)

        # get stats
        print("Getting stats...")
        stats = self._find_stats(soup)

        # get Connections
        print("Getting Connections...")
        connections = Connections(soup).connections

        return PlayerDC(
            name_id = self.name_id, 
            url = self.url, 
            recruit_name = recruit_name, 
            pos = pos, 
            height = height, 
            weight = weight,
            high_school = high_school, 
            city = city, 
            state = state, 
            class_year = class_year,
            experts = experts, 
            college_interest = college_interest,
            accolades = accolades,
            evaluators = evaluators,
            background = background, 
            skills = skills, 
            stats = stats,
            connections = connections,
            **ratings_data
        )

    def _find_metrics(self, soup_page):
        metrics = soup_page.find("ul", class_ = "metrics-list").find_all("li")
        for m in metrics:
            spans =  m.find_all("span")
            if spans[0].text == 'Pos':
                pos = spans[1]
            elif spans[0].text == "Height":
                height = spans[1]
            else:
                weight = spans[1]
        return pos, height, weight

    def _find_details(self, soup_page):
        details = soup_page.find("ul", class_ = "details").find_all("li")
        for d in details:
            spans = d.find_all("span")
            if spans[0].text == 'High School':
                hs = spans[1].find("a").text
            elif spans[0].text == 'City':
                city, state = spans[1].text.split(", ")
            elif spans[0].text == "Class":
                cls = spans[1].text
        return hs, city, state, cls

    def _find_ratings(self, soup_page, pos, state):
        ratings_sections = soup_page.find_all("section", class_ = "rankings-section")
        data = {}
        for rs in ratings_sections:
            title = rs.find("h3", class_ = 'title').text
            if 'composite' in title.lower():
                ranking = rs.find("div", class_ = "ranking")
                data['composite_score'] = ranking.find("div", class_ = "rank-block")
                rank_list = rs.find("ul", class_ = "ranks-list").find_all("li")
                for rl in rank_list:
                    rank_name, rank_value = rl.find("b").text, rl.find("a").find("strong").text
                    if rank_name == 'Natl.':
                        data['national_composite_rank'] = rank_value
                    elif rank_name == pos:
                        data['position_composite_rank'] = rank_value
                    else:
                        data['state_composite_rank'] = rank_value
            else:
                ranking = rs.find("div", class_ = "ranking")
                data['normal_score'] = ranking.find("div", class_ = "rank-block")
                rank_list = rs.find("ul", class_ = "ranks-list").find_all("li")
                for rl in rank_list:
                    rank_name, rank_value = rl.find("b").text, rl.find("a").find("strong").text
                    if rank_name == 'Natl.':
                        data['national_normal_rank'] = rank_value
                    elif rank_name == pos:
                        data['position_normal_rank'] = rank_value
                    else:
                        data['state_normal_rank'] = rank_value
        return data

    def _get_expert_averages(self, soup):
        expert_averages = soup.find("ul", class_ = "prediction-list long")
        list_ea = expert_averages.find_all('li')[1:]
        list_ea_dict = {}
        for lea in list_ea:
            link = lea.find('a').find('img', class_ = 'team-image')['src']
            name = lea.find("span").text
            list_ea_dict[link] = name
        return list_ea_dict

    def _find_predictions(self, soup):
        experts = soup.find("ul", class_ = "prediction-list long expert")
        if not experts:
            return None

        img_conversion = self._get_expert_averages(soup)
        lead_experts = experts.find_all("li")[1:]
        lead_experts_dict = defaultdict(dict)
        for i, expert in enumerate(lead_experts):
            expert_name = expert.find('a', class_='expert-link').text
            lead_experts_dict[expert_name]['expert_score'] = expert.find('b', class_ = "confidence-score lock").text
            lead_experts_dict[expert_name]['school'] = img_conversion[expert.find('img')['src']]
        return lead_experts_dict

    def _find_college_interest(self, soup):
        view_all_colleges = soup.find('a', class_ = "college-comp__view-all")
        school_list = []
        if view_all_colleges:
            url = view_all_colleges['href']
            page = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(page.content, "html.parser")
            interests = soup.find("ul", class_ = "recruit-interest-index_lst")
            first_blocks = interests.find_all("div", class_='first_blk')
            second_blocks = interests.find_all('div', class_='secondary_blk')
            for first_block, second_block in zip(first_blocks, second_blocks):
                
                # collect college name
                first_block_a = first_block.find_all('a')
                college_name = "".join(first_block_a[0].text.split())

                # collect college statuses
                college_status = first_block.find('span', class_ = 'status')
                college_status_text = college_status.find('span', class_='grey')
                if college_status_text:
                    college_status_text = "Signed"
                else:
                    college_status_text = college_status.find('span').text
                
                college_status_date = college_status.find("a")
                if college_status_date:
                    college_status_date = college_status_date.text
                else:
                    college_status_date = None

                # collect visit
                visit = second_block.find('span', class_='visit').text
                if '-' in visit:
                    visit = None
                
                # collect offer
                offer = second_block.find('span', class_='offer').text.strip()
                if 'yes' in offer.lower():
                    offer = True
                else:
                    offer = False

                # collect recruited by
                recruited_by = second_block.find("ul", class_='interest-class_lst')
                if not recruited_by:
                    recruiters = None
                else:
                    recruited_by = recruited_by.find_all("li")
                    recruiters = []
                    for recruiter in recruited_by:
                        recruiter = recruiter.find("a").text

                school = CollegeInterest(
                    college=college_name, status=college_status_text,
                    status_date=college_status_date, visit=visit, offered=offer
                )
                school_list.append(school)      
                break  

        else:
            schools = soup.find('ul', class_ = "college-comp__body-list").find_all('li')
            for school in schools:
                # get college name
                college_name = school.find('div', class_="college-comp__team-block") \
                .find('a', class_="college-comp__team-name-link").text

                # get offer
                offer = school.find("div", class_ = "college-comp__offer-block")
                if offer.find('b', class_ = "college-comp__offer-check checkmark"):
                    offer = True
                else:
                    offer = False
                
                if school.find("span", class_="college-comp__interest-level college-comp__interest-level--signed-bg"):
                    signed = True
                else:
                    signed = False
                
                school = CollegeInterest(
                    college=college_name, status=college_status_text,
                    status_date=college_status_date, visit=visit, offered=offer
                )
                school_list.append(school)
        return school_list

    def _find_accolades(self, soup):
        accolades = soup.find('section', class_ = 'accolades')
        if not accolades:
            return None
        
        accolades_list = accolades.find("ul").find_all("li")
        accolades_final = [accolade.find('a', class_='event-link').text for i, accolade in enumerate(accolades_list)]
        return accolades_final

    def _get_background_skills(self, soup):
        ## collect background
        background_skills = soup.find("div", class_="background-and-skills")
        background = background_skills.find("section", class_="athletic-background")
        if background:
            background = background.find("div", class_='body')
            background_text = " ".join([string.strip() for string in background.strings]).replace("\r", '').strip()
        else:
            background_text = None

        ## collect skills
        skills = background_skills.find("section", class_='skills')
        if skills:
            skills = skills.find('div', class_='body').find('ul').find_all('li')
            skills_dict = {}
            for skill in skills:
                skill_text = skill.find("span", class_='text').text
                skill_rating = int(skill.find("b").text)
                skills_dict[skill_text] = skill_rating
        else:
            skills_dict = None

        return background_text, skills_dict


    def _find_scouting_report(self, soup):
        scouting_report = soup.find("section", class_="scouting-report")
        if not scouting_report:
            return None

        evaluations = scouting_report.find("header").find('a', class_='view-all-eval-link')
        if evaluations:
            url = evaluations['href']
            page = requests.get(url, headers = HEADERS)
            soup = BeautifulSoup(page.content, 'lxml')
            evaluators = soup.find("section", class_="main-content list-content")
            evaluators_list = evaluators.find("ul", class_='evaluation-list').find_all("li")
            evaluators_dict = list()
            for evaluator in evaluators_list:
                eval_id = evaluator.get('id')
                eval_id = int(eval_id) if eval_id else None
                eval_list = evaluator.find("ul", class_ = "highlights-list")
                if eval_list:
                
                    # evaluator name and region0
                    evaluator_eval = eval_list.find("li", class_="eval-meta evaluator")
                    name = evaluator_eval.find("b", class_="text").text
                    region = evaluator_eval.find("span", class_="uppercase").text

                    # get projection
                    evaluator_projection = eval_list.find("li", class_="eval-meta projection")
                    projection = evaluator_projection.find("b", class_="text").text

                    # get comparison
                    evaluator_comparison = eval_list.find_all('li', class_='eval-meta', partial=False)[-1]
                    comparison = evaluator_comparison.find("a", attrs = {"target": "_blank"})
                    if comparison:
                        comparison = comparison.text
                    else:
                        comparison = None
                    
                    comparison_team = evaluator_comparison.find("span", class_="uppercase")
                    if comparison_team:
                        comparison_team = comparison_team.text
                    else:
                        comparison_team = None

                    # get evaluation
                    evaluation_data = evaluator.find("p", class_="eval-text")
                    evaluation_date = evaluation_data.find("strong", class_="eval-date").text.strip()
                    evaluation_text = evaluation_data.text.strip().split("\n")[-1].strip()

                    evaluators_dataclass = Evaluator(
                        id = eval_id, name = name, region = region, projection = projection, comparison=comparison,
                        comparison_team=comparison_team, evaluation_date=evaluation_date, evaluation=evaluation_text
                    )
                    evaluators_dict.append(evaluators_dataclass)

            # get background_and_skills
            background, skills = self._get_background_skills(scouting_report)

        else:
            evaluators = soup.find('section', class_='scouting-report')
            evaluators_dict = defaultdict(dict)

            # get highlights
            highlights = evaluators.find("section", class_="highlights")
            eval_date = highlights.find('div').find('h4').text.split(" ")[-1]
            evaluator = highlights.find("div", class_='evaluator')
            name = evaluator.find("b", class_='text').text
            region = evaluator.find('span', class_='uppercase').text

            # get projections
            projection = highlights.find("div", class_='projection').find('b').text

            # get comparison
            comparison = highlights.find_all('div')[-1]
            comparison_name = comparison.find('a').text
            comparison_team = comparison.find("span").text

            # get evaluations
            evaluation = evaluators.find("p", class_='eval-text').get_text().strip()

            # store evaluation
            evaluators_dataclass = Evaluator(
                name = name, region = region, projection = projection, comparison=comparison_name,
                comparison_team=comparison_team, evaluation_date=eval_date, evaluation=evaluation
            )
            evaluators_dict[name] = evaluators_dataclass

            # collect background and skills
            background, skills = self._get_background_skills(evaluators)

        return evaluators_dict, background, skills
        
    def _find_stats(self, soup):
        stats = soup.find('section', class_="profile-stats")
        if not stats:
            return None

        left_table_html = str(stats.find("table", class_='left-table'))
        right_table_html = str(stats.find('table', class_='right-table'))
        left_table = pd.read_html(left_table_html)[0]
        right_table = pd.read_html(right_table_html)[0]
        total = pd.concat([left_table, right_table], axis = 1)
        return total

class Connections:
    def __init__(self, soup):
        self.soup = soup
    
    @property
    def connections(self):
        pedigree = self.soup.find('section', class_ = 'pedigree')
        if not pedigree:
            return None

        pedigree = pedigree.find('div', class_ = 'body').find_all('li')
        connections = []
        for ped in pedigree:
            name = ped.find('a', class_ = 'name')
            if name:
                name = name.text
            else:
                name = ped.find('b', class_ = 'name').text

            relation = ped.find('span', class_ = 'relation').text
            accolades = ped.find('span', class_='accolades')
            accolades = "".join([string for string in accolades.strings])
            connection = Connection(
                name = name, relation=relation, accolades=accolades
            )
            connections.append(connection)
        return connections

class Staff:
    def __init__(self, name_id:str = None, url:str = None, soup:str = None):
        self.name_id = name_id
        self.url = url
        self.soup = soup
        self.page = self._gain_primary()

    def _gain_primary(self):
        if self.soup:
            return self.soup
        
        if self.url:
            page = requests.get(self.url, headers = HEADERS)
            soup = BeautifulSoup(page.content, 'html.parser')
            return soup
        
        if self.name:
            url = f"https://247sports.com/Coach/{self.name_id}/"
            page = requests.get(url, headers = HEADERS)
            soup = BeautifulSoup(page.content, 'html.parser')
            return soup
    
    @property
    def member(self):
        pass

    def _get_meta(self, soup):
        data = {}
        # get name
        data['name'] = soup.find('h1', class_='name').strip()

        # get metrics
        metrics_list = soup.find("ul", class_='metrics-list').find_all('li')
        for ml in metrics_list:
            met = ml.find_all('span')
            if met[0].lower() == 'job':
                data['job'] = met[1].strip()

        # get alma mater
        coach_details = soup.find("ul", class_='details coach').find_all('li')
        for cd in coach_details:
            if cd.get('class') == 'coach-alma-mater-item':
                data['alma_mater'] = cd.find_all('span')[-1].strip()

        # get vitals and team info
        team = soup.find('section', class_='team-block')
        if team:
            data['college'] = team.find('h2').text.strip()
            vitals = team.find('ul', class_='vitals').find_all('li')
            for v in vitals:
                v = v.find_all('span')
                if v[0] == 'Age':
                    data['staff_member_age'] = int(v[1]) if v[1] else None

        return data
    
    def _get_ratings(self, soup):
        data = {}
        rankings = soup.find('section', class_='rankings-section').find_all('li')
        for rank in rankings:
            rank_name = rank.find('b').text
            rank_value = rank.find('a').find('strong').text.strip()
            data[rank_name] = rank_value
        return data

    def _get_commites(self, soup):
        pass
