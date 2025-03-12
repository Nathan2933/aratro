#!/bin/bash

# Script to run the blockchain transaction retry process periodically
# This script will run the retry_blockchain_transactions.py script every 5 minutes

# Change to the directory containing the script
cd "$(dirname "$0")"

# Set up logging
LOG_FILE="blockchain_retry.log"
echo "Starting blockchain retry process at $(date)" >> $LOG_FILE

# Run the retry process in a loop
while true; do
    echo "Running blockchain retry process at $(date)" >> $LOG_FILE
    python retry_blockchain_transactions.py >> $LOG_FILE 2>&1
    
    # Check the exit code
    if [ $? -ne 0 ]; then
        echo "ERROR: Blockchain retry process failed at $(date)" >> $LOG_FILE
    fi
    
    # Wait for 5 minutes before running again
    echo "Waiting for 5 minutes before next run..." >> $LOG_FILE
    sleep 300
done 