#!/bin/bash
# Script to run the application and transaction checker together

# Change to the directory containing the script
cd "$(dirname "$0")"

# Start the transaction checker in the background
echo "Starting transaction checker..."
./run_transaction_checker.sh &
CHECKER_PID=$!

# Start the application
echo "Starting application..."
python app.py

# When the application exits, kill the transaction checker
echo "Application exited, stopping transaction checker..."
kill $CHECKER_PID 