#!/usr/bin/env bash

# EasyDT Web Dashboard - Run Script

# Determine the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install or update requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Clear the screen for better readability
clear

# Print a startup banner
echo "========================================================"
echo "             EasyDT Web Dashboard Starting              "
echo "========================================================"
echo ""
echo " All processing is done in memory - no temporary files! "
echo ""
echo " Access the dashboard at: http://localhost:5000         "
echo ""
echo "========================================================"
echo ""

# Run the server
python app.py "$@" 