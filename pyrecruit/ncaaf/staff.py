import requests
from .datamodels import StaffMember, TopCommit, CoachHistory
from bs4 import BeautifulSoup
from typing import Union, List, Dict

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