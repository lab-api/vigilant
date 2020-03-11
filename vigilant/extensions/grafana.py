import requests, json, numpy as np
from vigilant import config

def make_dashboard(title='Dashboard'):
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
      "id": 'null',
      "panels": [],
      "refresh": "1s",
      "schemaVersion": 22,
      "time": {"from": "now-5m", "to": "now"},
      "timepicker": {"refresh_intervals": ["1s", "10s", "1m", "10m"]},
      "timezone": "browser",
      "title": title,
      "uid": 'null',
      "version": 0
    }
    return dashboard



def get_dashboard_by_title(title):
    results = []

    headers = {"Authorization": f"Bearer {config['grafana']['api key']}",
           "Content-Type": "application/json"}
    address = f"http://{config['grafana']['address']}:{config['grafana']['port']}"
    r = requests.get(f"{address}/api/search", headers = headers).json()
    for db in r:
        if db['title'] == title:
            results.append(db)

    if len(results) > 1:
        raise Exception('Duplicate dashboard titles found!')

    return results[0]

def get_dashboard_by_uid(uid):
    headers = {"Authorization": f"Bearer {config['grafana']['api key']}",
           "Content-Type": "application/json"}
    address = f"http://{config['grafana']['address']}:{config['grafana']['port']}"
    r = requests.get(f"{address}/api/dashboards/uid/{uid}", headers = headers)
    dashboard = r.json()['dashboard']
    return dashboard

class Generator:
    panel_width = 6
    panel_height = 8
    panels_per_row = 4
    row_width = panel_width*panels_per_row
    row_height = 1

    def __init__(self, monitor):
        self.monitor = monitor
        self.measurement = monitor.measurement

        ## get dashboard by name
        try:
            self.uid = get_dashboard_by_title(monitor.dashboard)['uid']
            self.dashboard = get_dashboard_by_uid(self.uid)
        except IndexError:
            self.dashboard = make_dashboard(monitor.dashboard)

    def make_panel(self, field, title='New panel', id=0, x=0, y=0):
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
                          field
                        ],
                        "type": "field"
                      }
                    ]
                  ],
                  "tags": []
                }

        return {
              "gridPos": {
                "h": self.panel_height,
                "w": self.panel_width,
                "x": x,
                "y": y
              },
              "id": id,
              "targets": [target],
              "title": title,
              "type": "graph",
        }

    def make_row(self, title, id):
            return {
              "collapsed": "false",
              "datasource": "null",
              "gridPos": {
                "h": 1,
                "w": 24,
                "x": 0,
                "y": 0
              },
              "id": id,
              "panels": [],
              "title": title,
              "type": "row"
            }

    def add_category(self, category):
        ''' Appends a new row panel at the end of the dashboard '''
        new_row = self.make_row(title=category, id=len(self.dashboard['panels']))
        self.dashboard['panels'].append(new_row)

    def get_row_position(self, category):
        i = 0
        while True:
            panel = self.dashboard['panels'][i]
            if panel['type'] == 'row' and panel['title'] == category:
                return i
            i += 1

    def get_panels_in_row(self, category):
        i = self.get_row_position(category)
        panels = []
        while True:
            i += 1
            if i == len(self.dashboard['panels']) or self.dashboard['panels'][i]['type'] == 'row':
                break
            panels.append(self.dashboard['panels'][i])
        return panels

    def add_panel(self, category, field, title):
        siblings = self.get_panels_in_row(category)
        target_index = self.get_row_position(category) + len(siblings) + 1
        i = len(self.dashboard['panels'])
        x = (len(siblings) % self.panels_per_row) * self.panel_width
        y = (int(np.floor(len(siblings) / self.panels_per_row))) * self.row_width
        new_panel = self.make_panel(field, title=title, id=i, x=x, y=y)

        self.dashboard['panels'].insert(target_index, new_panel)

    def clear(self):
        self.dashboard['panels'] = []

    def generate(self, overwrite=False):
        existing = self.list_observers()
        for category in self.monitor.categories:
            if category not in existing or overwrite:
                if len(self.monitor.categories[category]) > 0:
                    self.add_category(category)
                    existing[category] = []
            for observer in self.monitor.categories[category].values():
                field = observer.name
                title = field.split(category+'/')[1]
                if title not in existing[category] or overwrite:
                    self.add_panel(category, field, title)
        self.post()

    def post(self):
        headers = {"Authorization": f"Bearer {config['grafana']['api key']}",
                   "Content-Type": "application/json"}
        data = {"dashboard": self.dashboard,
                "overwrite": "true"}
        data = json.dumps(data).replace('"null"', 'null').replace('"false"', 'false').replace('"true"', 'true')
        address = f"http://{config['grafana']['address']}:{config['grafana']['port']}"
        r = requests.post(f"{address}/api/dashboards/import", data=data, headers=headers)

    def list_observers(self):
        categories = []
        observers = {}
        for panel in self.dashboard['panels']:
            if panel['type'] == 'row':
                categories.append(panel['title'])
                observers[panel['title']] = []
            else:
                observers[categories[-1]].append(panel['title'])

        return observers
