from watchdog import Monitor
from watchdog.extensions import Publisher
import time
import numpy as np
import pandas as pd
import os

def read_voltage():
    return 2.13

def test_listen():
    m = Monitor()
    m.listen('data feed', address='127.0.0.1:9000')

    feed = Publisher('127.0.0.1:9000')
    time.sleep(0.5)
    feed.update(3.14)
    time.sleep(0.5)
    m.check()

    m.listeners['data feed'].stop()
    assert m.data.iloc[0]['data feed'] == 3.14

def test_watch():
    m = Monitor()
    m.watch(read_voltage)
    m.check()

    assert m.data.iloc[0]['read_voltage'] == 2.13

def test_jitter():
    m = Monitor()
    m.watch(read_voltage)

    m.start(period=0.1)

    time.sleep(5)
    m.stop()

    index = pd.DatetimeIndex(m.data.index).to_series()
    delta = (index-index.shift(1)).fillna(0)

    delta = pd.TimedeltaIndex(delta).microseconds/1e6 + pd.TimedeltaIndex(delta).seconds
    assert np.abs(np.mean(delta)-0.1) < np.std(delta)

def test_triggering():
    m = Monitor()
    m.watch(read_voltage)

    import time
    def trigger():
        time.sleep(.1)
        return
    m.start(trigger=trigger)

    time.sleep(5)
    m.stop()

    index = pd.DatetimeIndex(m.data.index).to_series()
    delta = (index-index.shift(1)).fillna(0)

    delta = pd.TimedeltaIndex(delta).microseconds/1e6 + pd.TimedeltaIndex(delta).seconds
    assert np.abs(np.mean(delta)-0.1) < np.std(delta)

def test_react():
    ## test lower threshold failing
    m = Monitor()
    m.watch(read_voltage, threshold=(3, None), reaction=m.stop)
    m.start(period=0.1)
    time.sleep(0.2)
    assert not m.running

    ## test upper threshold failing
    m = Monitor()
    m.watch(read_voltage, threshold=(None, 1), reaction=m.stop)
    m.start(period=0.1)
    time.sleep(0.2)
    assert not m.running

def test_logging():
    def read_integer():
        return np.random.randint(0, 10)

    if os.path.exists("test.csv"):
      os.remove("test.csv")

    m = Monitor(filename='test.csv')
    m.watch(read_integer)
    m.start(period=0.1)
    time.sleep(1)
    m.stop()

    loaded = pd.read_csv('test.csv', index_col=0)
    assert ((loaded-m.data).dropna()==0)['read_integer'].all()
    os.remove("test.csv")
