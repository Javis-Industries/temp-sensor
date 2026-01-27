# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import adafruit_dht
import logging
from prometheus_client import start_http_server, Gauge, Info
import sys
import socket
import configparser
import os

# Load configuration
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'config.ini')

if not os.path.exists(config_path):
    print(f"ERROR: config.ini not found at {config_path}")
    print("Copy config.ini.template to config.ini and update with your settings")
    sys.exit(1)

config.read(config_path)

# Configuration
SENSOR_LOCATION = config['sensor']['location']
SENSOR_PIN = getattr(board, config['sensor']['pin'])
READ_INTERVAL = config.getint('sensor', 'read_interval')
PROMETHEUS_PORT = config.getint('prometheus', 'port')

# Make log file path absolute if it's relative
log_file_config = config['logging']['log_file']
if not os.path.isabs(log_file_config):
    # If relative path, make it relative to the script directory
    LOG_FILE = os.path.join(os.path.dirname(__file__), log_file_config)
else:
    LOG_FILE = log_file_config

LOG_LEVEL = getattr(logging, config['logging']['log_level'])

# Ensure log directory exists (only if path contains a directory)
log_dir = os.path.dirname(LOG_FILE)
if log_dir:  # Only create directory if path includes one
    os.makedirs(log_dir, exist_ok=True)

# Prometheus metrics
temp_c_gauge = Gauge('temp_c', 'Temperature in Celsius', ['location', 'sensor_type', 'hostname'])
temp_f_gauge = Gauge('temp_f', 'Temperature in Fahrenheit', ['location', 'sensor_type', 'hostname'])
humidity_gauge = Gauge('humidity_pct', 'Humidity Percentage', ['location', 'sensor_type', 'hostname'])
sensor_info = Info('sensor', 'Sensor information')

# Sensor health metrics
sensor_read_errors = Gauge('sensor_read_errors_total', 'Total number of sensor read errors', ['location', 'hostname'])

last_successful_read = Gauge('sensor_last_successful_read_timestamp', 'Timestamp of last successful sensor read', ['location', 'hostname'])

# Initialize the dht device, with data pin connected to SENSOR_PIN
dht_device = adafruit_dht.DHT22(SENSOR_PIN)
hostname = socket.gethostname()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

# Set sensor metadata
sensor_info.info({
    'location': SENSOR_LOCATION,
    'sensor_type': 'DHT22',
    'hostname': hostname,
    'version': '1.0'
})

# Start Prometheus HTTP server
try:
    start_http_server(PROMETHEUS_PORT)
    logging.info(f"Prometheus metrics server started on port {PROMETHEUS_PORT}")
    logging.info(f"Metrics available at http://{hostname}:{PROMETHEUS_PORT}/metrics")
except Exception as e:
    logging.error(f"Failed to start metrics server: {e}")
    sys.exit(1)

logging.info(f"Temperature monitoring started for {SENSOR_LOCATION}")

# Main loop
error_count = 0

while True:
    try:
        # Read sensor
        temp_c = dht_device.temperature
        humidity = dht_device.humidity

        # Validate temperature reading
        if temp_c is None:
            logging.warning("Received None value for temperature")
            continue
        
        temp_f = temp_c * (9 / 5) + 32

        if humidity is None:
            logging.warning("Received None value for humidity")
            continue

        # Update Prometheus metrics
        temp_c_gauge.labels(
            location=SENSOR_LOCATION, 
            sensor_type='DHT22',
            hostname=hostname
        ).set(round(temp_c, 1))
        
        temp_f_gauge.labels(
            location=SENSOR_LOCATION,
            sensor_type='DHT22',
            hostname=hostname
        ).set(round(temp_f, 1))
        
        humidity_gauge.labels(
            location=SENSOR_LOCATION,
            sensor_type='DHT22',
            hostname=hostname
        ).set(round(humidity, 1))
        
        last_successful_read.labels(
            location=SENSOR_LOCATION,
            hostname=hostname
        ).set(time.time())

        logging.info(f'✓ Temp: {temp_f:0.1f}°F ({temp_c:0.1f}°C), Humidity: {humidity:0.1f}%')

    except RuntimeError as error:
        # DHT sensor read errors are common
        error_count += 1
        sensor_read_errors.labels(
            location=SENSOR_LOCATION,
            hostname=hostname
        ).set(error_count)
        logging.warning(f"Sensor read error (total: {error_count}): {error.args[0]}")
        time.sleep(2.0)
        continue
    
    except Exception as error:
        logging.error(f"Critical error: {error}", exc_info=True)
        dht_device.exit()
        raise error

    time.sleep(READ_INTERVAL)

    # Cleanup
    logging.info("Shutting down")
    dht_device.exit()