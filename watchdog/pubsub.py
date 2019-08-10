import zmq
import json
import pandas as pd

class Publisher:
    def __init__(self, address='127.0.0.1', port=1105):
        self.socket = zmq.Context().socket(zmq.PUB)
        self.socket.bind(f"tcp://{address}:{port}")

    def send(self, dataframe):
        self.socket.send_string(json.dumps(dataframe.to_json()))

class Subscriber:
    def __init__(self, addr='127.0.0.1', port=1105):
        self.socket = zmq.Context().socket(zmq.SUB)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')
        self.socket.connect(f"tcp://{addr}:{port}")

    def get(self):
        return pd.read_json(json.loads(self.socket.recv_string()))
