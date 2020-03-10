import pandas as pd
import requests

class InfluxClient:
    def __init__(self, database, measurement, addr='localhost', port=8086):
        self.address = f'http://{addr}:{port}'
        self.database = database
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
