import plotly.graph_objs as go
import numpy as np
# from IPython.display import display

class Visualizer():
    def __init__(self, data):
        self.data = data
        self.make_fig()
        self.active = True

    def make_fig(self):
        layout = go.Layout(
            xaxis={'title': 'Time'},
            yaxis={'title': 0}
        )

        self.fig = go.FigureWidget([], layout=layout)
        for col in self.data.columns:
            self.add_trace(col)

    def plot(self):
        display(self.fig)

    def add_trace(self, name):
        self.fig.add_trace(go.Scatter(y = self.data[name],
                                      x = self.data.index,
                                      mode = 'markers',
                                      name = name
                                      ))
    def refresh(self):
        for plot in self.fig.data:
            plot['x'] = self.data.index
            plot['y'] = self.data[plot['name']]

    def update(self, data):
        ''' Adds new data to the plot. '''
        for plot in self.fig.data:
            plot['x'] = np.append(plot['x'], data.index[0])
            plot['y'] = np.append(plot['y'], data[plot['name']])
