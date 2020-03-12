import subprocess
import os
from vigilant import config

def make_address(ip, port):
    return f'http://{ip}:{port}'

os.environ['KAPACITOR_DATA_DIR'] = "/Users/robbiefasano/.kapacitor"
os.environ['INFLUX_URL']=make_address(config['influx']['address'], config['influx']['port'])
os.environ['KAPACITOR_INFLUXDB_0_URLS_0']=os.environ['INFLUX_URL']
os.environ['INFLUX_DATABASE']=config['influx']['database']
os.environ['VIGILANT_ENDPOINT']=make_address(config['monitor']['address'], config['monitor']['port'])
os.environ['INFLUX_MEASUREMENT']=config['influx']['measurement']
os.environ['KAPACITOR_PORT']=str(config['kapacitor']['port'])
os.environ['KAPACITOR_BIND_ADDRESS']=f':{os.environ["KAPACITOR_PORT"]}'

kapacitor = subprocess.Popen(['kapacitord --config ./kapacitor.conf'], shell=True)
print('Started kapacitor on process', kapacitor.pid)
telegraf = subprocess.Popen(['telegraf --config ./telegraf.conf'], shell=True)
print('Started telegraf on process', telegraf.pid)

while True:
    continue

os.killpg(kapacitor.pid, signal.SIGTERM)
os.killpg(telegraf.pid, signal.SIGTERM)
