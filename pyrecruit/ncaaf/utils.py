"""
Utilities class for NCAAF Players and Teams
"""

import requests
from .datamodels import *
from bs4 import BeautifulSoup
from typing import Union, List, Tuple, Dict

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
}

class Staff:
    """Staff class that produces the staff member given the webpage
    """
    def __init__(self, name_id:str = None, url:str = None, soup:BeautifulSoup = None):
        self.name_id = name_id
        self.url = url
        self.soup = soup
        self.page = self._gain_primary()

    def _gain_primary(self) -> BeautifulSoup:
        """Method to obtain the BeautifulSoup page

        Returns:
            BeautifulSoup: page given the different identifiers
        """
              
        if self.url:
            page = requests.get(self.url, headers = HEADERS)
            soup = BeautifulSoup(page.content, 'html.parser')
            return soup
        
        if self.name_id:
            url = f"https://247sports.com/Coach/{self.name_id}/"
            page = requests.get(url, headers = HEADERS)
            soup = BeautifulSoup(page.content, 'html.parser')
            return soup
        
        return self.soup
        
    def _get_meta(self, page: BeautifulSoup) -> Dict:
        """Collect the metadata on the staff member

        Args:
            page (BeautifulSoup): webpage to be scraped

        Returns:
            Dict: metadata of the coach like job position, alma mater, and age
        """
        data = {}

        # get name
        data['name'] = page.find('h1', class_='name').text.strip()

        # get metrics
        metrics_list = page.find("ul", class_='metrics-list').find_all('li')
        for ml in metrics_list:
            met = ml.find_all('span')
            if met[0].text.lower() == 'job':
                data['position'] = met[1].text.strip()

        # get alma mater
        coach_details = page.find("ul", class_='details coach')
        if coach_details:
            coach_details = coach_details.find_all('li')
            for cd in coach_details:
                if cd.get('class') == 'coach-alma-mater-item':
                    data['alma_mater'] = cd.find_all('span')[-1].strip()

        # get vitals and team info
        team = page.find('section', class_='team-block')
        if team:
            data['college'] = team.find('h2').text.strip()
            vitals = team.find('ul', class_='vitals').find_all('li')
            for v in vitals:
                v = v.find_all('span')
                if v[0] == 'Age':
                    data['staff_member_age'] = int(v[1]) if v[1] else None

        return data
    
    def _get_ratings(self, page: BeautifulSoup) -> Dict:
        """Collect the ratings of the staff member

        Args:
            page (BeautifulSoup): webpage to be scraped

        Returns:
            Dict: Ratings data of the staff member like number of commits avg rank and so on.
        """

        data = {}
        rankings = page.find('section', class_='rankings-section')
        if not rankings:
            return None
        
        rankings = rankings.find_all('li')
        non_conf = ["commits", 'avg_rtg', 'natl_rk', 'star_5', 'star_4', 'star_3']
        for rank in rankings:
            # fix system to rearrange if the string starts with a number like 5
            rank_name = rank.find('b').text.replace('.', '').replace(' ', '_').replace('-', "_").lower()
            if rank_name[0].isdigit():
                num, star = rank_name.split('_')
                rank_name = "_".join([star, num])

            rank_value = rank.find('a')
            if rank_value:
                rank_value = rank_value.find('strong').text.strip()
                if rank_name in non_conf:
                    data[rank_name] = rank_value
                else:
                    data['conference'] = rank_value
        return data

    def _get_top_commits(self, page: BeautifulSoup) -> Union[None, List[TopCommit]]:
        """Collect the top commits of the coach.

        Args:
            page (BeautifulSoup): webpage to be scraped

        Returns:
            Union[None, List[TopCommit]]: The metadata of the player if found
        """
        commits = page.find_all('ul', class_='commits-details')
        if not commits:
            return None

        details = []
        for commit in commits:
            _, name, position, height_weight, rating, commitment = commit.find_all("li")

            # get name
            recruit_name = name.find('a', class_='player').text
            location = ' '.join([string.strip() for string in name.find_all("span")])

            # position
            position = position.find('span').text.strip()

            # find height and weight
            height, weight = height_weight.find('span').text.split(" / ")

            # find rating and stars
            stars = len(rating.find_all("span", class_="icon-starsolid yellow"))
            rating = float(rating.find('span', class_="rating").text)

            # find commitment
            college = commitment.find("a", class_='player-institution').find('img')['alt'].strip()
            commitment_date = commitment.find("span", class_='commit-date').text.strip()

            commit = TopCommit(
                name = recruit_name, location = location, position = position,
                height = height, weight = weight, stars = stars, rating = rating,
                college = college, commitment_date = commitment_date
            )
            details.append(commit)

        return details

    def _get_coach_history(self, page: BeautifulSoup) -> Union[None, List[CoachHistory]]:
        """Collect the history of the coach such as job positions

        Args:
            page (BeautifulSoup): webpage to be scraped

        Returns:
            Union[None, List[CoachHistory]]: _description_
        """
        coach_history = page.find("section", class_='coach-history')
        if not coach_history:
            return None
        
        coach_history = coach_history.find('div', class_='body').find_all('li')
        data = []
        for position in coach_history:
            college, (years, job) = position.find('img')['alt'], position.find_all('span')
            years, job = years.text.strip(), job.text.strip()

            coachhistory = CoachHistory(college=college, year=years, position=job)
            data.append(coachhistory)
        return data

    @property
    def member(self) -> StaffMember:
        """Output property for the Staff Member

        Returns:
            StaffMember: Staffmember dataclass that contains the just collected data
        """
        meta = self._get_meta(self.page)
        ratings = self._get_ratings(self.page)
        commits = self._get_top_commits(self.page)
        coach_history = self._get_coach_history(self.page)

        if ratings:
            return StaffMember(
                **meta, **ratings, top_commits=commits, coach_history=coach_history
            )
        else:
            return StaffMember(
                **meta, top_commits=commits, coach_history=coach_history
            )

