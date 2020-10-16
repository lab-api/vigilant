import yaml, os
path = os.path.dirname(__file__)
class Configurator:
    @staticmethod
    def load(*fields):
        ''' Loads and returns the configuration file. If fields are specified,
            returns only the corresponding values. '''
        config_path = os.path.join(path, 'config.yml')
        with open(config_path) as file:
            config = yaml.load(file, Loader=yaml.SafeLoader)
        if len(fields) == 0:
            return config
        else:
            return [config[f] for f in fields]

    @staticmethod
    def save(config):
        with open(os.path.join(path, 'config.yml'), 'w') as file:
            yaml.dump(config, file)


    @staticmethod
    def update(field, new_value):
        config = Configurator.load()
        config[field] = new_value
        Configurator.save(config)

# config = Configurator.load()

from .base import Watcher, Listener
from .monitor import Monitor
