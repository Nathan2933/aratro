#!/usr/bin/env python3
"""
Script to manually retry failed stock requests on the blockchain.
This script will:
1. Find all stock requests without blockchain IDs
2. Attempt to create them on the blockchain
3. Update the database with the blockchain IDs
"""
import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from the root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Stock, StockRequest
import app
from blockchain_integration import create_stock_on_blockchain, create_stock_request_on_blockchain

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('retry_stock_requests')

# Load environment variables
load_dotenv()

def retry_stock_request(request_id):
    """Retry a specific stock request."""
    # Get the stock request
    request = StockRequest.query.get(request_id)
    if not request:
        logger.error(f"Stock request {request_id} not found")
        return False
    
    logger.info(f"Retrying stock request {request_id} (Status: {request.status}, Blockchain ID: {request.blockchain_id})")
    
    # If the request already has a blockchain ID, skip it
    if request.blockchain_id:
        logger.info(f"Stock request {request_id} already has blockchain ID {request.blockchain_id}")
        return True
    
    # Get the stock
    stock = Stock.query.get(request.stock_id)
    if not stock:
        logger.error(f"Stock {request.stock_id} not found for request {request_id}")
        return False
    
    logger.info(f"Found stock {stock.id} (Type: {stock.type}, Blockchain ID: {stock.blockchain_id})")
    
    # If the stock doesn't have a blockchain ID, create it first
    if not stock.blockchain_id:
        logger.info(f"Stock {stock.id} doesn't have a blockchain ID, creating it first")
        stock_success = create_stock_on_blockchain(stock.id)
        if not stock_success:
            logger.error(f"Failed to create stock {stock.id} on blockchain")
            return False
        
        # Refresh the stock to get the updated blockchain ID
        db.session.refresh(stock)
        logger.info(f"Stock {stock.id} created on blockchain with ID {stock.blockchain_id}")
    
    # Create the stock request on the blockchain
    request_success = create_stock_request_on_blockchain(request.id)
    if not request_success:
        logger.error(f"Failed to create stock request {request.id} on blockchain")
        return False
    
    # Refresh the request to get the updated blockchain ID
    db.session.refresh(request)
    logger.info(f"Stock request {request.id} created on blockchain with ID {request.blockchain_id}")
    
    return True

def retry_recent_requests(days=7):
    """Retry all stock requests from the last X days that don't have blockchain IDs."""
    # Calculate the cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Find all stock requests without blockchain IDs from the last X days
    requests = StockRequest.query.filter(
        StockRequest.blockchain_id.is_(None),
        StockRequest.created_at >= cutoff_date
    ).order_by(StockRequest.created_at.desc()).all()
    
    logger.info(f"Found {len(requests)} stock requests without blockchain IDs from the last {days} days")
    
    success_count = 0
    for request in requests:
        try:
            success = retry_stock_request(request.id)
            if success:
                success_count += 1
        except Exception as e:
            logger.error(f"Error retrying stock request {request.id}: {e}")
            continue
    
    logger.info(f"Successfully retried {success_count} out of {len(requests)} stock requests")
    return success_count

def retry_all_requests():
    """Retry all stock requests that don't have blockchain IDs."""
    # Find all stock requests without blockchain IDs
    requests = StockRequest.query.filter(
        StockRequest.blockchain_id.is_(None)
    ).order_by(StockRequest.created_at.desc()).all()
    
    logger.info(f"Found {len(requests)} stock requests without blockchain IDs")
    
    success_count = 0
    for request in requests:
        try:
            success = retry_stock_request(request.id)
            if success:
                success_count += 1
        except Exception as e:
            logger.error(f"Error retrying stock request {request.id}: {e}")
            continue
    
    logger.info(f"Successfully retried {success_count} out of {len(requests)} stock requests")
    return success_count

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Retry failed stock requests on the blockchain')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--request-id', type=int, help='Retry a specific stock request')
    group.add_argument('--recent', type=int, default=7, help='Retry all stock requests from the last X days (default: 7)')
    group.add_argument('--all', action='store_true', help='Retry all stock requests')
    
    args = parser.parse_args()
    
    # Initialize Flask app
    flask_app = app.Flask(__name__)
    
    # Database configuration
    local_db_url = os.environ.get('LOCAL_DB_URL')
    supabase_url = os.environ.get('SUPABASE_DB_URL')

    # Use local database if specified, otherwise use Supabase
    if local_db_url and os.environ.get('USE_LOCAL_DB', 'false').lower() == 'true':
        logger.info("Using LOCAL database")
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = local_db_url
    elif supabase_url:
        logger.info("Using SUPABASE database")
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = supabase_url
    else:
        logger.error("No database URL found in environment variables")
        return 1
    
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(flask_app)
    
    with flask_app.app_context():
        try:
            if args.request_id:
                logger.info(f"Retrying stock request {args.request_id}")
                success = retry_stock_request(args.request_id)
                return 0 if success else 1
            elif args.all:
                logger.info("Retrying all stock requests")
                success_count = retry_all_requests()
                return 0 if success_count > 0 else 1
            else:
                logger.info(f"Retrying stock requests from the last {args.recent} days")
                success_count = retry_recent_requests(args.recent)
                return 0 if success_count > 0 else 1
        except Exception as e:
            logger.error(f"Error retrying stock requests: {e}")
            return 1

if __name__ == "__main__":
    sys.exit(main()) 