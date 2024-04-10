#!/usr/bin/env python3

import os
from app import create_app
import os
from datetime import datetime
from app import create_app
from time import sleep

import logging
from logging.handlers import RotatingFileHandler
import logging


current_dir = os.path.dirname(os.path.realpath(__file__))
config_file = f'{current_dir}/config.py'
sample_config_file = f'{current_dir}/config.sample'

def setup_logging():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    log_dir = os.path.join(current_dir, 'logs')
    log_file = os.path.join(log_dir, 'M3Usort.log')

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5)
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        handlers=[handler])

setup_logging()

# Check if config.py exists, if not, read from config.sample and write to config.py
if not os.path.exists(config_file):
    with open(sample_config_file, 'r') as sample_file:
        sample_content = sample_file.read()
    
    with open(config_file, 'w') as config:
        config.write(sample_content)
    
    print(f"'{config_file}' created from '{sample_config_file}'.")
    sleep(1)

app_start_time = datetime.now()
os.environ['TZ'] = 'Europe/Amsterdam'


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, 'config.py')
CONFIG_PATH = os.path.normpath(CONFIG_PATH)

with open(CONFIG_PATH, 'r') as file:
    config_content = file.read()
config_namespace = {}
exec(config_content, {}, config_namespace)
PORT_NUMBER = config_namespace.get('port_number')

from app import create_app
app = create_app()
app.app_start_time = datetime.now()


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=PORT_NUMBER)

    
