import sqlite3


class DatabaseHelper:
    OWM_TABLE = "openweather_api"
    TND_TABLE = "timeanddate_com"

    def __init__(self, db_name="data.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def create_tables(self):
        # Create tables if they don't exist
        with self.conn:
            self.conn.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.OWM_TABLE} (
                city TEXT PRIMARY KEY,
                temperature REAL,
                feels_like REAL);''')
        # with self.conn:
            self.conn.execute(f'''    
                CREATE TABLE IF NOT EXISTS {self.TND_TABLE} (
                city TEXT PRIMARY KEY,
                weather REAL);''')

    def delete_from_table(self, city):
        self.cursor.execute(f"DELETE FROM {self.OWM_TABLE} WHERE city = '{city}'")
        self.conn.commit()

    def drop_table(self, table):
        try:
            self.cursor.execute(f"DROP TABLE IF EXISTS {table};")
            self.conn.commit()
            print(f"Table '{table}' dropped successfully")
        except sqlite3.Error as error:
            print("Error during table drop: ", error)

    def append_new_column(self, column_name, data_type="REAL"):
        try:
            self.cursor.execute(f"PRAGMA table_info({self.OWM_TABLE})")
            columns = self.cursor.fetchall()
            column_exists = any(column[1] == column_name for column in columns)
            if column_exists:
                return
            self.cursor.execute(f"ALTER TABLE {self.OWM_TABLE} ADD COLUMN {column_name} {data_type};")
            self.conn.commit()
        except sqlite3.Error as error:
            print("Error during new column addition", error)

    #  city, temperature, feels_like, average_temp
    def insert_weather_data(self, **columns):
        query = (f"INSERT OR IGNORE INTO {self.OWM_TABLE} ({", ".join(key for key in columns.keys())}) "
                 f"VALUES ({', '.join("'" + str(val) + "'" if isinstance(val, str) else str(val) for val in columns.values())});")
        self.cursor.execute(query)
        self.conn.commit()

    #  city, weather
    def insert_into_timeanddate(self, **columns):
        query = (f"INSERT OR IGNORE INTO {self.TND_TABLE} ({", ".join(key for key in columns.keys())}) "
                 f"VALUES ({', '.join("'" + str(val) + "'" if isinstance(val, str) else str(val) for val in columns.values())});")
        self.cursor.execute(query)
        self.conn.commit()

    def insert_many_rows(self, table_name, rows):
        query = f"INSERT OR IGNORE INTO {table_name} VALUES ({', '.join(['?'] * len(rows[0]))})"
        self.cursor.executemany(query, rows)
        self.conn.commit()

    def get_weather_data(self, city, *columns):
        self.cursor.execute(f"SELECT {', '.join(columns) if columns else '*'} FROM {self.OWM_TABLE} WHERE city = '{city}';")
        result = self.cursor.fetchall()[0]
        return result

    def max_avg_temp(self):
        self.cursor.execute(f"SELECT city, average_temp FROM {self.OWM_TABLE} WHERE "
                            f"average_temp = (SELECT MAX(average_temp) FROM {self.OWM_TABLE});")
        result = self.cursor.fetchall()[0]
        return result

    def get_all_cities(self):
        self.cursor.execute(f"SELECT city FROM {self.OWM_TABLE};")
        result = [city[0] for city in self.cursor.fetchall()]
        return result

    def compare_two_sources(self):
        self.cursor.execute(f"""
        SELECT 
        CASE
            WHEN ABS(wd.temperature - tw.weather) > 10 THEN '5: 10+ deg'
            WHEN ABS(wd.temperature - tw.weather) BETWEEN 5 AND 10 THEN '4: 5-10 deg'
            WHEN ABS(wd.temperature - tw.weather) BETWEEN 2 AND 5 THEN '3: 2-5 deg'
            WHEN ABS(wd.temperature - tw.weather) BETWEEN 1 AND 2 THEN '2: 1-2 deg'
            WHEN ABS(wd.temperature - tw.weather) BETWEEN 0 AND 1 THEN '1: 0-1 deg'
        END AS diff_group,
        COUNT(*) AS count_diff
        FROM 
            {self.OWM_TABLE} wd
        JOIN 
            {self.TND_TABLE} tw ON wd.city = tw.city
        GROUP BY 
            diff_group;
                """)
        return self.cursor.fetchall()

    def old_max_diff(self, min_or_max):
        self.cursor.execute(f"""
            SELECT
                wd.city,
                {min_or_max}(wd.temperature - tw.weather) AS difference
            FROM
                {self.OWM_TABLE} wd
            JOIN
                {self.TND_TABLE} tw ON wd.city = tw.city
            GROUP BY
                wd.city;
                                """)
        return self.cursor.fetchall()

    def max_diff(self, asc=False):
        query = (f"SELECT wd.city, (wd.temperature - tw.weather) AS difference "
                 f"FROM {self.OWM_TABLE} wd JOIN {self.TND_TABLE} tw ON wd.city = tw.city "
                 f"ORDER BY difference {'ASC' if asc else 'DESC'} LIMIT 1;")
        self.cursor.execute(query)
        result = self.cursor.fetchall()[0]
        return result
