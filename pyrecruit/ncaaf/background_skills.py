from bs4 import BeautifulSoup
from .datamodels import Skills

class BackgroundSkills:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup

    def _examine_background(self, page: BeautifulSoup) -> str:
        """Collect background info on the recruit other. Like their biography

        Args:
            page (BeautifulSoup): webpage to be scraped

        Returns:
            str: Biography text of the recruit
        """
        background = page.find("section", class_="athletic-background")
        if not background:
            return None

        # extract biography text
        background = background.find("div", class_='body')
        background_text = " ".join([string.strip() for string in background.strings]).replace("\r", '').strip()
        return background_text

    
    def _examine_skills(self, page: BeautifulSoup) -> Skills:
        """Method to find the skills of the player if listed

        Args:
            page (BeautifulSoup): webpage to be scraped

        Returns:
            Skills: Skills Dataclass that consist of the recruits skills
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
    def background_skills(self) -> tuple[str, Skills]:
        """Method to output the background and skills

        Returns:
            tuple[str, Skills]: The background and skills of the player
        """
        background_skills = self.soup.find("div", class_="background-and-skills")
        background = self._examine_background(background_skills)
        skills = self._examine_skills(background_skills)
        return background, skills
