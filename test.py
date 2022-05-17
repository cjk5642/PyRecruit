import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
}
page = requests.get("https://247sports.com/Player/Travis-Hunter-46084728/", headers = HEADERS)
soup = BeautifulSoup(page.content, 'html.parser')
details = soup.find("ul", class_ = "details").find_all("li")
for d in details:
    spans = d.find_all("span")
    print(spans[1].find('a').text)
    break
