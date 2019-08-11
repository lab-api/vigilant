from influxdb import DataFrameClient
import pandas as pd

class InfluxClient:
    def __init__(self, address='localhost', port=8086, database='demo'):
        self.client = DataFrameClient(address, port, 'root', 'root', database)
        self.database = database

        if not self.database_exists(database):
            self.client.create_database(database)

    def database_exists(self, name):
        for db in self.client.get_list_database():
            if db['name'] == name:
                return True
        return False

    def update(self, data):
        data.index = pd.to_datetime(data.index)
        self.client.write_points(data, self.database, protocol='json')

    def read(self):
        return self.client.query(f'select * from {self.database}')[self.database]
