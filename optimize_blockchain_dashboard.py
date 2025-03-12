#!/usr/bin/env python3
"""
Script to optimize the blockchain dashboard by resetting the database and ensuring fast data transfer.
This script combines multiple operations:
1. Reset the database
2. Reset blockchain IDs
3. Reset any aborted transactions
4. Sync data to the blockchain
"""
import os
import sys
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('optimize_blockchain_dashboard')

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

def optimize_blockchain_dashboard():
    """Main function to optimize the blockchain dashboard."""
    start_time = datetime.now()
    logger.info("Starting blockchain dashboard optimization...")
    
    # Step 1: Reset the database
    if not run_script('reset_db.py', 'Database reset'):
        logger.error("Failed to reset database. Aborting optimization.")
        return False
    
    # Step 2: Reset blockchain IDs
    if not run_script('reset_blockchain_ids.py', 'Blockchain ID reset'):
        logger.error("Failed to reset blockchain IDs. Aborting optimization.")
        return False
    
    # Step 3: Reset any aborted transactions
    if not run_script('reset_db_transactions.py', 'Database transaction reset'):
        logger.error("Failed to reset database transactions. Continuing anyway...")
    
    # Step 4: Sync data to the blockchain
    if not run_script('sync_blockchain.py', 'Blockchain sync'):
        logger.error("Failed to sync data to blockchain. Continuing anyway...")
    
    # Calculate total time
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Blockchain dashboard optimization completed in {duration:.2f} seconds")
    
    # Provide instructions for running the application
    logger.info("To run the application with the transaction checker, execute:")
    logger.info("./run_app_with_checker.sh")
    
    return True

if __name__ == "__main__":
    logger.info("This script will reset ALL data in the database and optimize the blockchain dashboard.")
    logger.info("Are you sure you want to continue? (yes/no)")
    
    confirmation = input().strip().lower()
    if confirmation == "yes":
        optimize_blockchain_dashboard()
    else:
        logger.info("Blockchain dashboard optimization cancelled.") 