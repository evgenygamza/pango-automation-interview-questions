import pytest
import configparser
from automation_framework.utilities.api_helpers import ApiHelper
from automation_framework.utilities.db_helpers import DatabaseHelper
from automation_framework.utilities.timeanddate_com import TndParser


@pytest.fixture
def use_conf():
    return False


@pytest.fixture()
def api(use_conf):
    api = ApiHelper()
    if use_conf:
        config = configparser.ConfigParser()
        config.read('../config/config.ini')
        api.url = config['API']['API_URL']
        api.key = config['API']['API_KEY']
    return api


@pytest.fixture
def db(use_conf):
    with DatabaseHelper() as db:
        if use_conf:
            config = configparser.ConfigParser()
            config.read('../config/config.ini')
            db.url = config['DB']['DB_NAME']
        yield db


@pytest.fixture
def cities_ids():
    yield [611717, 615532, 7667581]
    with DatabaseHelper() as db:
        [db.delete_from_table(city_name) for city_name in
         ['Tbilisi', 'Batumi', 'Telavi']]


@pytest.fixture
def city():
    city_name = "Tokyo"
    yield city_name
    with DatabaseHelper() as db:
        db.delete_from_table(city_name)


@pytest.fixture()
def data_from_timeanddate(db, api):
    tnd_cities = TndParser.parse_cities()
    tnd_data = []
    owm_data = []
    for tnd_city in tnd_cities:
        try:
            tnd_weather = tnd_cities[tnd_city]
            tnd_data.append((tnd_city, tnd_weather))

            response = api.get_current_weather_by_city_name(city=tnd_city)
            if response.status_code is 200:
                owm_row = api.get_temp_and_feels_like_from_resp(response)
                owm_data.append((tnd_city, *owm_row))
        except:
            pass
    db.insert_many_rows(db.TND_TABLE, tnd_data)
    db.insert_many_rows(db.OWM_TABLE, owm_data)
    return


@pytest.fixture(autouse=True, scope="class")
def drop_table():
    yield
    with DatabaseHelper() as db:
        db.drop_table(db.TND_TABLE)
        db.drop_table(db.OWM_TABLE)


class TestOpenweatherApi:

    #  Test Case: Verify `get_current_weather` with Celsius Metric and English Language
    def test_get_weather_data(self, api, db, city):
        response = api.get_current_weather_by_city_name(city=city)
        temperature, feels_like = api.get_temp_and_feels_like_from_resp(response)
        name = api.get_city_name(response)

        db.insert_weather_data(city=city, temperature=temperature, feels_like=feels_like)
        db_temperature, db_feels_like = db.get_weather_data(city)[1:3]

        assert response.status_code is 200
        assert name == city, f"Something wrong with city name"
        assert temperature < 200, f"Units are not standard"
        assert temperature == db_temperature, f"Temperature mismatch for {city}"
        assert feels_like == db_feels_like, f"Feels-like-temperature mismatch for {city}"

    #  Test Case: Utilize Weather Data for Multiple Cities via City ID Parameter
    def test_multiple_cities_by_id(self, api, db, cities_ids):
        for city_id in cities_ids:
            response = api.get_current_weather_by_city_id(city_id)
            temperature, feels_like = api.get_temp_and_feels_like_from_resp(response)
            city_name = api.get_city_name(response)
            db.insert_weather_data(city=city_name, temperature=temperature, feels_like=feels_like)
            db_temperature, db_feels_like = db.get_weather_data(city_name)[1:3]
            assert temperature == db_temperature, f"Temperature mismatch for {city_name}"
            assert feels_like == db_feels_like, f"Feels-like-temperature mismatch for {city_name}"

    #  Create a new database column for the average temperature of each city
    def test_new_column(self, api, db, cities_ids):
        db.append_new_column("average_temp")
        avg_temps = []
        for city_id in cities_ids:
            response = api.get_current_weather_by_city_id(city_id)
            city_name = api.get_city_name(response)
            temperature, feels_like = api.get_temp_and_feels_like_from_resp(response)
            avg_temp = api.calc_city_average_temp(response)
            avg_temps.append(avg_temp)
            db.insert_weather_data(city=city_name, temperature=temperature, feels_like=feels_like,
                                   average_temp=avg_temp)

        max_avg_temp = max(avg_temps)
        max_avg_temp_db = db.max_avg_temp()
        assert max_avg_temp == max_avg_temp_db[1]
        print(" The warmest city is:", max_avg_temp_db[0])
        cities = db.get_all_cities()
        assert len(cities) == 3, ""

    @pytest.mark.parametrize("use_conf", [True, False])
    #  3 Dynamic API Key and Base URL Configuration
    def test_with_both_apis(self, api, use_conf):
        assert isinstance(api, ApiHelper)

    @pytest.mark.parametrize("use_conf", [True, False])
    def test_custom_db_config(self, db, use_conf):
        assert isinstance(db, DatabaseHelper)

    @pytest.mark.skip(reason="Too slow")
    #  3 Bonus Question: City Temperature Discrepancy Analysis
    def test_weather_reports_analysis(self, data_from_timeanddate, api, db):
        result = db.compare_two_sources()
        max = db.max_diff()
        min = db.max_diff(asc=True)

        print("\n")
        print("The temperature discrepancy analysis")
        for l in result:
            print(l[0][3:], l[1], "cities")
        print("\n")
        print("Max in OpenWeatherMap:", *max, "degrees more than in TimeAndDate:")
        print("Max in TimeAndDate:", min[0], abs(min[1]), "degrees more than in OpenWeatherMap")
