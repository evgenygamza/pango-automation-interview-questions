import requests
from bs4 import BeautifulSoup

TND_URL = "https://www.timeanddate.com/weather/"


class TndParser:
    TND_URL = "https://www.timeanddate.com/weather/"

    def __init__(self):
        self.url = self.TND_URL

    @staticmethod
    def parse_cities():
        # I remember that a Selenium script was expected here, but this way is much faster
        html_content = requests.get(TND_URL).text
        soup = BeautifulSoup(html_content, 'lxml')
        weather_table = soup.find("table")
        city_temperatures = {}

        for row in weather_table.find_all("tr"):
            cells = row.find_all("td")
            if cells:
                try:
                    city = cells[0].text.strip()
                    city2 = cells[4].text.strip()
                    temperature = int(cells[3].text.strip().split("\xa0")[0])
                    temperature2 = int(
                        cells[7].text.strip().split("\xa0")[0])  # Extract temperature and convert to integer
                    city_temperatures[city[:-2] if city[-1] == "*" else city] = temperature
                    city_temperatures[city2[:-2] if city2[-1] == "*" else city2] = temperature2
                except:
                    pass
        return city_temperatures
