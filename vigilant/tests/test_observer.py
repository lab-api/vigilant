from vigilant.base import Observer, Watcher, Listener
from vigilant.extensions import Publisher
from hypothesis import given
import hypothesis.strategies as st
import time
import numpy as np
import pytest

def ensure_valid_bounds(lower, upper):
    if lower > upper:
        temp = lower
        lower = upper
        upper = temp
    return lower, upper

@given(st.floats(), st.floats(), st.floats())
def test_comparison(value, lower, upper):
    ''' Generate random values and thresholds and verify that comparison works '''
    lower, upper = ensure_valid_bounds(lower, upper)
    valid = (value >= lower) & (value <= upper)

    if lower == upper:
        return

    bounded_observer = Observer('test', threshold=(lower, upper), reaction=None)
    bounded_observer.TESTFLAG = True
    def react():
        bounded_observer.TESTFLAG = False
    bounded_observer.react = react
    assert bounded_observer.compare(value) == valid
    assert bounded_observer.in_threshold == valid
    assert bounded_observer.TESTFLAG == valid

    unbounded_observer = Observer('test', threshold=(None, None), reaction=None)
    assert unbounded_observer.compare(value) == True
    assert unbounded_observer.in_threshold == True

@given(st.floats(), st.floats(), st.floats())
def test_watcher(value, lower, upper):
    ''' Generate random results for a Watcher measurement and check that the
        comparison is correct.
    '''
    lower, upper = ensure_valid_bounds(lower, upper)
    valid = (value >= lower) & (value <= upper)
    if lower == upper:
        return
    def measure():
        return value

    watcher = Watcher('test', measure, threshold=(lower, upper), reaction=None)
    result = watcher.measure()
    assert watcher.compare(result) == valid

def test_listener():
    ''' Generate random results, publish them over socket, intercept with a
        Listener, and check that the comparison is correct.
    '''
    addr = '127.0.0.1:5002'
    publisher = Publisher(addr)
    listener = Listener('test', addr, threshold=(None, None), reaction=None)

    while listener.queue.empty():
        publisher.update(1)
    listener.measure()   # flush queue

    @given(st.floats(), st.floats(), st.floats())
    def test_listener_comparison(value, lower, upper):
        ''' Warning: test fails for infinite/nan values '''
        lower, upper = ensure_valid_bounds(lower, upper)
        if lower == upper:
            return

        if np.isinf(value) or np.isnan(value):
            return

        valid = (value >= lower) & (value <= upper)

        listener.threshold = (lower, upper)

        publisher.update(value)
        time.sleep(0.1)
        result = listener.measure()

        assert listener.compare(result) == valid

    test_listener_comparison()
    listener.stop()
    publisher.socket.close()

@given(st.floats(), st.floats())
def test_invalid_bounds(lower, upper):
    if lower >= upper:
        with pytest.raises(ValueError):
            assert Observer('test', threshold=(lower, upper), reaction=None)
