from bs4 import BeautifulSoup
from .datamodels import Connection

class Connections:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
    
    @property
    def connections(self) -> list[Connection]:
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