class Connections:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
    
    @property
    def connections(self) -> Union[None, List[Connection]]:
        """Collect the connecions to the player

        Returns:
            Union[None, List[Connection]]: Data on the connections to the player
        """
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

class CollegeRecruitingInterest:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
    
    def _examine_more_colleges(self, url: str) -> List[CollegeInterest]:
        """Method to parse over page if there is long list of colleges. Congrats!

        Args:
            url (str): the url to the webpage that contains list of colleges

        Returns:
            List[CollegeInterest]: Data of all colleges that actively recruited recruit
        """
        school_list = []
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
            
            # collect the status of signature or not
            college_status_date = college_status.find("a")
            if college_status_date:
                college_status_date = college_status_date.text
                college_status_date = college_status_date.translate(str.maketrans("", "", "()"))
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
            recruited_by = second_block.find("ul", class_='interest-details_lst')
            if not recruited_by:
                recruiters = None
            else:
                recruited_by = recruited_by.find_all("li")[1:]
                recruiters = [Staff(url = recruiter.find("a")['href']).member for recruiter in recruited_by]

            school = CollegeInterest(
                college=college_name, status=college_status_text,
                status_date=college_status_date, visit=visit, offered=offer,
                recruited_by=recruiters
            )
            school_list.append(school)      
        return school_list

    @property
    def college_interest(self) -> Union[None, List[CollegeInterest]]:
        """Method to output the data of college

        Returns:
            Union[None, List[CollegeInterest]]: Data of all colleges interested in the recruit
        """
        view_all_colleges = self.soup.find('a', class_ = "college-comp__view-all")
        school_list = []
        if view_all_colleges:
            school_list = self._examine_more_colleges(view_all_colleges['href'])
        else:
            school_list = None
        return school_list

