# DHT22 Temperature and Humidity Sensor

Read temperature and humidity data from a DHT22 sensor connected to a Raspberry Pi or other Blinka-supported boards. See a list of supported boards [here](https://circuitpython.org/blinka).

## Deployment

```bash
# SSH into Pi
ssh pi@192.168.1.100

# Clone and install
cd ~
git clone https://github.com/Javis-Industries/temp-sensor
cd temp-sensor
./install.sh

# Edit config for this location
nano ~/temp-sensor/config.ini
# Change: location = server_room_floor_1

# Start service
sudo systemctl enable temp-sensor
sudo systemctl start temp-sensor

# Verify
curl http://localhost:9100/metrics
```

## Prometheus Configuration

This project exposes metrics on port 9100 by default. Below is an example job configuration for Prometheus to scrape these metrics.

````yaml
scrape_configs:
  - job_name: "temperature-sensors"
    static_configs:
      - targets:
          - "hostname:9100" # Replace with your device's IP or hostname
    scrape_interval: 30s```
````

## Example Queries

| Query                                | Description             |
| ------------------------------------ | ----------------------- |
| temp_f{location="server_room"}       | Current temperature     |
| humidity_pct{location="server_room"} | Current humidity        |
| avg_over_time(temp_f[1h])            | Avg temp over last hour |
| sensor_read_errors_total             | Total read errors       |
