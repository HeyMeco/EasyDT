#!/bin/bash
# Simple runner for DTS Visualizer

# Install dependencies with uv
echo "Installing dependencies with uv..."
uv pip install -r requirements.txt

# Make sure dts_visualizer.py is executable
chmod +x dts_visualizer.py

# Run the visualizer with uv run
uv run dts_visualizer.py "$@" 