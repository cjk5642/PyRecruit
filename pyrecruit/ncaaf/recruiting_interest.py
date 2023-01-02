from bs4 import BeautifulSoup
from .datamodels import CollegeInterest
from .staff import Staff
import requests
from .utils import HEADERS

class CollegeRecruitingInterest:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
    
    def _examine_more_colleges(self, url: str) -> list[CollegeInterest]:
        """Method to parse over page if there is long list of colleges. Congrats!

        Args:
            url (str): the url to the webpage that contains list of colleges

        Returns:
            list[CollegeInterest]: Data of all colleges that actively recruited recruit
        """
        school_list = []
        page = requests.get(url, headers=HEADERS, timeout=10)
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
    def college_interest(self) -> tuple[None, list[CollegeInterest]]:
        """Method to output the data of college

        Returns:
            tuple[None, list[CollegeInterest]]: Data of all colleges interested in the recruit
        """
        view_all_colleges = self.soup.find('a', class_ = "college-comp__view-all")
        school_list = []
        if view_all_colleges:
            school_list = self._examine_more_colleges(view_all_colleges['href'])
        else:
            school_list = None
        return school_list