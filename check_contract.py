#!/usr/bin/env python3
"""
Script to check the total number of stocks in the contract.
"""
import logging
from app import app
from blockchain import blockchain_manager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('check_contract')

def main():
    """Main function to check the contract."""
    with app.app_context():
        logger.info("Checking contract...")
        
        # Get total stocks
        try:
            total_stocks = blockchain_manager.get_total_stocks()
            logger.info(f"Total stocks in contract: {total_stocks}")
        except Exception as e:
            logger.error(f"Error getting total stocks: {e}")
        
        # Get total stock requests
        try:
            total_requests = blockchain_manager.get_total_stock_requests()
            logger.info(f"Total stock requests in contract: {total_requests}")
        except Exception as e:
            logger.error(f"Error getting total stock requests: {e}")
        
        # Try to get a stock
        try:
            stock_id = 1
            stock = blockchain_manager.get_stock(stock_id)
            logger.info(f"Stock {stock_id}: {stock}")
        except Exception as e:
            logger.error(f"Error getting stock {stock_id}: {e}")
        
        logger.info("Contract check completed")

if __name__ == "__main__":
    main() 