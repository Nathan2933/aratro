#!/usr/bin/env python3
"""
Script to verify if stocks and stock requests exist on the blockchain.
This script must be run within the Flask application context.
"""
import logging
from app import app
from models import Stock, StockRequest, db
from blockchain import blockchain_manager, init_blockchain

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('verify_blockchain')

def main():
    """Main function to verify data on the blockchain."""
    with app.app_context():
        logger.info("Starting blockchain verification...")
        
        # Initialize blockchain manager if needed
        if blockchain_manager is None:
            init_blockchain()
        
        # Check stocks with blockchain IDs
        stocks_with_blockchain_id = Stock.query.filter(Stock.blockchain_id.is_not(None)).all()
        logger.info(f"Found {len(stocks_with_blockchain_id)} stocks with blockchain IDs")
        
        valid_stocks = 0
        invalid_stocks = 0
        
        # Verify each stock
        for stock in stocks_with_blockchain_id:
            try:
                # Convert blockchain_id to integer
                blockchain_id = int(stock.blockchain_id)
                
                # Check if stock exists on blockchain
                stock_data = blockchain_manager.contract.functions.stocks(blockchain_id).call()
                
                # If we get here, the stock exists
                logger.info(f"Stock {stock.id} with blockchain ID {blockchain_id} exists on blockchain")
                valid_stocks += 1
            except Exception as e:
                logger.error(f"Stock {stock.id} with blockchain ID {stock.blockchain_id} does not exist on blockchain: {e}")
                invalid_stocks += 1
        
        logger.info(f"Valid stocks: {valid_stocks}/{len(stocks_with_blockchain_id)}")
        logger.info(f"Invalid stocks: {invalid_stocks}/{len(stocks_with_blockchain_id)}")
        
        # Check stock requests with blockchain IDs
        requests_with_blockchain_id = StockRequest.query.filter(StockRequest.blockchain_id.is_not(None)).all()
        logger.info(f"Found {len(requests_with_blockchain_id)} stock requests with blockchain IDs")
        
        valid_requests = 0
        invalid_requests = 0
        
        # Verify each stock request
        for request in requests_with_blockchain_id:
            try:
                # Convert blockchain_id to integer
                blockchain_id = int(request.blockchain_id)
                
                # Check if stock request exists on blockchain
                request_data = blockchain_manager.contract.functions.stockRequests(blockchain_id).call()
                
                # If we get here, the stock request exists
                logger.info(f"Stock request {request.id} with blockchain ID {blockchain_id} exists on blockchain")
                valid_requests += 1
            except Exception as e:
                logger.error(f"Stock request {request.id} with blockchain ID {request.blockchain_id} does not exist on blockchain: {e}")
                invalid_requests += 1
        
        logger.info(f"Valid stock requests: {valid_requests}/{len(requests_with_blockchain_id)}")
        logger.info(f"Invalid stock requests: {invalid_requests}/{len(requests_with_blockchain_id)}")
        
        # Check stock requests without blockchain IDs
        requests_without_blockchain_id = StockRequest.query.filter(StockRequest.blockchain_id.is_(None)).all()
        logger.info(f"Found {len(requests_without_blockchain_id)} stock requests without blockchain IDs")
        
        # Check if referenced stocks exist and have valid blockchain IDs
        for request in requests_without_blockchain_id:
            try:
                stock = Stock.query.get(request.stock_id)
                if not stock:
                    logger.error(f"Stock {request.stock_id} referenced by stock request {request.id} does not exist in database")
                    continue
                
                if not stock.blockchain_id:
                    logger.error(f"Stock {request.stock_id} referenced by stock request {request.id} does not have a blockchain ID")
                    continue
                
                # Convert blockchain_id to integer
                blockchain_id = int(stock.blockchain_id)
                
                # Check if stock exists on blockchain
                try:
                    stock_data = blockchain_manager.contract.functions.stocks(blockchain_id).call()
                    logger.info(f"Stock {stock.id} with blockchain ID {blockchain_id} referenced by stock request {request.id} exists on blockchain")
                except Exception as e:
                    logger.error(f"Stock {stock.id} with blockchain ID {stock.blockchain_id} referenced by stock request {request.id} does not exist on blockchain: {e}")
            except Exception as e:
                logger.error(f"Error checking stock for stock request {request.id}: {e}")
        
        logger.info("Blockchain verification completed")

if __name__ == "__main__":
    main() 