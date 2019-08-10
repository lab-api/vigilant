import datetime
import time
import sched
import decorator
import pandas as pd
import numpy as np
from threading import Thread
import os
from watchdog import Watchdog

class Monitor():
    def __init__(self, filename = None, callback = None, visualize=True):
        ''' Args:
                filename (str): optional filename for logging
                callback (function): a function to call each time the watchdog states
                                     are checked. The Monitor passes a Pandas dataframe
                                     of the most recent measurement to this function.
                visualize (bool): whether to enable realtime plotting
        '''
        self.watchdogs = {}
        self.filename = filename
        self.callback = callback
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.data = pd.DataFrame()
        self.data.index.rename('Timestamp', inplace=True)

        self.visualizer = None
        if visualize:
            from watchdog import Visualizer
            self.visualizer = Visualizer(self.data)

        self.last_time = None
        self.thresholds = {}

    def watch(self, experiment, threshold=(None, None), name=None, reaction=None):
        if name is None:
            name = experiment.__name__
        self.thresholds[name] = threshold
        self.watchdogs[name] = Watchdog(experiment, threshold, name)
        if reaction is not None:
            self.watchdogs[name].react = reaction

        self.data[name] = np.nan
        if self.visualizer is not None:
            self.visualizer.add_trace(name)

    def check(self):
        now = datetime.datetime.now().isoformat()
        for w in self.watchdogs:
            value, tf = self.watchdogs[w].check()
            self.data.loc[now, w] = value
        new_data = self.data.loc[[now]]

        if self.filename is not None:
            self.log(new_data)

        if self.visualizer is not None:
            self.visualizer.update(new_data)

        if self.callback is not None:
            self.callback(new_data)

        return new_data

    def log(self, data):
        if not os.path.isfile(self.filename):
            data.to_csv(self.filename, header=True)
        else:
            data.to_csv(self.filename, mode='a', header=False)

    def start_triggered(self, trigger):
        self.on = 1
        while self.on:
            trigger()
            self.check()

    def start_periodic(self, period):
        self.on = 1
        if self.last_time is None:
            self.last_time = time.time()
        while self.on:
            self.scheduler.enterabs(self.last_time, 1, self.check)
            self.last_time += period
            self.scheduler.run()

    def start(self, period=None, trigger=None):
        if trigger is None and period is not None:
            thread = Thread(target=self.start_periodic, args=(period,))
        elif period is None and trigger is not None:
            thread = Thread(target=self.start_triggered, args=(trigger,))
        else:
            raise Exception('Pass either a period or a trigger to Monitor.start().')
        thread.start()

    def stop(self):
        self.on = 0
        self.last_time = None

    def plot(self):
        if self.visualizer is None:
            raise Exception('Monitor visualization is disabled unless visualize=True is passed.')
        self.visualizer.plot()
