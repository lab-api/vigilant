import requests

class Slack():
    def __init__(self, webhook):
        ''' A class for relaying messages between the code and Slack.
            Pass in a channel's webhook at initialization.
        '''
        self.webhook = webhook

    def send(self, message):
        ''' Sends a specified message to the webhook '''
        payload={"text": "%s"%message}
        return requests.post(self.webhook, json=payload).status_code