class BackgroundSkills:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup

    def _examine_background(self, page: BeautifulSoup) -> Union[None, str]:
        """Collect background info on the recruit other. Like their biography

        Args:
            page (BeautifulSoup): webpage to be scraped

        Returns:
            Union[None, str]: Biography text of the recruit
        """
        background = page.find("section", class_="athletic-background")
        if not background:
            return None

        # extract biography text
        background = background.find("div", class_='body')
        background_text = " ".join([string.strip() for string in background.strings]).replace("\r", '').strip()
        return background_text

    
    def _examine_skills(self, page: BeautifulSoup) -> Union[None, Skills]:
        """Method to find the skills of the player if listed

        Args:
            page (BeautifulSoup): webpage to be scraped

        Returns:
            Union[None, Skills]: Skills Dataclass that consist of the recruits skills
        """
        skills = page.find("section", class_='skills')
        if not skills:
            return None

        # collect the skills
        skills = skills.find('div', class_='body').find('ul').find_all('li')
        skills_dict = {}
        for skill in skills:
            skill_text = skill.find("span", class_='text').text
            skill_rating = int(skill.find("b").text)
            skills_dict[skill_text] = skill_rating
        return Skills.from_kwargs(**skills_dict)

    @property
    def background_skills(self) -> Tuple[Union[None, str], Union[None, Skills]]:
        """Method to output the background and skills

        Returns:
            Tuple[Union[None, str], Union[None, Skills]]: The background and skills of the player
        """
        background_skills = self.soup.find("div", class_="background-and-skills")
        background = self._examine_background(background_skills)
        skills = self._examine_skills(background_skills)
        return background, skills

class Evaluators:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup

    def _examine_multiple_evaluators(self, page: BeautifulSoup) -> List[Evaluator]:
        """Find evaluators data if the webpage allows for multiple evaluators

        Args:
            page (BeautifulSoup): webpage to be scraped

        Returns:
            List[Evaluator]: Evaluator dataclasses of the evaluators found evaluating
            the recruit.
        """

        evaluators = page.find("section", class_="main-content list-content")
        evaluators_list = evaluators.find("ul", class_='evaluation-list').find_all("li")
        evaluators_list = list()
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
                
                # see if there is a comparison team
                comparison_team = evaluator_comparison.find("span", class_="uppercase")
                if comparison_team:
                    comparison_team = comparison_team.text
                else:
                    comparison_team = None

                # get evaluation date and text
                evaluation_data = evaluator.find("p", class_="eval-text")
                evaluation_date = evaluation_data.find("strong", class_="eval-date").text.strip()
                evaluation_text = evaluation_data.text.strip().split("\n")[-1].strip()

                evaluators_dataclass = Evaluator(
                    id = eval_id, name = name, region = region, projection = projection, comparison=comparison,
                    comparison_team=comparison_team, evaluation_date=evaluation_date, evaluation=evaluation_text
                )
                evaluators_list.append(evaluators_dataclass)
        return evaluators_list

    def _examine_single_page_evaluators(self, page: BeautifulSoup) -> Union[None, Evaluator]:
        """Find evaluator if there is no external webpage.

        Args:
            page (BeautifulSoup): webpage to be scraped

        Returns:
            Union[None, Evaluator]: Evaluator data class that consists of Evaluator metadata
        """
        # get highlights
        highlights = page.find("section", class_="highlights")
        if not highlights:
            return None

        # get evaluator metadata
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
        evaluation = page.find("p", class_='eval-text').get_text().strip()

        # store evaluation
        evaluators_dataclass = Evaluator(
            name = name, region = region, projection = projection, comparison=comparison_name,
            comparison_team=comparison_team, evaluation_date=eval_date, evaluation=evaluation
        )
        
        return evaluators_dataclass

    @property
    def evaluator(self) -> Union[None, Tuple[List[Evaluator], Union[None, str], Union[None, Skills]], Tuple[Evaluator, Union[None, str], Union[None, Skills]]]:
        """Output method to collect the Evaluators

        Returns:
            Union[None, 
                  Tuple[List[Evaluator], Union[None, str], Union[None, Skills]], 
                  Tuple[Evaluator, Union[None, str], Union[None, Skills]]]: Evaluator dataclasses with
                  the background and skills dataclasses embedded
        """
        scouting_report = self.soup.find("section", class_="scouting-report")
        if not scouting_report:
            return None

        # collect evaluators
        evaluations = scouting_report.find("header").find('a', class_='view-all-eval-link')
        if evaluations:
            url = evaluations['href']
            page = requests.get(url, headers = HEADERS)
            soup = BeautifulSoup(page.content, 'lxml')
            evaluators_list = self._examine_multiple_evaluators(soup)
            background, skills = BackgroundSkills(scouting_report).background_skills

        else:
            evaluators = self.soup.find('section', class_='scouting-report')
            evaluators_list = self._examine_single_page_evaluators(evaluators)
            background, skills = BackgroundSkills(evaluators).background_skills

        return evaluators_list, background, skills

