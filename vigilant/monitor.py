import datetime
import time
import sched
import os
from threading import Thread
import pandas as pd
from vigilant import config, Watcher, Listener
from vigilant.extensions import InfluxClient, FileLogger, Generator

class Monitor():
    ''' Implements periodic or triggered monitoring of any functions passed to
        the Monitor.watch() method. Extensions can be added using the
        Monitor.add_extension() method, adding features like realtime plotting,
        ZeroMQ pub/sub feeds, and writing to an Influx database.
    '''
    def __init__(self, filename=None, period=None, trigger=None, measurement=None, dashboard=None):
        '''
        Args:
            period (float): sampling period.
            trigger (function): a function which blocks until sampling time, then
                                returns. Either a trigger or a period should be
                                defined, but not both.
            filename (str): optional filename for logging to CSV
            measurement (str): optional measurement name for logging to InfluxDB

        Config options (entries in config.yml):
            max points (int): number of points to store in memory (FIFO basis).
            resampling interval (str): interval with which to bin incoming data.
                                       Value should be formatted as a pandas
                                       offset alias, e.g. '1s' for resampling to
                                       one second intervals. Leave blank to disable
                                       resampling.
        '''
        self.period = period
        self.trigger = trigger

        self.categories = {'default': {}}
        self.callbacks = {}
        self.alerts = []

        self.data = pd.DataFrame()
        self.data.index.rename('Timestamp', inplace=True)

        self.running = False
        self.in_threshold = True

        self.measurement = measurement
        if measurement is not None:
            self.add_extension(InfluxClient(measurement='test'))

        if filename is not None:
            self.add_extension(FileLogger(filename=filename))

        self.dashboard = dashboard
        if self.dashboard is not None:
            self.generator = Generator(self)

    def watch(self, experiment, name=None, category='default', threshold=(None, None), reaction=None):
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
        if category not in self.categories:
            self.categories[category] = {}
        name = category + '/' + name
        self.categories[category][name] = Watcher(name, experiment,
                                                 threshold=threshold,
                                                 reaction=reaction)
        if self.dashboard is not None:
            self.generator.generate()
            self.generator.post()


    def listen(self, name, address, category='default', threshold=(None, None), reaction=None):
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
        if category not in self.categories:
            self.categories[category] = {}
        name = category + '/' + name
        self.categories[category][name] = Listener(name, address,
                                        threshold=threshold,
                                        reaction=reaction)
        if self.dashboard is not None:
            self.generator.generate()
            self.generator.post()

    def add_extension(self, extension):
        ''' Add an extension by registering its update() method as a callback '''
        self.callbacks[extension.__class__] = extension.update

    def add_alert(self, alert):
        ''' Add an alert by registering its send() method as a callback '''
        self.alerts.append(alert.send)

    def check(self):
        ''' Check all attached watchers and optionally log the result, update
            the plot, and/or call the callback.

            If a value is out of threshold, enter the Alert state.
        '''
        new_data = pd.DataFrame()
        now = datetime.datetime.utcnow().isoformat()

        all_in_threshold = True
        for category in self.categories:
            for name, observer in self.categories[category].items():
                observation = observer.measure()
                if len(observation) != 0:
                    new_data = new_data.append(observation, sort=False)
                    all_in_threshold &= observer.compare(observation)

        if len(new_data) == 0:
            return

        ## bin data into new interval and append to dataset
        if config['monitor']['resampling interval'] is not None:
            new_data = self.resample(new_data, freq=config['monitor']['resampling interval'])
        new_data.sort_index(inplace=True)
        self.data = self.data.append(new_data, sort=False)

        ## trim to chosen maximum length of data in memory
        overflow = len(self.data) - config['monitor']['max points']
        if overflow > 0:
            self.data.drop(self.data.head(overflow).index, inplace=True)

        ## raise alerts if an unlock is detected
        if self.in_threshold and not all_in_threshold:
            self.alert()
        self.in_threshold = all_in_threshold

        for callback in self.callbacks.values():
            callback(new_data)

        return new_data

    @staticmethod
    def resample(data, freq='1s'):
        ''' Bin observations into the passed frequency '''
        data.index = pd.DatetimeIndex(data.index)   # convert to datetime index for resampling
        data = data.reset_index().groupby(pd.Grouper(key='index', freq=freq)).mean()  # resample
        data.index = data.index.strftime('%Y-%m-%dT%H:%M:%S.%f')  # convert back to string index

        return data

    def alert(self):
        out_of_threshold = [obs.name for obs in self.observers.values() if not obs.in_threshold]
        msg = f'Observers {out_of_threshold} are out of threshold!'
        for alert in self.alerts:
            alert(msg)

    def start(self):
        ''' Start acquisition in either periodic or triggered mode, depending on
            which argument is passed when instantiating the Monitor.
        '''
        if self.trigger is None and self.period is not None:
            thread = Thread(target=self.start_periodic, args=(self.period,))
        elif self.period is None and self.trigger is not None:
            thread = Thread(target=self.start_triggered, args=(self.trigger,))
        else:
            raise Exception('Pass either a period or a trigger to Monitor.start().')
        thread.start()

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
        scheduler = sched.scheduler(time.time, time.sleep)

        last_time = time.time()
        while self.running:
            scheduler.enterabs(last_time, 1, self.check)
            last_time += period
            scheduler.run()

    def stop(self):
        ''' Stop acquisition. '''
        self.running = False
