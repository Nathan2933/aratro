#!/usr/bin/env python3
"""
Script to check blockchain transactions in the database.
"""
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('check_transactions')

# Load environment variables
load_dotenv()

def main():
    """Main function to check transactions."""
    try:
        # Import here to avoid circular imports
        from app import app
        from models import db, BlockchainTransaction, StockRequest
        
        with app.app_context():
            # Get total transactions
            total_transactions = BlockchainTransaction.query.count()
            logger.info(f"Total transactions in database: {total_transactions}")
            
            # Get recent transactions
            recent_transactions = BlockchainTransaction.query.order_by(BlockchainTransaction.created_at.desc()).limit(5).all()
            logger.info(f"Recent transactions: {len(recent_transactions)}")
            
            for tx in recent_transactions:
                logger.info(f"ID: {tx.id}, Hash: {tx.tx_hash[:10]}..., Type: {tx.tx_type}, Status: {tx.status}, Created: {tx.created_at}")
            
            # Get recent stock requests
            recent_requests = StockRequest.query.order_by(StockRequest.created_at.desc()).limit(5).all()
            logger.info(f"Recent stock requests: {len(recent_requests)}")
            
            for req in recent_requests:
                logger.info(f"ID: {req.id}, From: {req.from_id}, To: {req.to_id}, Stock: {req.stock_id}, Status: {req.status}, Blockchain ID: {req.blockchain_id}, Created: {req.created_at}")
    
    except Exception as e:
        logger.error(f"Error checking transactions: {e}")

if __name__ == "__main__":
    main() 