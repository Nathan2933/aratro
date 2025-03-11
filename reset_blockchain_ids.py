#!/usr/bin/env python3
"""
Script to reset blockchain IDs in the database.
This script must be run within the Flask application context.
"""
import logging
from app import app
from models import Stock, StockRequest, BlockchainTransaction, db

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('reset_blockchain_ids')

def main():
    """Main function to reset blockchain IDs in the database."""
    with app.app_context():
        logger.info("Starting blockchain ID reset...")
        
        # Reset stock blockchain IDs
        stocks = Stock.query.all()
        logger.info(f"Found {len(stocks)} stocks in database")
        
        for stock in stocks:
            stock.blockchain_id = None
            stock.blockchain_tx_hash = None
            logger.info(f"Reset blockchain ID for stock {stock.id}")
        
        # Reset stock request blockchain IDs
        stock_requests = StockRequest.query.all()
        logger.info(f"Found {len(stock_requests)} stock requests in database")
        
        for request in stock_requests:
            request.blockchain_id = None
            request.blockchain_tx_hash = None
            logger.info(f"Reset blockchain ID for stock request {request.id}")
        
        # Delete blockchain transaction records
        transactions = BlockchainTransaction.query.all()
        logger.info(f"Found {len(transactions)} blockchain transactions in database")
        
        for transaction in transactions:
            db.session.delete(transaction)
            logger.info(f"Deleted blockchain transaction {transaction.id}")
        
        # Commit changes to database
        db.session.commit()
        logger.info("Blockchain ID reset completed")

if __name__ == "__main__":
    main() 