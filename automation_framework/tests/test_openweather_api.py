import pytest
from automation_framework.utilities.api_helpers import ApiHelper
from automation_framework.utilities.db_helpers import DatabaseHelper


@pytest.fixture(scope="module")
def api():
    return ApiHelper()


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


@pytest.fixture(autouse=True, scope="class")
def drop_table():
    yield
    with DatabaseHelper() as db:
        db.drop_table()


class TestOpenweatherApi:
    #  Test Case: Verify `get_current_weather` with Celsius Metric and English Language
    def test_get_weather_data(self, api, city):
        response = api.get_current_weather_by_city_name(city=city)
        temperature, feels_like = api.get_temp_and_feels_like_from_resp(response)

        with DatabaseHelper() as db:
            db.insert_weather_data(city=city, temperature=temperature, feels_like=feels_like)
            db_temperature, db_feels_like = db.get_weather_data(city)[1:3]

        assert temperature == db_temperature, f"Temperature mismatch for {city}"
        assert feels_like == db_feels_like, f"Feels-like-temperature mismatch for {city}"

    #  Test Case: Utilize Weather Data for Multiple Cities via City ID Parameter
    def test_multiple_cities_by_id(self, api, cities_ids):
        for city_id in cities_ids:
            response = api.get_current_weather_by_city_id(city_id)
            temperature, feels_like = api.get_temp_and_feels_like_from_resp(response)
            city_name = api.get_city_name(response)
            with DatabaseHelper() as db:
                db.insert_weather_data(city=city_name, temperature=temperature, feels_like=feels_like)
                db_temperature, db_feels_like = db.get_weather_data(city_name)[1:3]
            assert temperature == db_temperature, f"Temperature mismatch for {city_name}"
            assert feels_like == db_feels_like, f"Feels-like-temperature mismatch for {city_name}"

    #  Create a new database column for the average temperature of each city
    def test_new_column(self, api, cities_ids):
        with DatabaseHelper() as db:
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
