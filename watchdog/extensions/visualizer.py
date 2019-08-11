import numpy as np
from IPython.display import display
import plotly.graph_objs as go

class Visualizer():
    ''' Handles plotting in Jupyter notebooks using Plotly. '''
    def __init__(self):
        layout = go.Layout(
            xaxis={'title': 'Time'},
            yaxis={'title': 0}
        )

        self.fig = go.FigureWidget([], layout=layout)
        display(self.fig)

    def add_trace(self, name):
        ''' Add a new trace to the plot corresponding to a name string in
            self.data.columns.
        '''
        self.fig.add_trace(go.Scatter(y=[],
                                      x=[],
                                      mode='markers',
                                      name=name
                                      ))

    def refresh(self):
        ''' Redraw the plot using data from self.data. More computationally
            expensive than appending data to the plot, so this should only be
            called if the plot and self.data are out of sync (e.g. if plotting is
            started during a run).
        '''
        for plot in self.fig.data:
            plot['x'] = self.data.index
            plot['y'] = self.data[plot['name']]

    def update(self, data):
        ''' Adds new data to the plot.
            Args:
                data (pandas.DataFrame): a DataFrame containing new data
        '''
        for col in data.columns:
            if col not in [x['name'] for x in self.fig.data]:
                self.add_trace(col)

        for plot in self.fig.data:
            plot['x'] = np.append(plot['x'], data.index[0])
            plot['y'] = np.append(plot['y'], data[plot['name']])
