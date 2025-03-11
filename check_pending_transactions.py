#!/usr/bin/env python3
"""
Script to check and update the status of pending blockchain transactions.
This script should be run periodically to update the status of pending transactions.
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('check_pending_transactions')

# Add the parent directory to the path so we can import from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def main():
    """Main function to check pending transactions."""
    try:
        # Import here to avoid circular imports
        from app import app
        from models import db, BlockchainTransaction
        from blockchain import blockchain_manager, init_blockchain
        
        # Initialize blockchain manager if needed
        if blockchain_manager is None:
            blockchain_manager = init_blockchain()
        
        with app.app_context():
            # Get pending transactions
            pending_transactions = BlockchainTransaction.query.filter_by(status='pending').all()
            logger.info(f"Found {len(pending_transactions)} pending transactions")
            
            # Check each transaction
            for tx in pending_transactions:
                try:
                    logger.info(f"Checking transaction {tx.tx_hash}")
                    
                    # Check if transaction exists on blockchain
                    try:
                        # Get transaction receipt
                        receipt = blockchain_manager.w3.eth.get_transaction_receipt(tx.tx_hash)
                        
                        if receipt:
                            # Transaction exists, update status
                            if receipt.status == 1:
                                tx.status = 'confirmed'
                                tx.confirmed_at = datetime.utcnow()
                                logger.info(f"Transaction {tx.tx_hash} confirmed")
                            else:
                                tx.status = 'failed'
                                logger.warning(f"Transaction {tx.tx_hash} failed")
                        else:
                            # Transaction not found, but might still be pending
                            # Check if it's been pending for too long (more than 1 hour)
                            if datetime.utcnow() - tx.created_at > timedelta(hours=1):
                                tx.status = 'failed'
                                logger.warning(f"Transaction {tx.tx_hash} not found after 1 hour, marking as failed")
                    except Exception as e:
                        logger.error(f"Error checking transaction {tx.tx_hash}: {e}")
                        
                        # If transaction not found and it's been pending for too long, mark as failed
                        if "not found" in str(e).lower() and datetime.utcnow() - tx.created_at > timedelta(hours=1):
                            tx.status = 'failed'
                            logger.warning(f"Transaction {tx.tx_hash} not found after 1 hour, marking as failed")
                
                except Exception as e:
                    logger.error(f"Error processing transaction {tx.id}: {e}")
            
            # Commit changes
            db.session.commit()
            logger.info("Transaction status update completed")
    
    except Exception as e:
        logger.error(f"Error checking pending transactions: {e}")

if __name__ == "__main__":
    main() 