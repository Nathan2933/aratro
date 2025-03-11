#!/usr/bin/env python3
"""
Script to debug blockchain issues.
"""
import os
import sys
import logging
import json
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('debug_blockchain')

# Load environment variables
load_dotenv()

def check_blockchain_connection():
    """Check if the blockchain is accessible."""
    try:
        from blockchain import blockchain_manager, init_blockchain
        
        # Initialize blockchain manager if needed
        if blockchain_manager is None:
            blockchain_manager = init_blockchain()
        
        # Check connection
        block_number = blockchain_manager.w3.eth.block_number
        logger.info(f"Connected to blockchain at {blockchain_manager.w3.provider.endpoint_uri}, current block: {block_number}")
        
        # Check account
        account = blockchain_manager.account
        balance = blockchain_manager.w3.eth.get_balance(account)
        
        # Convert wei to ether
        try:
            balance_eth = blockchain_manager.w3.fromWei(balance, 'ether')
        except AttributeError:
            # Manual conversion as fallback
            balance_eth = float(balance) / 1e18  # 1 ether = 10^18 wei
        
        logger.info(f"Using account: {account}, balance: {balance_eth} ETH")
        
        # Check contract
        contract_address = blockchain_manager.contract_address
        logger.info(f"Contract address: {contract_address}")
        
        # Check if contract exists
        code = blockchain_manager.w3.eth.get_code(contract_address)
        if code and len(code) > 2:  # '0x' is returned for non-existent contracts
            logger.info(f"Contract exists at {contract_address}")
        else:
            logger.error(f"No contract found at {contract_address}")
        
        return True
    except Exception as e:
        logger.error(f"Error checking blockchain connection: {e}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        return False

def test_create_stock():
    """Test creating a stock on the blockchain."""
    try:
        from app import app
        from models import db, Stock, Farmer, Warehouse
        from blockchain import blockchain_manager, init_blockchain
        from blockchain_integration import create_stock_on_blockchain
        
        # Initialize blockchain manager if needed
        if blockchain_manager is None:
            blockchain_manager = init_blockchain()
        
        with app.app_context():
            # Get a farmer and warehouse
            farmer = Farmer.query.first()
            warehouse = Warehouse.query.first()
            
            if not farmer or not warehouse:
                logger.error("No farmer or warehouse found in database")
                return False
            
            logger.info(f"Using farmer: ID={farmer.id}, Name={farmer.name}, ETH Address={farmer.eth_address}")
            logger.info(f"Using warehouse: ID={warehouse.id}, Name={warehouse.name}, ETH Address={warehouse.eth_address}")
            
            # Create a test stock
            stock = Stock(
                type="Test Crop",
                quantity=1.0,
                requested_quantity=1.0,
                status="pending",
                farmer_id=farmer.id,
                warehouse_id=warehouse.id
            )
            
            db.session.add(stock)
            db.session.commit()
            
            logger.info(f"Created test stock: ID={stock.id}")
            
            # Create stock on blockchain
            result = create_stock_on_blockchain(stock.id)
            
            if result:
                logger.info(f"Successfully created stock on blockchain")
                return True
            else:
                logger.error(f"Failed to create stock on blockchain")
                return False
    except Exception as e:
        logger.error(f"Error testing stock creation: {e}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        return False

def test_create_stock_request():
    """Test creating a stock request on the blockchain."""
    try:
        from app import app
        from models import db, Stock, StockRequest, Farmer, Warehouse
        from blockchain import blockchain_manager, init_blockchain
        from blockchain_integration import create_stock_on_blockchain, create_stock_request_on_blockchain
        
        # Initialize blockchain manager if needed
        if blockchain_manager is None:
            blockchain_manager = init_blockchain()
        
        with app.app_context():
            # Get a farmer and warehouse
            farmer = Farmer.query.first()
            warehouse = Warehouse.query.first()
            
            if not farmer or not warehouse:
                logger.error("No farmer or warehouse found in database")
                return False
            
            logger.info(f"Using farmer: ID={farmer.id}, Name={farmer.name}, ETH Address={farmer.eth_address}")
            logger.info(f"Using warehouse: ID={warehouse.id}, Name={warehouse.name}, ETH Address={warehouse.eth_address}")
            
            # Create a test stock
            stock = Stock(
                type="Test Crop",
                quantity=1.0,
                requested_quantity=1.0,
                status="pending",
                farmer_id=farmer.id,
                warehouse_id=warehouse.id
            )
            
            db.session.add(stock)
            db.session.commit()
            
            logger.info(f"Created test stock: ID={stock.id}")
            
            # Create stock on blockchain
            stock_result = create_stock_on_blockchain(stock.id)
            
            if not stock_result:
                logger.error(f"Failed to create stock on blockchain")
                return False
            
            # Refresh stock to get blockchain_id
            db.session.refresh(stock)
            logger.info(f"Stock created on blockchain with ID: {stock.blockchain_id}")
            
            # Create a test stock request
            stock_request = StockRequest(
                from_id=farmer.id,
                to_id=warehouse.id,
                stock_id=stock.id,
                status="pending"
            )
            
            db.session.add(stock_request)
            db.session.commit()
            
            logger.info(f"Created test stock request: ID={stock_request.id}")
            
            # Create stock request on blockchain
            request_result = create_stock_request_on_blockchain(stock_request.id)
            
            if request_result:
                logger.info(f"Successfully created stock request on blockchain")
                return True
            else:
                logger.error(f"Failed to create stock request on blockchain")
                return False
    except Exception as e:
        logger.error(f"Error testing stock request creation: {e}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        return False

def check_private_key():
    """Check if the private key is valid."""
    try:
        from web3 import Web3
        from eth_account import Account
        
        private_key = os.environ.get('PRIVATE_KEY')
        
        if not private_key:
            logger.error("No private key found in environment variables")
            return False
        
        if not private_key.startswith('0x'):
            private_key = f'0x{private_key}'
        
        # Try to derive an account from the private key
        try:
            account = Account.from_key(private_key)
            address = account.address
            logger.info(f"Valid private key, derived address: {address}")
            return True
        except Exception as e:
            logger.error(f"Invalid private key: {e}")
            return False
    except Exception as e:
        logger.error(f"Error checking private key: {e}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        return False

def main():
    """Main function to debug blockchain issues."""
    if len(sys.argv) < 2:
        print("Usage: python debug_blockchain.py <command>")
        print("Commands:")
        print("  connection - Check blockchain connection")
        print("  stock - Test creating a stock on the blockchain")
        print("  request - Test creating a stock request on the blockchain")
        print("  key - Check if the private key is valid")
        print("  all - Run all tests")
        return
    
    command = sys.argv[1]
    
    if command == "connection":
        check_blockchain_connection()
    elif command == "stock":
        test_create_stock()
    elif command == "request":
        test_create_stock_request()
    elif command == "key":
        check_private_key()
    elif command == "all":
        logger.info("========== CHECKING BLOCKCHAIN CONNECTION ==========")
        connection_result = check_blockchain_connection()
        
        logger.info("========== CHECKING PRIVATE KEY ==========")
        key_result = check_private_key()
        
        if connection_result and key_result:
            logger.info("========== TESTING STOCK CREATION ==========")
            stock_result = test_create_stock()
            
            if stock_result:
                logger.info("========== TESTING STOCK REQUEST CREATION ==========")
                request_result = test_create_stock_request()
                
                if request_result:
                    logger.info("All tests passed successfully!")
                else:
                    logger.error("Stock request creation test failed")
            else:
                logger.error("Stock creation test failed")
        else:
            if not connection_result:
                logger.error("Blockchain connection test failed")
            if not key_result:
                logger.error("Private key test failed")
    else:
        print(f"Unknown command: {command}")
        print("Use 'python debug_blockchain.py' without arguments to see available commands")

if __name__ == "__main__":
    main() 