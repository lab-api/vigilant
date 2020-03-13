import subprocess
import os
from vigilant import config

## cd into directory of this script for relative imports of .conf files
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

def make_address(ip, port):
    return f'http://{ip}:{port}'

os.environ['KAPACITOR_DATA_DIR'] = config['kapacitor']['data_dir']
os.environ['INFLUX_URL']=make_address(config['influx']['address'], config['influx']['port'])
os.environ['KAPACITOR_INFLUXDB_0_URLS_0']=os.environ['INFLUX_URL']
os.environ['INFLUX_DATABASE']=config['influx']['database']
os.environ['VIGILANT_ENDPOINT']=make_address(config['monitor']['address'], config['monitor']['port'])
os.environ['INFLUX_MEASUREMENT']=config['influx']['measurement']
os.environ['KAPACITOR_PORT']=str(config['kapacitor']['port'])
os.environ['KAPACITOR_URL']=make_address(config['kapacitor']['address'], config['kapacitor']['port'])
os.environ['KAPACITOR_BIND_ADDRESS']=f':{os.environ["KAPACITOR_PORT"]}'

influx = subprocess.Popen(['influxd', '--config', './influxdb.conf'])
print('Started influx on process', influx.pid)

telegraf = subprocess.Popen(['telegraf', '--config', './telegraf.conf'])
print('Started telegraf on process', telegraf.pid)

kapacitor = subprocess.Popen(['kapacitord', '--config', './kapacitor.conf'])
print('Started kapacitor on process', kapacitor.pid)

while True:
    continue

os.killpg(kapacitor.pid, signal.SIGTERM)
os.killpg(telegraf.pid, signal.SIGTERM)
os.killpg(influx.pid, signal.SIGTERM)
