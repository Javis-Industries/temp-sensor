#!/bin/bash
set -euo pipefail # Exit immediately if any failures

echo "====================================="
echo "Temperature Monitor Installation"
echo "====================================="

# Get the directory where the script is located
INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo ""
echo "Installing to: $INSTALL_DIR"
echo ""

echo ""
echo "Step 1: Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

echo ""
echo "Step 2: Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"

echo ""
echo "Step 3: Installing Python packages..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

echo ""
echo "Step 4: Copying files..."
if [ ! -f "$INSTALL_DIR/config.ini" ]; then
      cp "$INSTALL_DIR/config.ini.template" "$INSTALL_DIR/config.ini"
      echo "Created config.ini - please edit before starting the service"
  else
      echo "config.ini already exists, keeping existing configuration"
  fi

echo ""
echo "Step 6: Setting up systemd service..."
# Update service file with correct venv path
sed -e "s|{{USER}}|$USER|g" \
    -e "s|{{INSTALL_DIR}}|$INSTALL_DIR|g" \
    "$SOURCE_DIR/systemd/temp-sensor.service" | \
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