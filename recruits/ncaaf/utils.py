import requests
from datamodels import *
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
}

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

class CollegeRecruitingInterest:
    def __init__(self, soup):
        self.soup = soup
    
    def _examine_more_colleges(self, url:str):
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
        return school_list

    def _examine_present_colleges(self, page):
        school_list = []
        schools = page.find('ul', class_ = "college-comp__body-list").find_all('li')
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

    @property
    def college_interest(self):
        view_all_colleges = self.soup.find('a', class_ = "college-comp__view-all")
        school_list = []
        if view_all_colleges:
            school_list = self._examine_more_colleges(view_all_colleges['href'])

        else:
            school_list = self._examine_present_colleges(self.soup)
        return school_list

class BackgroundSkills:
    def __init__(self, soup):
        self.soup = soup

    def _examine_background(self, page):
        background = page.find("section", class_="athletic-background")
        if not background:
            return None

        background = background.find("div", class_='body')
        background_text = " ".join([string.strip() for string in background.strings]).replace("\r", '').strip()
        return background_text

    def _examine_skills(self, page):
        skills = page.find("section", class_='skills')
        if not skills:
            return None

        skills = skills.find('div', class_='body').find('ul').find_all('li')
        skills_dict = {}
        for skill in skills:
            skill_text = skill.find("span", class_='text').text
            skill_rating = int(skill.find("b").text)
            skills_dict[skill_text] = skill_rating
        return skills_dict

    @property
    def background_skills(self):
        ## collect background
        background_skills = self.soup.find("div", class_="background-and-skills")
        background = self._examine_background(background_skills)
        skills = self._examine_skills(background_skills)
        return background, skills

class Evaluators:
    def __init__(self, soup):
        self.soup = soup

    def _examine_multiple_evaluators(self, page):
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
                evaluators_list.append(evaluators_dataclass)
        return evaluators_list

    def _examine_single_page_evaluators(self, page):
        # get highlights
        highlights = page.find("section", class_="highlights")
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
    def evaluator(self):
        scouting_report = soup.find("section", class_="scouting-report")
        if not scouting_report:
            return None

        evaluations = scouting_report.find("header").find('a', class_='view-all-eval-link')
        if evaluations:
            url = evaluations['href']
            page = requests.get(url, headers = HEADERS)
            soup = BeautifulSoup(page.content, 'lxml')
            evaluators_list = self._examine_multiple_evaluators(soup)
            background, skills = BackgroundSkills(scouting_report).background_skills

        else:
            evaluators = soup.find('section', class_='scouting-report')
            evaluators_list = self._example_single_page_evaluators(evaluators)
            background, skills = BackgroundSkills(evaluators).background_skills

        return evaluators_list, background, skills