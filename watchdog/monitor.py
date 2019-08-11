import datetime
import time
import sched
import os
from threading import Thread
import pandas as pd
import numpy as np
from watchdog import Watchdog

class Monitor():
    ''' Implements periodic or triggered monitoring of any functions passed to
        the Monitor.watch() method. Extensions can be added using the
        Monitor.add_extension() method, adding features like realtime plotting,
        ZeroMQ pub/sub feeds, and writing to an Influx database.
    '''
    def __init__(self, filename=None):
        ''' Args:
                filename (str): optional filename for logging
        '''
        self.watchdogs = {}
        self.filename = filename
        self.scheduler = sched.scheduler(time.time, time.sleep)

        self.data = pd.DataFrame()
        self.data.index.rename('Timestamp', inplace=True)

        self.callbacks = []
        self.last_time = None
        self.running = False

    def watch(self, experiment, threshold=(None, None), name=None, reaction=None):
        ''' Add a variable to be monitored.
            Args:
                experiment (callable): a function or other callable. Should take
                                       no arguments and return a numerical value.
                threshold (tuple): lower and upper threshold. Pass None to either
                                   threshold to deactivate it.
                name (str): optional variable name. If None is passed, the default
                            experiment.__name__ string is used.
                reaction (function): optional action to take when the variable
                                     exits defined thresholds.
        '''
        if name is None:
            name = experiment.__name__
        self.watchdogs[name] = Watchdog(experiment, threshold, name)
        if reaction is not None:
            self.watchdogs[name].react = reaction

        self.data[name] = np.nan

    def add_extension(self, extension):
        ''' Add an extension by registering its update() method as a callback '''
        self.callbacks.append(extension.update)

    def check(self):
        ''' Check all attached watchdogs and optionally log the result, update
            the plot, and/or call the callback.
        '''
        now = datetime.datetime.now().isoformat()
        for name in self.watchdogs:
            value, in_threshold = self.watchdogs[name].check()
            self.data.loc[now, name] = value
        new_data = self.data.loc[[now]]

        if self.filename is not None:
            self.log(new_data)

        for callback in self.callbacks:
            callback(new_data)

        return new_data

    def log(self, data):
        ''' Append the latest measurement to file. If the file does not exist,
            headers matching the columns in self.data are written first.
            Args:
                data (pandas.DataFrame): the most recent measurement
        '''
        if not os.path.isfile(self.filename):
            data.to_csv(self.filename, header=True)
        else:
            data.to_csv(self.filename, mode='a', header=False)

    def start_triggered(self, trigger):
        ''' Start acquisition in triggered mode.
            Args:
                trigger (function): a function which returns as soon as a trigger
                                    condition is satisfied
        '''
        self.running = True
        while self.running:
            trigger()
            self.check()

    def start_periodic(self, period):
        ''' Start acquisition in periodic mode. Uses Python's sched library to
            avoid timing drifts. Make sure that the passed period is longer than
            the time required to call self.check().

            Args:
                period (float): the repetition time in seconds
        '''
        self.running = True
        if self.last_time is None:
            self.last_time = time.time()
        while self.running:
            self.scheduler.enterabs(self.last_time, 1, self.check)
            self.last_time += period
            self.scheduler.run()

    def start(self, period=None, trigger=None):
        ''' Start acquisition in either periodic or triggered mode, depending on
            which argument is passed.
        '''
        if trigger is None and period is not None:
            thread = Thread(target=self.start_periodic, args=(period,))
        elif period is None and trigger is not None:
            thread = Thread(target=self.start_triggered, args=(trigger,))
        else:
            raise Exception('Pass either a period or a trigger to Monitor.start().')
        thread.start()

    def stop(self):
        ''' Stop acquisition. '''
        self.running = False
        self.last_time = None
