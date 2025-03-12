#!/usr/bin/env python3
"""
Script to reset the database and optimize the blockchain dashboard.
This script combines both optimization scripts to:
1. Reset the database
2. Reset blockchain IDs
3. Reset any aborted transactions
4. Sync data to the blockchain
5. Optimize database indexes
6. Optimize query performance
7. Clear any stuck pending transactions
8. Run the blockchain transaction checker
"""
import os
import sys
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('reset_and_optimize_blockchain')

def run_script(script_name, description):
    """Run a Python script and log the output."""
    logger.info(f"Running {description}...")
    try:
        result = subprocess.run(['python', script_name], 
                               capture_output=True, 
                               text=True, 
                               check=True)
        logger.info(f"{description} completed successfully")
        logger.debug(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"{description} failed with error code {e.returncode}")
        logger.error(e.stderr)
        return False

def reset_and_optimize_blockchain():
    """Main function to reset and optimize the blockchain dashboard."""
    start_time = datetime.now()
    logger.info("Starting blockchain reset and optimization...")
    
    # Step 1: Run the database reset script
    if not run_script('optimize_blockchain_dashboard.py', 'Database reset and blockchain sync'):
        logger.error("Failed to reset database and sync blockchain. Aborting optimization.")
        return False
    
    # Step 2: Run the blockchain transfer optimization script
    if not run_script('optimize_blockchain_transfer.py', 'Blockchain transfer optimization'):
        logger.error("Failed to optimize blockchain transfer. Continuing anyway...")
    
    # Calculate total time
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Blockchain reset and optimization completed in {duration:.2f} seconds")
    
    # Provide instructions for running the application
    logger.info("To run the application with the transaction checker, execute:")
    logger.info("./run_app_with_checker.sh")
    
    return True

if __name__ == "__main__":
    logger.info("This script will reset ALL data in the database and optimize the blockchain dashboard.")
    logger.info("Are you sure you want to continue? (yes/no)")
    
    confirmation = input().strip().lower()
    if confirmation == "yes":
        reset_and_optimize_blockchain()
    else:
        logger.info("Blockchain reset and optimization cancelled.") 