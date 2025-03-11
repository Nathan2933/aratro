#!/usr/bin/env python3
"""
Script to sync existing data to the blockchain.
This script must be run within the Flask application context.
"""
import logging
from app import app
from blockchain_integration import sync_existing_stocks_to_blockchain, sync_existing_stock_requests_to_blockchain, sync_stock_to_blockchain
from models import Stock, StockRequest, db

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('sync_blockchain')

def main():
    """Main function to sync data to the blockchain."""
    with app.app_context():
        logger.info("Starting blockchain sync...")
        
        # First, check if there are any stocks without blockchain IDs
        stocks_to_sync = Stock.query.filter(Stock.blockchain_id.is_(None)).all()
        logger.info(f"Found {len(stocks_to_sync)} stocks without blockchain IDs")
        
        # Sync stocks
        if stocks_to_sync:
            logger.info("Syncing stocks to blockchain...")
            stock_success_count = sync_existing_stocks_to_blockchain()
            if stock_success_count > 0:
                logger.info(f"Successfully synced {stock_success_count} stocks to blockchain")
            else:
                logger.error("Failed to sync any stocks to blockchain")
        else:
            logger.info("No stocks need to be synced to blockchain")
        
        # Verify that all stocks referenced by stock requests have blockchain IDs
        stock_requests_to_sync = StockRequest.query.filter(StockRequest.blockchain_id.is_(None)).all()
        logger.info(f"Found {len(stock_requests_to_sync)} stock requests without blockchain IDs")
        
        # Check if all referenced stocks have blockchain IDs
        missing_stock_ids = []
        for request in stock_requests_to_sync:
            stock = Stock.query.get(request.stock_id)
            if not stock or not stock.blockchain_id:
                missing_stock_ids.append(request.stock_id)
        
        if missing_stock_ids:
            logger.warning(f"Found {len(missing_stock_ids)} stocks referenced by stock requests that don't have blockchain IDs")
            logger.warning(f"Stock IDs: {missing_stock_ids}")
            logger.warning("These stocks must be synced first before syncing stock requests")
            
            # Try to sync these stocks specifically
            synced_count = 0
            for stock_id in missing_stock_ids:
                stock = Stock.query.get(stock_id)
                if stock and not stock.blockchain_id:
                    logger.info(f"Attempting to sync stock {stock_id} to blockchain...")
                    if sync_stock_to_blockchain(stock_id):
                        synced_count += 1
            
            logger.info(f"Successfully synced {synced_count} out of {len(missing_stock_ids)} missing stocks to blockchain")
            
            # Check again if there are still missing stock IDs
            missing_stock_ids = []
            for request in stock_requests_to_sync:
                stock = Stock.query.get(request.stock_id)
                if not stock or not stock.blockchain_id:
                    missing_stock_ids.append(request.stock_id)
        
        # Sync stock requests only if there are no missing stock blockchain IDs
        if not missing_stock_ids:
            logger.info("Syncing stock requests to blockchain...")
            request_success_count = sync_existing_stock_requests_to_blockchain()
            if request_success_count > 0:
                logger.info(f"Successfully synced {request_success_count} stock requests to blockchain")
            else:
                logger.error("Failed to sync any stock requests to blockchain")
        else:
            logger.error("Cannot sync stock requests until all referenced stocks have blockchain IDs")
            logger.error(f"Still missing blockchain IDs for stocks: {missing_stock_ids}")
        
        logger.info("Blockchain sync completed")

if __name__ == "__main__":
    main() 