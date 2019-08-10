from watchdog import Monitor

def test_add_trace():
    m = Monitor(address=None)
    def read_voltage():
        return 2.13
    m.watch(read_voltage)
    m.check()
    assert 'read_voltage' == m.visualizer.fig.data[0]['name']
