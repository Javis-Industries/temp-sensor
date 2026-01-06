#!/bin/bash
set -e # Exit immediately if any failures

echo "====================================="
echo "Temperature Monitor Installation"
echo "====================================="

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="/home/pi/temp_sensor"

echo ""
echo "Step 1: Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

echo ""
echo "Step 2: Creating installation directory..."
mkdir -p "$INSTALL_DIR"

echo ""
echo "Step 3: Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"

echo ""
echo "Step 4: Installing Python packages..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "Step 5: Copying files..."
cp "$SCRIPT_DIR/sensor.py" "$INSTALL_DIR/"

echo ""
echo "Step 6: Setting up systemd service..."
# Update service file with correct venv path
sed "s|/usr/bin/python3|$INSTALL_DIR/venv/bin/python3|g" \
    "$SCRIPT_DIR/systemd/temp-sensor.service" | \
    sudo tee /etc/systemd/system/temp-sensor.service > /dev/null

sudo systemctl daemon-reload

echo ""
echo "====================================="
echo "Installation complete!"
echo "====================================="
echo ""
echo "Next steps:"
echo "1. Edit the config file:"
echo "   nano $INSTALL_DIR/config.ini"
echo ""
echo "2. Update the 'location' setting for this Pi"
echo ""
echo "3. Enable and start the service:"
echo "   sudo systemctl enable temp-sensor"
echo "   sudo systemctl start temp-sensor"
echo ""
echo "4. Check the status:"
echo "   sudo systemctl status temp-sensor"
echo ""
echo "5. View metrics:"
echo "   curl http://localhost:9100/metrics"
echo ""