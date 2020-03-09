from influxdb import DataFrameClient
import pandas as pd

class InfluxClient:
    def __init__(self, database, measurement, address='localhost:8086', username='root', password='root'):
        ip = address.split(':')[0]
        port = int(address.split(':')[1])
        self.database = database
        self.measurement = measurement
        self.client = DataFrameClient(ip, port, username, password, self.database)

        if not self.database_exists(self.database):
            self.client.create_database(self.database)

    def database_exists(self, name):
        for db in self.client.get_list_database():
            if db['name'] == name:
                return True
        return False

    def update(self, data):
        data.index = pd.to_datetime(data.index)
        self.client.write_points(data, self.measurement, protocol='json')

    def read(self):
        return self.client.query(f'select * from {self.measurement}')[self.measurement]
