#!/bin/bash

# Activate the virtual environment
source venv_py311/bin/activate

# Make sure we're using the correct Python version
echo "Using Python: $(which python)"
echo "Python version: $(python --version)"

# Get the local IP address
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "Your local IP address is: $LOCAL_IP"
echo "Other computers on the network can access this application at: http://$LOCAL_IP:8080"

# Blockchain setup information
echo ""
echo "=== BLOCKCHAIN SETUP ==="
echo "If you're running Ganache on this machine and want it accessible from other machines:"
echo "1. Open Ganache and go to Settings"
echo "2. Under 'SERVER' tab, change HOSTNAME from '127.0.0.1' to '0.0.0.0'"
echo "3. Click 'SAVE AND RESTART'"
echo "4. Other machines should use http://$LOCAL_IP:7545 as the BLOCKCHAIN_URL"
echo ""
echo "To set the blockchain URL for this application, you can:"
echo "export BLOCKCHAIN_URL=http://<blockchain-ip>:7545"
echo ""

# Run the application with network access
python app.py --host 0.0.0.0 --port 8080 