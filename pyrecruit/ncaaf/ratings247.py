from bs4 import BeautifulSoup
from .datamodels import Ratings

class Ratings247:
    def __init__(self, soup: BeautifulSoup, pos: str, state: str):
        self.soup = soup
        self.pos = pos
        self.state = state

    def _find_ratings_composite_helper(self, soup: BeautifulSoup, it: BeautifulSoup) -> dict:
        """Collect the composite ratings of the recruit (247Sports Composite)

        Args:
            soup (BeautifulSoup): webpage to be scraped
            it (BeautifulSoup): position on webpage

        Returns:
            dict: data that consists of the different composite scores
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

    def _find_ratings_normal_helper(self, soup: BeautifulSoup, it: BeautifulSoup) -> dict:
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