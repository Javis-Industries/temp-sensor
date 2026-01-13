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
    print("Copy config.ini.example to config.ini and update with your settings")
    sys.exit(1)

config.read(config_path)

# Configuration
SENSOR_LOCATION = config['sensor']['location']
SENSOR_PIN = getattr(board, config['sensor']['pin'])
READ_INTERVAL = 30 # Seconds
PROMETHEUS_PORT = 9100
LOG_FILE = config['logging']['log_file']
LOG_LEVEL = getattr(logging, config['logging']['log_level'])

# Ensure log directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Prometheus metrics
temp_c = Gauge('temp_c', 'Temperate in Celcius', ['location', 'sensor_type', 'hostname'])
temp_f = Gauge('temp_f', 'Temperature in Fahrenheiht', ['location', 'sensor_type', 'hostname'])
humidity = Gauge('humidity_pct', 'Humidiity Percentage', ['location', 'sensor_type', 'hostname'])
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
        else:
            temp_f = temp_c * (9 / 5) + 32

        if humidity is None:
            logging.warning("Received None value for humidity")

        # Update Prometheus metrics
        temp_c.labels(
            location=SENSOR_LOCATION, 
            sensor_type='DHT22',
            hostname=hostname
        ).set(round(temp_c, 1))
        
        temp_f.labels(
            location=SENSOR_LOCATION,
            sensor_type='DHT22',
            hostname=hostname
        ).set(round(temp_f, 1))
        
        humidity.labels(
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
        dht_device.exit()
        raise error
    
    except Exception as error:
        logging.error(f"Critical error: {error}", exc_info=True)
        dht_device.exit()
        raise error

    time.sleep(READ_INTERVAL)

    # Cleanup
    logging.info("Shutting down")
    dht_device.exit()