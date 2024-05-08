import requests

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
API_KEY = "f88d54cd8eddb5d1f23ff82a80b95fec"


class ApiHelper:
    def __init__(self):
        self.url = BASE_URL
        self.key = API_KEY
        self.UNITS = "metric"
        self.LANG = "en"

    @staticmethod
    def get_temp_and_feels_like_from_resp(response):
        resp = response.json()["main"]
        return resp["temp"], resp['feels_like']

    @staticmethod
    def get_city_name(response):
        return response.json()['name']

    @staticmethod
    def calc_city_average_temp(response):
        resp = response.json()["main"]
        # I'm not sure that this is correct method. maybe I should to take some info via api?
        return (resp["temp_min"] + resp["temp_max"]) / 2

    def compose_url(self, **params):
        return f"{self.url}?{'&'.join(f'{key}={value}' for key, value in params.items())}&appid={self.key}"

    def get_current_weather_by_city_name(self, city):
        url = self.compose_url(units=self.UNITS, lang=self.LANG, q=city)
        response = requests.get(url)
        assert response.status_code is 200, "Something goes wrong with response from openweather api"
        return response

    def get_current_weather_by_city_id(self, city_id):
        url = self.compose_url(units=self.UNITS, lang=self.LANG, id=city_id)
        response = requests.get(url)
        assert response.status_code is 200, "Something goes wrong with response from openweather api"
        return response

