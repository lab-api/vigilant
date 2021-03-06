from vigilant import Monitor
from vigilant.extensions import Publisher
from hypothesis import given
import hypothesis.strategies as st
import time
import os
import numpy as np
import pandas as pd

def test_listen_watch_check():
    addr = '127.0.0.1:5002'
    publisher = Publisher(addr)
    m = Monitor()

    def placeholder():
        return None

    m.watch(placeholder, name='measure_x', threshold=(0, 1))
    m.listen('measure_y', addr, threshold=(0, 1))

    listener = m.categories['default']['measure_y']
    while listener.queue.empty():
        publisher.update(1)
    listener.measure()   # flush queue

    @given(st.floats(), st.floats())
    def test_check(x, y):
        # reset threshold checks to avoid contamination from previous test
        m.in_threshold = True
        m.categories['default']['measure_x'].in_threshold = True
        m.categores['default']['measure_y'].in_threshold = True


        def measure_x():
            return x

        m.categories['default']['measure_x']._measure = measure_x
        publisher.update(y)
        time.sleep(0.1)

        m.check()

        x_good = m.categories['default']['measure_x'].in_threshold
        y_good = m.categories['default']['measure_y'].in_threshold

        assert m.in_threshold == (x_good & y_good)

    test_check()
    listener.stop()
    publisher.socket.close()

def test_logging():
    def read_integer():
        return np.random.randint(0, 10)

    if os.path.exists("test.csv"):
      os.remove("test.csv")

    m = Monitor(filename='test.csv')
    m.watch(read_integer)
    for i in range(3):
        m.check()
        time.sleep(0.1)

    loaded = pd.read_csv('test.csv', index_col=0)
    assert ((loaded-m.data).dropna()==0)['default/read_integer'].all()
    os.remove("test.csv")

def test_periodic():
    def read_integer():
        return np.random.randint(0, 10)
    m = Monitor(period=0.1)
    m.watch(read_integer)

    m.start()

    time.sleep(5)
    m.stop()

    index = pd.DatetimeIndex(m.data.index).to_series()
    delta = (index-index.shift(1)).fillna(pd.Timedelta(seconds=0))

    delta = pd.TimedeltaIndex(delta).microseconds/1e6 + pd.TimedeltaIndex(delta).seconds
    assert np.abs(np.mean(delta)-0.1) < np.std(delta)

def test_triggering():
    def read_integer():
        return np.random.randint(0, 10)
    def trigger():
        time.sleep(.1)
        return
    m = Monitor(trigger=trigger)
    m.watch(read_integer)


    m.start()

    time.sleep(5)
    m.stop()

    index = pd.DatetimeIndex(m.data.index).to_series()
    delta = (index-index.shift(1)).fillna(pd.Timedelta(seconds=0))

    delta = pd.TimedeltaIndex(delta).microseconds/1e6 + pd.TimedeltaIndex(delta).seconds
    assert np.abs(np.mean(delta)-0.1) < np.std(delta)
