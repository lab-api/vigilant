# vigilant
[![Build Status](https://travis-ci.org/lab-api/vigilant.svg?branch=master)](https://travis-ci.org/lab-api/vigilant)
[![Test Coverage](https://api.codeclimate.com/v1/badges/1bf03b260cf34826639d/test_coverage)](https://codeclimate.com/github/lab-api/vigilant/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/1bf03b260cf34826639d/maintainability)](https://codeclimate.com/github/lab-api/vigilant/maintainability)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/lab-api/vigilant/master?filepath=vigilant%2Ftutorial.ipynb)

Vigilant is a Python framework for realtime, reactive process monitoring. Suppose we have a function ``read_voltage()`` which measures and returns a voltage. We can create a Monitor task to measure this voltage once per second:

```python
from vigilant import Monitor
monitor = Monitor()
monitor.watch(read_voltage)
monitor.start(period=1)
```

If you pass a threshold into the ``Monitor.watch()`` method, you can also define a reaction function to be called when a monitored variable exits the range. This can be used to alert operators to a failure, or to automatically bring the process back into the operational range:
```python
def react():
    print('Monitored variable out of range!')

monitor.watch(read_voltage, threshold=(0, 1), reaction=react)
```
You can also subscribe to external data feeds, which will be monitored asynchronously and merged with the dataset during the monitoring cycle:
```python
monitor.listen('voltage feed', address='127.0.0.1:9000')
```
Vigilant provides a number of other features, including:
* Adding new monitored variables dynamically
* Plotting acquired data in realtime
* Automatically saving data to file
* Data feed with ZMQ to which external processes can subscribe for UI or analysis
* Scalable time-series storage using InfluxDB

These features are covered in the [Tutorial notebook](https://github.com/robertfasano/vigilant/blob/master/vigilant/tutorial.ipynb), which can also be run in the cloud from the Binder badge above.

Note: some computers have issues displaying the Plotly graphs in Chrome. If no plot appears when the Visualizer extension is loaded, try running in Firefox.
