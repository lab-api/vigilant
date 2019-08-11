import datetime
import time
import sched
import os
from threading import Thread
import pandas as pd
from watchdog import Watcher, Listener

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
        self.watchers = {}
        self.listeners = {}
        self.filename = filename
        self.scheduler = sched.scheduler(time.time, time.sleep)

        self.data = pd.DataFrame()
        self.data.index.rename('Timestamp', inplace=True)

        self.callbacks = []
        self.last_time = None
        self.running = False

    def watch(self, experiment, name=None, threshold=(None, None), reaction=None):
        ''' Add a variable to be monitored actively (querying a method for new
            results with each measurement cycle).
            Args:
                experiment (callable): a function or other callable. Should take
                                       no arguments and return a numerical value.
                name (str): optional variable name. If None is passed, the default
                            experiment.__name__ string is used.
                threshold (tuple): lower and upper threshold. Pass None to either
                                   threshold to deactivate it.
                reaction (function): optional action to take when the variable
                                     exits defined thresholds.
        '''
        if name is None:
            name = experiment.__name__
        self.watchers[name] = Watcher(name, experiment,
                                      threshold=threshold,
                                      reaction=reaction)

    def listen(self, name, address, threshold=(None, None), reaction=None):
        ''' Add a variable to be monitored passively (initiated from the variable,
            not the monitor).
            Args:
                name (str): label with which to store the data
                address (str): address of data feed, e.g. '127.0.0.1:8000'
                threshold (tuple): lower and upper threshold. Pass None to either
                                   threshold to deactivate it.
                reaction (function): optional action to take when the variable
                                     exits defined thresholds.
        '''

        self.listeners[name] = Listener(name, address, 
                                        threshold=threshold,
                                        reaction=reaction)

    def add_extension(self, extension):
        ''' Add an extension by registering its update() method as a callback '''
        self.callbacks.append(extension.update)

    def check(self):
        ''' Check all attached watchers and optionally log the result, update
            the plot, and/or call the callback.
        '''
        new_data = pd.DataFrame()
        now = datetime.datetime.now().isoformat()

        ## check watchers
        for name in self.watchers:
            value, in_threshold = self.watchers[name].check()
            new_data.loc[now, name] = value

        ## check listeners
        for name, listener in self.listeners.items():
            while not listener.queue.empty():
                new_queue_data = listener.queue.get()
                new_data = new_data.append(new_queue_data, sort=False)

        # check listener results against thresholds
        for name, listener in self.listeners.items():
            if name in new_data:
                vals = new_data[name].dropna().values
                listener.check(vals)

        if len(new_data) == 0:
            return

        new_data.sort_index(inplace=True)
        self.data = self.data.append(new_data, sort=False)
        self.process(new_data)

        return new_data

    def process(self, data):
        ''' Logs data and sends it to extensions '''
        if self.filename is not None:
            self.log(data)

        for callback in self.callbacks:
            callback(data)

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
