#!/bin/bash
# Script to run the check_pending_transactions.py script periodically

# Change to the directory containing the script
cd "$(dirname "$0")"

# Set the interval in seconds (default: 5 minutes)
INTERVAL=${1:-300}

echo "Starting transaction checker with interval of $INTERVAL seconds"

while true; do
    echo "$(date): Checking pending transactions..."
    python3 check_pending_transactions.py
    echo "$(date): Sleeping for $INTERVAL seconds..."
    sleep $INTERVAL
done 