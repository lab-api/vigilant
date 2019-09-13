import json
import requests
import time

class Dweet():
    ''' A class for remote communication through the Dweet protocol. Pass in a unique guid at initialization. '''
    def __init__(self, guid):
        self.guid = guid
        self.url = f'https://dweet.io/dweet/for/{guid}'
    def receive(self):
        try:
            r = json.loads(requests.get(self.url).text)

            j = r['with'][0]['content']
            return j
        except KeyError:
            if r['because'] == 'Rate limit exceeded, try again in 1 second(s).':
                time.sleep(1.01)
                return self.receive()
            else:
                print(r)

    def send(self, dictionary):
        headers = {'Content-type': 'application/json'}
        requests.post(self.url, data=json.dumps(dictionary), headers=headers)

    def update(self, data):
        data_dict = data.T.to_dict()
        timestamp = list(data_dict.keys())[0]
        data_dict[timestamp]['Timestamp'] = timestamp
        self.send(data_dict[timestamp])
