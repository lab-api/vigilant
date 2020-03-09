''' This modules implements the Watcher and Listener classes for reactive monitoring. '''
from multiprocessing import Process, SimpleQueue
import datetime
import pandas as pd
import numpy as np
from vigilant.extensions import Subscriber

class Observer:
    def __init__(self, name, threshold, reaction):
        self.name = name
        self.threshold = threshold
        self.react = reaction
        self._in_threshold = True

    @property
    def threshold(self):
        return self._threshold

    @threshold.setter
    def threshold(self, t):
        if t[0] is not None and t[1] is not None:
            if t[0] >= t[1]:
                raise ValueError('Lower bound must be less than upper bound.')
        self._threshold = t

    @property
    def in_threshold(self):
        return self._in_threshold

    @in_threshold.setter
    def in_threshold(self, tf):
        if self.in_threshold and not tf:
            if self.react is not None:
                self.react()

        self._in_threshold = tf

    def compare(self, value):
        ''' Compare the passed value(s) to thresholds if defined, and
            return the value and a bool reflecting the comparison. '''
        value = np.array(value)
        in_threshold = True

        if self.threshold[0] is not None:
            in_threshold &= (value >= self.threshold[0]).all()
        if self.threshold[1] is not None:
            in_threshold &= (value <= self.threshold[1]).all()

        self.in_threshold = in_threshold

        return in_threshold


class Watcher(Observer):
    def __init__(self, name, measure, threshold=(None, None), reaction=None):
        ''' Args:
                measure (function): an argument-less function returning a
                                       single float-valued variable.
                threshold (tuple): numerical lower and upper bounds for logical
                                   comparison. Deactivate either bound by passing
                                   None.
        '''
        super().__init__(name, threshold, reaction)
        self._measure = measure

    def measure(self):
        ''' Measure the assigned function and associate a timestamp. Return a
            single-row DataFrame. Future development will allow timestamped
            values reported in the user-defined function itself.
        '''
        now = datetime.datetime.utcnow().isoformat()
        result = self._measure()
        if isinstance(result, pd.DataFrame):
            return result
        return pd.DataFrame(result, index=[now], columns=[self.name])

class Listener(Observer):
    def __init__(self, name, address, threshold=(None, None), reaction=None):

        ''' Args:
                name (str)
                threshold (tuple): numerical lower and upper bounds for logical
                                   comparison. Deactivate either bound by passing
                                   None.
        '''
        super().__init__(name, threshold, reaction)

        self.queue = SimpleQueue()
        self.process = Process(target=self.listen, args=(name, address, self.queue))
        self.process.start()

    def listen(self, name, address, queue):
        subscriber = Subscriber(address)

        while True:
            value = subscriber.receive()
            now = datetime.datetime.utcnow().isoformat()
            self.queue.put(pd.DataFrame(value, index=[now], columns=[name]))

    def measure(self):
        data = pd.DataFrame()
        while not self.queue.empty():
            data = data.append(self.queue.get(), sort=False)
        return data

    def stop(self):
        self.process.terminate()
