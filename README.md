# watchdog
[![Build Status](https://travis-ci.org/robertfasano/watchdog.svg?branch=master)](https://travis-ci.org/robertfasano/watchdog)
[![Coverage Status](https://coveralls.io/repos/github/robertfasano/watchdog/badge.svg)](https://coveralls.io/github/robertfasano/watchdog)
[![Maintainability](https://api.codeclimate.com/v1/badges/0be76138b49ecb2081eb/maintainability)](https://codeclimate.com/github/robertfasano/watchdog/maintainability)

Watchdog is a Python framework for realtime, reactive process monitoring. Suppose we have a function ``read_voltage()`` which measures and returns a voltage. We can create a Monitor task to measure this voltage once per second:

```python
from watchdog import Monitor
m = Monitor()
m.watch(read_voltage)
m.start_periodic(period=1)
```

If you pass a threshold into the ``Monitor.watch()`` method, you can also define a reaction function to be called when a monitored variable exits the range. This can be used to alert operators to a failure, or to automatically bring the process back into the operational range:
```python
def react():
    print('Monitored variable out of range!')
    
m.watch(read_voltage, threshold=(0, 1), reaction=react)
```

Watchdog provides a number of other features, including:
* Adding new monitored variables dynamically
* Plotting acquired data in realtime
* Automatically saving data to file
* Custom callbacks to pipe acquired data to external processes for UI or analysis
These features are covered in the [Tutorial notebook](https://github.com/robertfasano/watchdog/blob/master/watchdog/tutorial.ipynb).
