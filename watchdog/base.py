''' This modules implements the Watchdog class for reactive monitoring. '''

import logging as log
log.basicConfig(level=log.INFO)
from abc import abstractmethod

class Watchdog():
    def __init__(self, experiment, threshold=(None,None), name='watchdog'):
        ''' Args:
                experiment (function): an argument-less function returning a single float-valued variable
                threshold (tuple): numerical lower and upper bounds for logical comparison.
                                   Deactivate either bound by passing None.
        '''
        self.experiment = experiment
        self.threshold = threshold
        self.name = name
        self.value = 0
        self.threshold_type = 'lower'
        self.state = 0

    def check(self):
        ''' Private method which calls self.measure then updates the state '''
        self.value = self.experiment()
        state = 1
        if self.threshold[0] is not None:
            state = state and self.value >= self.threshold[0]
        if self.threshold[1] is not None:
            state = state and self.value <= self.threshold[1]
        self.state = state

        if not self.state:
            log.debug('Watchdog %s is reacting to an unlock!', self.name)
            self.react()

        return self.value, self.state

    def react(self):
        ''' Overload this method to allow a custom reaction when monitored
            variables leave the acceptable range. '''
        return
