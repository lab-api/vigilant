import datetime
from vigilant import config
from threading import Thread
from flask import Flask
import json
import numpy as np

class Monitor():
    def __init__(self):
        self.categories = {'default': {}}
        Thread(target=self.serve).start()

    def serve(self):
        ip = config['monitor']['address']
        port = config['monitor']['port']
        app =  Flask(__name__)
        self.last = {}

        @app.route('/')
        def sample():
            result = {}
            for category in self.categories:
                for name, item in self.categories[category].items():
                    result[name] = item['experiment']()
                    result[name+'/min'] = item['min']
                    result[name+'/max'] = item['max']
            self.last = result
            return json.dumps(result)

        @app.route('/last')
        def last_sample():
            return json.dumps(self.last)

        app.run(host=ip, port=port)

    def watch(self, experiment, name=None, category='default', bounds=[-np.inf, np.inf]):
        ''' Add a variable to be monitored actively (querying a method for new
            results with each measurement cycle).
            Args:
                experiment (callable): a function or other callable. Should take
                                       no arguments and return a numerical value.
                name (str): optional variable name. If None is passed, the default
                            experiment.__name__ string is used.
        '''
        if name is None:
            name = experiment.__name__
        if category not in self.categories:
            self.categories[category] = {}
        field = category + '/' + name
        self.categories[category][field] = {'experiment': experiment, 'min': bounds[0], 'max': bounds[1]}
