import json
import datetime
import time
import logging as log
log.basicConfig(level=log.INFO)
import sched
import decorator
import pandas as pd
from threading import Thread
from IPython.display import display
from watchdog import Visualizer

@decorator.decorator
def thread(func, *args, **kwargs):
    new_thread = Thread(target=func, args=args, kwargs=kwargs)
    new_thread.start()

class Monitor():
    def __init__(self, watchdogs, filename = None, callback = None, visualize=False):
        ''' Args:
                watchdogs (dict): a dictionary of watchdogs labeled by their names
                filename (str): optional filename for logging
                callback (function): a function to call each time the watchdog states
                                     are checked. The Monitor passes a Pandas dataframe
                                     of the most recent measurement to this function.
        '''
        self.watchdogs = watchdogs
        self.filename = filename
        self.callback = callback
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.trigger = None
        self.data = pd.DataFrame(columns = watchdogs.keys())
        self.data.index.rename('Timestamp', inplace=True)

        self.visualize = visualize
        if visualize:
            self.visualizer = Visualizer(self.data)

    def add(self, key, watchdog):
        if key in self.watchdogs:
            raise IndexError(f'A Watchdog named {key} already exists!')
        self.watchdogs[key] = watchdog


    def check(self):
        now = datetime.datetime.now().isoformat()
        state = {'time': now,
                 'values': {},
                 'states': {}}
        for w in self.watchdogs:
            value, tf = self.watchdogs[w].check()
            state['values'][w] = value
            state['states'][w] = int(tf)

            self.data.loc[now, w] = value

        if self.filename is not None:
            self.log(state, self.filename)

        if self.visualize:
            self.visualizer.update(self.data.loc[now])

        if self.callback is not None:
            self.callback(self.data.loc[now])

        return state

    def log(self, state, filename):
        ''' Append a timestamped state dict to a file. '''
        with open(filename, 'a') as file:
            file.write(json.dumps(state)+'\n')

    def wait_trigger(self, period):
        time.sleep(period)

    @thread
    def start_triggered(self, trigger=None):
        if trigger is None:
            trigger = self.trigger
        self.on = 1

        if trigger is None:
            log.warn('Attach or pass a trigger!')
            return

        while self.on:
            trigger()
            self.check()

    @thread
    def start_periodic(self, period):
        self.on = 1
        if not hasattr(self, 'last_time'):
            self.last_time = time.time()
        while self.on:
            self.scheduler.enterabs(self.last_time, 1, self.check)
            self.last_time += period
            self.scheduler.run()

    def stop(self):
        self.on = 0

    def plot(self):
        if not self.visualize:
            raise Exception('Monitor visualization is disabled unless visualize=True is passed.')
        self.visualizer.plot()
