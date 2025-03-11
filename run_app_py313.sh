#!/bin/bash

# Activate the Python 3.13 virtual environment
source venv_py313/bin/activate

# Make sure we're using the correct Python version
echo "Using Python: $(which python)"
echo "Python version: $(python --version)"

# Run the application
python app.py 