import pandas as pd
import requests
from vigilant import config

class InfluxClient:
    def __init__(self, measurement, database=None):
        self.address = f"http://{config['influx']['address']}:{config['influx']['port']}"
        self.database = database
        if database is None:
            self.database = config['influx']['database']
        self.measurement = measurement

        if not self.database in self.list_databases():
            self.create_database(self.database)

    def create_database(self, name):
        params = {'q': f'CREATE DATABASE "{name}"'}
        requests.post(f'{self.address}/query', params=params)

    def list_databases(self):
        params = {'q': "SHOW DATABASES"}
        r = requests.get(f'{self.address}/query', params=params).json()
        dbs = r['results'][0]['series'][0]['values']
        return [x[0] for x in dbs]

    def query(self, q):
        params = {'q': q}
        r = requests.get(f'{self.address}/query', params=params).json()
        return r

    def post(self, q, data={}):
        params = {'q': q}
        r = requests.post(f'{self.address}/query', params=params, data=data).json()
        return r

    def update(self, data):
        ''' Writes a set of points to the database '''
        data.index = pd.to_datetime(data.index)

        for i in range(len(data)):
            payload = f'{self.measurement} '
            field_values = []

            timestamp = int(data.index[i].timestamp())
            for column in data.columns:
                field_values.append(f'{column}={data.iloc[i][column]}')

            payload += ','.join(field_values)
            payload += f' {timestamp}'
            requests.post(f"{self.address}/write?db={self.database}&precision=s",
                          data=payload.encode('utf-8'))

    def read(self):
        params = {'q': f'select * from {self.database}..{self.measurement}'}
        r = requests.get(f'{self.address}/query', params=params).json()
        r = r['results'][0]['series'][0]

        return pd.DataFrame(r['values'], columns=r['columns']).set_index('time')
