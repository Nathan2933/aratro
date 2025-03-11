# Python 3.13 Compatibility for Aratro

This document explains how to run the Aratro application with Python 3.13, which requires some additional setup due to compatibility issues with certain dependencies.

## Issue

Python 3.13 removed the `getargspec` function from the `inspect` module, which is used by the `parsimonious` library (a dependency of `web3.py`). Additionally, the `pkg_resources` module (part of `setuptools`) is not installed by default in Python 3.13 virtual environments.

## Solution

### 1. Create a Python 3.13 Virtual Environment

```bash
python3.13 -m venv venv_py313
```

### 2. Install Required Packages

```bash
source venv_py313/bin/activate
pip install -r requirements.txt
pip install setuptools
```

### 3. Patch the Parsimonious Library

Create a script to patch the `parsimonious` library to use `getfullargspec` instead of `getargspec`:

```python
#!/usr/bin/env python3
import os
import sys
import inspect
from pathlib import Path

def find_parsimonious_expressions():
    """Find the parsimonious expressions.py file in the site-packages directory."""
    for path in sys.path:
        if 'site-packages' in path:
            expressions_path = Path(path) / 'parsimonious' / 'expressions.py'
            if expressions_path.exists():
                return expressions_path
    return None

def patch_parsimonious(file_path):
    """Patch the parsimonious expressions.py file to use getfullargspec instead of getargspec."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace getargspec with getfullargspec
    if 'from inspect import getargspec' in content:
        content = content.replace('from inspect import getargspec', 'from inspect import getfullargspec as getargspec')
        print(f"Patched {file_path}")
        
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    else:
        print(f"Could not find 'from inspect import getargspec' in {file_path}")
        return False

def main():
    expressions_path = find_parsimonious_expressions()
    if expressions_path:
        print(f"Found parsimonious expressions.py at {expressions_path}")
        if patch_parsimonious(expressions_path):
            print("Successfully patched parsimonious to work with Python 3.13")
        else:
            print("Failed to patch parsimonious")
    else:
        print("Could not find parsimonious expressions.py")

if __name__ == "__main__":
    main()
```

Run the patch script:

```bash
chmod +x fix_parsimonious.py
source venv_py313/bin/activate
python fix_parsimonious.py
```

### 4. Run the Application

Create a script to run the application with Python 3.13:

```bash
#!/bin/bash

# Activate the Python 3.13 virtual environment
source venv_py313/bin/activate

# Make sure we're using the correct Python version
echo "Using Python: $(which python)"
echo "Python version: $(python --version)"

# Run the application
python app.py
```

Make the script executable and run it:

```bash
chmod +x run_app_py313.sh
./run_app_py313.sh
```

## Verification

The application should now be running with Python 3.13. You can verify this by checking the running processes:

```bash
ps aux | grep python | grep app.py
```

And by accessing the application in your browser at http://localhost:8080.

## Notes

- This solution is specific to Python 3.13 and may need to be adjusted for future Python versions.
- The patch for the `parsimonious` library is a temporary workaround until the library is updated to be compatible with Python 3.13.
- If you encounter any issues, try running the application with Python 3.11 using the `run_app.sh` script. 