class Ratings247:
    def __init__(self, soup: BeautifulSoup, pos: str, state: str):
        self.soup = soup
        self.pos = pos
        self.state = state

    def _find_ratings_composite_helper(self, soup: BeautifulSoup, it: BeautifulSoup) -> Dict:
        """Collect the composite ratings of the recruit (247Sports Composite)

        Args:
            soup (BeautifulSoup): webpage to be scraped
            it (BeautifulSoup): position on webpage

        Returns:
            Dict: data that consists of the different composite scores
        """
        data = {}
        data['composite_score'] = soup.find("div", class_ = "rank-block").text
        if data['composite_score'] == 'N/A':
            data['composite_score'] = None
        else:
            data['composite_score'] = float("".join(data['composite_score'].split())) if data['composite_score'] else None
        
        rank_list = it.find("ul", class_ = "ranks-list").find_all("li")
        for rl in rank_list:
            rank_name, rank_value = rl.find("b").text, rl.find("a").find("strong").text
            if rank_value == 'N/A':
                rank_value = None

            if rank_name == 'Natl.':
                data['national_composite_rank'] = int(rank_value) if rank_value else None
            if rank_name == self.pos:
                data['position_composite_rank'] = int(rank_value) if rank_value else None
            if rank_name == self.state:
                data['state_composite_rank'] = int(rank_value) if rank_value else None
        return data

    def _find_ratings_normal_helper(self, soup: BeautifulSoup, it: BeautifulSoup) -> Dict:
        """Collect the normal ratings of the recruit (247Sports)

        Args:
            soup (BeautifulSoup): webpage to be scraped
            it (BeautifulSoup): position on webpage

        Returns:
            Dict: data that consists of the different normal scores
        """
        data = {}
        data['normal_score'] = soup.find("div", class_ = "rank-block").text.strip()
        if data['normal_score'] == 'N/A':
            data['normal_score'] = None
        else:
            data['normal_score'] = float("".join(data['normal_score'].split())) if data['normal_score'] else None

        rank_list = it.find("ul", class_ = "ranks-list").find_all("li")
        for rl in rank_list:
            rank_name, rank_value = rl.find("b").text, rl.find("a").find("strong").text
            # change n/a to None
            if rank_value == 'N/A':
                rank_value = None

            if rank_name == 'Natl.':
                data['national_normal_rank'] = int(rank_value) if rank_value else None
            if rank_name == self.pos:
                data['position_normal_rank'] = int(rank_value) if rank_value else None
            if rank_name == self.state:
                data['state_normal_rank'] = int(rank_value) if rank_value else None
        return data

    @property
    def ratings(self) -> Ratings:
        """Method to output Ratings dataclass that consist of Normal and
        Composite ratings.

        Returns:
            Ratings: Ratings dataclass that consist of Normal and 
            composite ratings.
        """
        ratings_sections = self.soup.find_all("section", class_ = "rankings-section")
        data = {}
        for rs in ratings_sections:
            title = rs.find("h3", class_ = 'title').text
            if 'composite' in title.lower():
                ranking = rs.find("div", class_ = "ranking")
                new_data = self._find_ratings_composite_helper(ranking, rs)
                data.update(new_data)
                
            else:
                ranking = rs.find("div", class_ = "ranking")
                new_data = self._find_ratings_normal_helper(ranking, rs)
                data.update(new_data)

        return Ratings(**data)