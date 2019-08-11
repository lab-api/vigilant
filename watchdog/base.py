''' This modules implements the Watchdog class for reactive monitoring. '''
from multiprocessing import Process, SimpleQueue
import datetime
import pandas as pd
import numpy as np
from watchdog.extensions import Subscriber

class Watcher():
    def __init__(self, name, experiment, threshold=(None, None), reaction=None):
        ''' Args:
                experiment (function): an argument-less function returning a
                                       single float-valued variable.
                threshold (tuple): numerical lower and upper bounds for logical
                                   comparison. Deactivate either bound by passing
                                   None.
        '''
        self.experiment = experiment
        self.threshold = threshold
        self.name = name
        self.react = reaction

    def check(self):
        ''' Measure the attached function, compare to thresholds if defined, and
            return the value and a bool reflecting the comparison. '''
        value = self.experiment()
        state = 1
        if self.threshold[0] is not None:
            state = state and value >= self.threshold[0]
        if self.threshold[1] is not None:
            state = state and value <= self.threshold[1]

        if not state and self.react is not None:
            self.react()

        return value, state

class Listener():
    def __init__(self, name, address, threshold=(None, None), reaction=None):

        ''' Args:
                name (str)
                threshold (tuple): numerical lower and upper bounds for logical
                                   comparison. Deactivate either bound by passing
                                   None.
        '''
        self.name = name
        self.threshold = threshold
        self.react = reaction
        self.queue = SimpleQueue()

        self.process = Process(target=self.listen, args=(name, address, self.queue))
        self.process.start()

    def check(self, value):
        ''' Compare the passed value(s) to thresholds if defined, and
            return the value and a bool reflecting the comparison. '''
        value = np.array(value)
        state = 1
        if self.threshold[0] is not None:
            state = state and (value >= self.threshold[0]).all()
        if self.threshold[1] is not None:
            state = state and (value <= self.threshold[1]).all()

        if not state and self.react is not None:
            self.react()

        return value, state

    def listen(self, name, address, queue):
        subscriber = Subscriber(address)

        while True:
            value = subscriber.receive()
            now = datetime.datetime.now().isoformat()
            self.queue.put(pd.DataFrame(value, index=[now], columns=[name]))

    def stop(self):
        self.process.terminate()
