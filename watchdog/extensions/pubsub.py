import zmq
import json
import pandas as pd

class Publisher:
    def __init__(self, address='127.0.0.1:1105'):
        self.socket = zmq.Context().socket(zmq.PUB)
        self.socket.bind(f"tcp://{address}")

    def update(self, data):
        if isinstance(data, pd.DataFrame):
            self.socket.send_string(json.dumps(data.to_json()))
        else:
            self.socket.send_string(str(data))

class Subscriber:
    def __init__(self, address='127.0.0.1:1105'):
        self.socket = zmq.Context().socket(zmq.SUB)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')
        self.socket.connect(f"tcp://{address}")

    def receive(self):
        ''' Receives either a float or json-formatted dataframe and processes and
            returns it by context.
        '''
        msg = self.socket.recv_string()
        try:
            msg = float(msg)
        except Exception:
            msg = pd.read_json(json.loads(msg))
        return msg
