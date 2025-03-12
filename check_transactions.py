#!/usr/bin/env python3
"""
Script to check blockchain transactions in the database.
"""
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from models import db, BlockchainTransaction
import app

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('check_transactions')

# Load environment variables
load_dotenv()

def main():
    with app.app.app_context():
        # Count total transactions
        total_transactions = BlockchainTransaction.query.count()
        print(f'Total transactions: {total_transactions}')
        
        # Get recent transactions
        print('\nRecent transactions:')
        recent_transactions = BlockchainTransaction.query.order_by(
            BlockchainTransaction.created_at.desc()
        ).limit(5).all()
        
        if recent_transactions:
            for tx in recent_transactions:
                print(f'ID: {tx.id}, Hash: {tx.tx_hash}, Type: {tx.tx_type}, Status: {tx.status}, Created: {tx.created_at}')
        else:
            print("No transactions found in the database.")

if __name__ == '__main__':
    main() 