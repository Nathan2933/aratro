#!/bin/bash

# Activate the virtual environment
source venv_py311/bin/activate

# Make sure we're using the correct Python version
echo "Using Python: $(which python)"
echo "Python version: $(python --version)"

# Run the application
python app.py 