# Raspberry Pi Temp Sensor

Read temperature and humidity data from a DHT22 sensor connected to a Raspberry Pi.

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
nano /home/temp-sensor/config.ini
# Change: location = server_room_floor_1

# Start service
sudo systemctl enable temp-sensor
sudo systemctl start temp-sensor

# Verify
curl http://localhost:9100/metrics
```
