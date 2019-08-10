from watchdog import Monitor
import time
import numpy as np
import pandas as pd

def read_voltage():
    return 2.13

def test_watch():
    m = Monitor()
    m.watch(read_voltage)
    m.check()

    assert m.data.iloc[0]['read_voltage'] == 2.13

def test_jitter():
    m = Monitor()
    m.watch(read_voltage)

    m.start_periodic(period=0.1)

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
    m.start_triggered(trigger=trigger)

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
    m.start_periodic(0.1)
    time.sleep(0.2)
    assert not m.on

    ## test upper threshold failing
    m = Monitor()
    m.watch(read_voltage, threshold=(None, 1), reaction=m.stop)
    m.start_periodic(0.1)
    time.sleep(0.2)
    assert not m.on

def test_logging():
    def read_integer():
        return np.random.randint(0, 10)

    import os
    if os.path.exists("test.csv"):
      os.remove("test.csv")

    m = Monitor(filename='test.csv')
    m.watch(read_integer)
    m.start_periodic(0.1)
    time.sleep(1)
    m.stop()

    loaded = pd.read_csv('test.csv', index_col=0)
    assert ((loaded-m.data).dropna()==0)['read_integer'].all()
    os.remove("test.csv")
