#!/usr/bin/env python3
"""
Script to test the blockchain connection.
This script will:
1. Connect to the blockchain
2. Get the current block number
3. Print the connection status
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from the root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blockchain import blockchain_manager, init_blockchain
from models import db, Farmer, Warehouse, Stock, StockRequest
import app

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_blockchain_connection')

# Load environment variables
load_dotenv()

def test_connection():
    """Test the connection to the blockchain."""
    try:
        # Initialize blockchain manager
        if blockchain_manager is None:
            logger.info("Initializing blockchain manager...")
            bm = init_blockchain()
        else:
            logger.info("Using existing blockchain manager...")
            bm = blockchain_manager
        
        if not bm:
            logger.error("Failed to initialize blockchain manager")
            return False
        
        # Test connection
        try:
            # Try to get the block number to check connection
            block_number = bm.w3.eth.block_number
            logger.info(f"Connected to blockchain. Current block number: {block_number}")
        except Exception as e:
            logger.error(f"Not connected to blockchain: {e}")
            return False
        
        # Get contract address
        contract_address = bm.contract_address
        logger.info(f"Contract address: {contract_address}")
        
        # Check if contract is deployed
        if not contract_address:
            logger.error("Contract not deployed")
            return False
        
        # Check if contract is accessible
        try:
            total_stocks = bm.get_total_stocks()
            logger.info(f"Total stocks on blockchain: {total_stocks}")
            
            total_requests = bm.get_total_stock_requests()
            logger.info(f"Total stock requests on blockchain: {total_requests}")
        except Exception as e:
            logger.error(f"Error accessing contract: {e}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error testing blockchain connection: {e}")
        return False

def check_ethereum_addresses():
    """Check if farmers and warehouses have Ethereum addresses."""
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
        return False
    
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(flask_app)
    
    with flask_app.app_context():
        # Check farmers
        farmers = Farmer.query.all()
        logger.info(f"Found {len(farmers)} farmers")
        
        missing_eth_farmers = [f for f in farmers if not f.eth_address]
        if missing_eth_farmers:
            logger.error(f"{len(missing_eth_farmers)} farmers missing Ethereum addresses")
            for farmer in missing_eth_farmers[:5]:  # Show first 5
                logger.error(f"Farmer ID {farmer.id}, Name: {farmer.name}")
        else:
            logger.info("All farmers have Ethereum addresses")
        
        # Check warehouses
        warehouses = Warehouse.query.all()
        logger.info(f"Found {len(warehouses)} warehouses")
        
        missing_eth_warehouses = [w for w in warehouses if not w.eth_address]
        if missing_eth_warehouses:
            logger.error(f"{len(missing_eth_warehouses)} warehouses missing Ethereum addresses")
            for warehouse in missing_eth_warehouses[:5]:  # Show first 5
                logger.error(f"Warehouse ID {warehouse.id}, Name: {warehouse.name}")
        else:
            logger.info("All warehouses have Ethereum addresses")
        
        # Check recent stock requests
        recent_requests = StockRequest.query.order_by(StockRequest.created_at.desc()).limit(5).all()
        logger.info(f"Found {len(recent_requests)} recent stock requests")
        
        for req in recent_requests:
            logger.info(f"Request ID: {req.id}, Status: {req.status}, Blockchain ID: {req.blockchain_id}")
            
            # Check stock
            stock = Stock.query.get(req.stock_id)
            if stock:
                logger.info(f"  Stock ID: {stock.id}, Type: {stock.type}, Blockchain ID: {stock.blockchain_id}")
            else:
                logger.error(f"  Stock not found for request {req.id}")
            
            # Check farmer
            farmer = Farmer.query.get(req.from_id)
            if farmer:
                logger.info(f"  Farmer ID: {farmer.id}, Name: {farmer.name}, ETH Address: {farmer.eth_address}")
            else:
                logger.error(f"  Farmer not found for request {req.id}")
            
            # Check warehouse
            warehouse = Warehouse.query.get(req.to_id)
            if warehouse:
                logger.info(f"  Warehouse ID: {warehouse.id}, Name: {warehouse.name}, ETH Address: {warehouse.eth_address}")
            else:
                logger.error(f"  Warehouse not found for request {req.id}")

def main():
    """Main function to run the script."""
    logger.info("Testing blockchain connection...")
    connection_ok = test_connection()
    
    if connection_ok:
        logger.info("Blockchain connection test passed")
        
        # Check Ethereum addresses
        logger.info("Checking Ethereum addresses...")
        check_ethereum_addresses()
    else:
        logger.error("Blockchain connection test failed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 