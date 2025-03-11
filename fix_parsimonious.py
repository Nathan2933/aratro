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