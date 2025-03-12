#!/bin/bash
# Script to run the application and transaction checker together

# Change to the directory containing the script
cd "$(dirname "$0")"

# Start the transaction checker in the background
echo "Starting transaction checker..."
./run_transaction_checker.sh &
CHECKER_PID=$!

# Start the blockchain retry process in the background
echo "Starting blockchain retry process..."
./run_blockchain_retry.sh &
RETRY_PID=$!

# Start the application
echo "Starting application..."
python app.py

# When the application exits, kill the transaction checker and blockchain retry process
echo "Application exited, stopping background processes..."
kill $CHECKER_PID
kill $RETRY_PID 