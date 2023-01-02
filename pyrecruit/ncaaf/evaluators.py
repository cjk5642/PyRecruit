from bs4 import BeautifulSoup
from typing import List, Union, Tuple
from .datamodels import Evaluator, Skills
from .background_skills import BackgroundSkills
from .utils import HEADERS
import requests

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
        evaluators_all_list = []
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
                evaluators_all_list.append(evaluators_dataclass)
        return evaluators_all_list

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
            id = name,
            name = name, 
            region = region, 
            projection = projection, 
            comparison=comparison_name,
            comparison_team=comparison_team, 
            evaluation_date=eval_date, 
            evaluation=evaluation
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
            page = requests.get(url, headers = HEADERS, timeout=10)
            soup = BeautifulSoup(page.content, 'lxml')
            evaluators_list = self._examine_multiple_evaluators(soup)
            background, skills = BackgroundSkills(scouting_report).background_skills

        else:
            evaluators = self.soup.find('section', class_='scouting-report')
            evaluators_list = self._examine_single_page_evaluators(evaluators)
            background, skills = BackgroundSkills(evaluators).background_skills

        return evaluators_list, background, skills
