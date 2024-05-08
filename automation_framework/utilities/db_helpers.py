import sqlite3

class DatabaseHelper:
    TABLE_NAME = "weather_data"

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
            self.conn.execute(f'''CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                city TEXT PRIMARY KEY,
                temperature REAL,
                feels_like REAL
            )''')

    def delete_from_table(self, city):
        self.cursor.execute(f"DELETE FROM {self.TABLE_NAME} WHERE city = '{city}'")
        self.conn.commit()

    def drop_table(self):
        try:
            self.cursor.execute(f"DROP TABLE IF EXISTS {self.TABLE_NAME};")
            self.conn.commit()
            print(f"Table '{self.TABLE_NAME}' dropped successfully")
        except sqlite3.Error as error:
            print("Error during table drop: ", error)

    def append_new_column(self, column_name, data_type="REAL"):
        try:
            self.cursor.execute(f"PRAGMA table_info({self.TABLE_NAME})")
            columns = self.cursor.fetchall()
            column_exists = any(column[1] == column_name for column in columns)
            if column_exists:
                return
            self.cursor.execute(f"ALTER TABLE {self.TABLE_NAME} ADD COLUMN {column_name} {data_type};")
            self.conn.commit()
        except sqlite3.Error as error:
            print("Error during new column addition", error)

    #  city, temperature, feels_like, average_temp
    def insert_weather_data(self, **columns):
        query = (f"INSERT OR IGNORE INTO {self.TABLE_NAME} ({", ".join(key for key in columns.keys())}) "
                 f"VALUES ({', '.join("'" + str(val) + "'" if isinstance(val, str) else str(val) for val in columns.values())});")
        self.cursor.execute(query)
        self.conn.commit()

    def get_weather_data(self, city, *columns):
        self.cursor.execute(f"SELECT {', '.join(columns) if columns else '*'} FROM {self.TABLE_NAME} WHERE city = '{city}';")
        result = self.cursor.fetchall()[0]
        return result

    def max_avg_temp(self):
        self.cursor.execute(f"SELECT city, average_temp FROM {self.TABLE_NAME} WHERE "
                            f"average_temp = (SELECT MAX(average_temp) FROM {self.TABLE_NAME});")
        result = self.cursor.fetchall()[0]
        return result

    def get_all_cities(self):
        self.cursor.execute(f"SELECT city FROM {self.TABLE_NAME};")
        result = [city[0] for city in self.cursor.fetchall()]
        return result
