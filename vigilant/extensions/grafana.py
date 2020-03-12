import requests, json, numpy as np
from vigilant import config

class Dashboard:
    row_width = 24
    panels_per_row = 4
    panel_width = row_width / panels_per_row
    panel_height = 8

    def __init__(self, measurement, title='LabAPI', uid='vigilant-dashboard'):
        self.title = title
        self.measurement = measurement
        self.uid = uid

        try:
            self.model = self.download()
        except IndexError:
            self.model = self.template()

        self.build_schema()

    def add_row(self, title, overwrite=False):
        if title in self.rows and not overwrite:
            return
        id = len(self.rows) + len(self.panels)
        self.rows[title] = Row(title, id)

    def add_panel(self, title, row, bounds=(-np.inf, np.inf), overwrite=False):
        field = row + '/' + title
        if row not in self.rows:
            self.add_row(row)
        if field in self.rows[row].children and not overwrite:
            return
        id = len(self.rows) + len(self.panels)
        siblings = self.rows[row].children.copy()
        self.rows[row].children.append(field)

        ## determine positioning
        x = (len(siblings) % self.panels_per_row) * self.panel_width
        y = (int(np.floor(len(siblings) / self.panels_per_row))) * self.row_width
        panel = Panel(title, self.measurement, field, id, x, y, self.panel_width, self.panel_height, bounds=bounds)
        self.panels[field] = panel

    def build_schema(self):
        self.rows = {}
        self.panels = {}

        for item in self.model['panels']:
            if item['type'] == 'row':
                self.rows[item['title']] = Row.load(item)
            else:
                last_row_name = list(self.rows.keys())[-1]
                field = last_row_name + '/' + item['title']
                self.rows[last_row_name].children.append(field)
                self.panels[field] = Panel.load(item)

    def download(self):
        ''' Attempt to download the dashboard matching the passed uid '''
        headers = {"Authorization": f"Bearer {config['grafana']['api key']}",
               "Content-Type": "application/json"}
        address = f"http://{config['grafana']['address']}:{config['grafana']['port']}"
        r = requests.get(f"{address}/api/dashboards/uid/{self.uid}", headers = headers)
        if r.json() == {'message': 'Dashboard not found'}:
            raise IndexError('Dashboard not found')
        dashboard = r.json()['dashboard']
        return dashboard

    def post(self):
        headers = {"Authorization": f"Bearer {config['grafana']['api key']}",
                   "Content-Type": "application/json"}
        data = {"dashboard": self.model,
                "overwrite": "true"}
        data = json.dumps(data).replace('"null"', 'null').replace('"false"', 'false').replace('"true"', 'true')
        address = f"http://{config['grafana']['address']}:{config['grafana']['port']}"
        r = requests.post(f"{address}/api/dashboards/import", data=data, headers=headers)


    def render(self):
        panels = []
        for row_id, row in self.rows.items():
            panels.append(row.model())

            for panel_id in row.children:
                panels.append(self.panels[panel_id].model())

        self.model['panels'] = panels

    def template(self):
        dashboard = {
          "annotations": {
            "list": [
              {
                "builtIn": 1,
                "datasource": "-- Grafana --",
                "enable": 'true',
                "hide": 'true',
                "iconColor": "rgba(0, 211, 255, 1)",
                "name": "Annotations & Alerts",
                "type": "dashboard"
              }
            ]
          },
          "id": self.uid,
          "panels": [],
          "refresh": "1s",
          "schemaVersion": 22,
          "time": {"from": "now-5m", "to": "now"},
          "timepicker": {"refresh_intervals": ["1s", "10s", "1m", "10m"]},
          "timezone": "browser",
          "title": self.title,
          "uid": self.uid,
          "version": 0
        }
        return dashboard

class Row:
    def __init__(self, title, id):
        self.title = title
        self.id = id
        self.children = []

    @staticmethod
    def load(model):
        return Row(model['title'], model['id'])

    def model(self):
        return {
          "collapsed": "false",
          "datasource": "null",
          "gridPos": {
            "h": 1,
            "w": 24,
            "x": 0,
            "y": 0
          },
          "id": self.id,
          "panels": [],
          "title": self.title,
          "type": "row"
        }

class Panel:
    def __init__(self, title, measurement, field, id, x, y, w, h, bounds=(-np.inf, np.inf)):
        self.title = title
        self.measurement = measurement
        self.field = field
        self.id = id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.bounds = bounds

    @staticmethod
    def load(model):
        ''' Build a Panel instance from a JSON model '''
        title = model['title']
        measurement = model['targets'][0]['measurement']
        field = model['targets'][0]['select'][0][0]['params'][0]
        id = model['id']
        x = model['gridPos']['x']
        y = model['gridPos']['y']
        w = model['gridPos']['w']
        h = model['gridPos']['h']
        bounds = None
        if 'alert' in model:
            evaluator =  model['alert']['conditions'][0]['evaluator']
            if evaluator['type'] == 'gt':
                bounds = [-np.inf, evaluator['params'][0]]
            elif evaluator['type'] == 'lt':
                bounds = [evaluator['params'][0], np.inf]
            elif evaluator['type'] == 'outside_range':
                bounds = evaluator['params']
        return Panel(title, measurement, field, id, x, y, w, h, bounds)

    def model(self):
        target = {
                  "groupBy": [],
                  "measurement": self.measurement,
                  "orderByTime": "ASC",
                  "policy": "default",
                  "refId": "A",
                  "resultFormat": "time_series",
                  "select": [
                    [
                      {
                        "params": [
                          self.field
                        ],
                        "type": "field"
                      }
                    ]
                  ],
                  "tags": []
                }
        alert = {}
        thresholds = []
        if np.isfinite(self.bounds[0]) and np.isfinite(self.bounds[1]):
            evaluator = {'params': self.bounds, 'type': 'outside_range'}
            thresholds = [{'colorMode': 'critical',
                            'fill': 'true',
                            'line': 'true',
                            'op': 'lt',
                            'value': self.bounds[0]},
                           {'colorMode': 'critical',
                            'fill': 'true',
                            'line': 'true',
                            'op': 'gt',
                            'value': self.bounds[1]}]



        elif np.isfinite(self.bounds[0]):
            evaluator = {'params': [self.bounds[0]], 'type': 'lt'}
            thresholds = [{'colorMode': 'critical',
                            'fill': 'true',
                            'line': 'true',
                            'op': 'lt',
                            'value': self.bounds[0]}]

        elif np.isfinite(self.bounds[1]):
            evaluator = {'params': [self.bounds[1]], 'type': 'gt'}
            thresholds = [{'colorMode': 'critical',
                            'fill': 'true',
                            'line': 'true',
                            'op': 'gt',
                            'value': self.bounds[1]}]


        if len(thresholds) > 0:
            alert = {'alertRuleTags': {},
             'conditions': [{'evaluator': evaluator,
               'operator': {'type': 'and'},
               'query': {'params': ['A', '3s', 'now']},
               'reducer': {'params': [], 'type': 'avg'},
               'type': 'query'}],
             'executionErrorState': 'alerting',
             'for': '5s',
             'frequency': '1s',
             'handler': 1,
             'name': f'{self.title} alert',
             'noDataState': 'no_data',
             'notifications': []}

        return {
              "alert": alert,
              "thresholds": thresholds,
              "gridPos": {
                "h": self.h,
                "w": self.w,
                "x": self.x,
                "y": self.y
              },
              "id": self.id,
              "targets": [target],
              "title": self.title,
              "type": "graph",
        }
