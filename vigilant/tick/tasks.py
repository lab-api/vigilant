import textwrap, requests, json
from vigilant import config

def submit_task(task_id, script):
    ''' Submits and enable a task to Kapacitor. '''
    database = config['influx']['database']
    rp = 'autogen'
    task = {
        "id" : task_id,
        "type" : "stream",
        "dbrps": [{"db": database, "rp" : rp}],
        "script": script,
        "status": "enabled"
    }
    requests.delete(f'http://localhost:9092/kapacitor/v1/tasks/{task_id}')
    r = requests.post('http://localhost:9092/kapacitor/v1/tasks', data=json.dumps(task))

    return r

def process_alerts(fields, rp='autogen'):
    ''' Compares incoming data against min and max values. For each field, saves a boolean result, which is True if
        out of threshold, to the "alerts" measurement in the InfluxDB database. Also saves the result of OR comparison
        of all fields to the "ALL" field of the "alerts" measurement.
    '''
    database = config['influx']['database']
    measurement = config['influx']['measurement']

    field_eval = ', '.join([f'lambda: "{field}" < "{field}/min" OR "{field}" > "{field}/max"' for field in fields])
    as_fields = ', '.join([f"'{field}'" for field in fields])
    isNotOK = [f'"{field}"==TRUE' for field in fields]
    crit = 'lambda: ' + ' OR '.join(isNotOK)
    script = textwrap.dedent(f"""
        stream
            |from()
               .database('{database}')
               .measurement('{measurement}')
            |eval({field_eval})
                .as({as_fields})
            |eval({crit})
                .as('ALL')
                .keep('ALL', {as_fields})
            |influxDBOut()
                .database('{database}')
                .measurement('alerts')
    """)
    return script

    return r
