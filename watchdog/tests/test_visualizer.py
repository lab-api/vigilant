from watchdog import Monitor
from watchdog.extensions import Visualizer

def test_add_trace():
    m = Monitor()
    vis = Visualizer()
    m.add_extension(vis)

    def read_voltage():
        return 2.13
    m.watch(read_voltage)
    m.check()
    assert 'read_voltage' == vis.fig.data[0]['name']
