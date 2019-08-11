import zmq
import json
import pandas as pd

class Publisher:
    def __init__(self, address='127.0.0.1', port=1105):
        self.socket = zmq.Context().socket(zmq.PUB)
        self.socket.bind(f"tcp://{address}:{port}")

    def update(self, data):
        if isinstance(data, pd.DataFrame):
            self.socket.send_string(json.dumps(dataframe.to_json()))
        else:
            self.socket.send_string(str(data))

class Subscriber:
    def __init__(self, address='127.0.0.1', port=1105):
        self.socket = zmq.Context().socket(zmq.SUB)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')
        self.socket.connect(f"tcp://{address}:{port}")

    def receive(self):
        ''' Receives either a float or json-formatted dataframe and processes and
            returns it by context.
        '''
        msg = self.socket.recv_string()
        try:
            return float(msg)
        except TypeError:
            return pd.read_json(msg)
