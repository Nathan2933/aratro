#!/usr/bin/env python3
"""
Script to check if a stock exists on the blockchain.
"""
import logging
import sys
from app import app
from models import Stock
from blockchain import blockchain_manager, init_blockchain
from blockchain import BlockchainManager
import os
from web3 import Web3
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('check_blockchain_stock')

# Load environment variables
load_dotenv()

def main():
    """Main function to check a stock on the blockchain."""
    if len(sys.argv) < 2:
        print("Usage: python check_blockchain_stock.py <blockchain_id>")
        return
    
    blockchain_id = int(sys.argv[1])
    
    with app.app_context():
        logger.info(f"Checking stock with blockchain ID {blockchain_id}")
        
        # Initialize blockchain manager if needed
        if blockchain_manager is None:
            init_blockchain()
        
        # Check if stock exists on blockchain
        try:
            # First try using the contract's getStock function
            stock_data = blockchain_manager.get_stock(blockchain_id)
            print(f"Stock found on blockchain using get_stock:")
            print(f"ID: {stock_data['id']}")
            print(f"Crop Type: {stock_data['crop_type']}")
            print(f"Quantity: {stock_data['quantity']}")
            print(f"Requested Quantity: {stock_data['requested_quantity']}")
            print(f"Status: {stock_data['status']}")
            print(f"Farmer: {stock_data['farmer']}")
            print(f"Warehouse: {stock_data['warehouse']}")
            print(f"Timestamp: {stock_data['timestamp']}")
            print(f"Updated At: {stock_data['updated_at']}")
        except Exception as e:
            print(f"Error getting stock with get_stock: {e}")
            
            # Try using the contract's stocks mapping directly
            try:
                stock_data = blockchain_manager.contract.functions.stocks(blockchain_id).call()
                print(f"\nStock found on blockchain using direct mapping:")
                print(f"ID: {stock_data[0]}")
                print(f"Crop Type: {stock_data[1]}")
                print(f"Quantity: {stock_data[2] / 1000}")  # Convert from kg to tons
                print(f"Requested Quantity: {stock_data[3] / 1000}")  # Convert from kg to tons
                
                status_map = {
                    0: 'pending',
                    1: 'stored',
                    2: 'rejected',
                    3: 'transferred'
                }
                print(f"Status: {status_map.get(stock_data[4], 'unknown')}")
                print(f"Farmer: {stock_data[5]}")
                print(f"Warehouse: {stock_data[6]}")
                print(f"Timestamp: {stock_data[7]}")
                print(f"Updated At: {stock_data[8]}")
            except Exception as e:
                print(f"Error getting stock with direct mapping: {e}")
                print(f"Stock with blockchain ID {blockchain_id} not found on blockchain")
        
        # Check if any stocks in the database reference this blockchain ID
        # Convert blockchain_id to string since it's stored as a string in the database
        stocks = Stock.query.filter_by(blockchain_id=str(blockchain_id)).all()
        if stocks:
            print(f"\nFound {len(stocks)} stocks in database with blockchain ID {blockchain_id}:")
            for stock in stocks:
                print(f"Stock ID: {stock.id}")
                print(f"Type: {stock.type}")
                print(f"Quantity: {stock.quantity}")
                print(f"Status: {stock.status}")
                print(f"Blockchain TX Hash: {stock.blockchain_tx_hash}")
                print(f"Created At: {stock.created_at}")
                print(f"Updated At: {stock.updated_at}")
        else:
            print(f"\nNo stocks in database with blockchain ID {blockchain_id}")

def check_blockchain_stock():
    """Check the blockchain for stock records and test creating a new stock."""
    with app.app_context():
        bm = BlockchainManager()
        
        print(f"Using account: {bm.account}")
        print(f"Contract address: {bm.contract_address}")
        
        # Check total stocks
        total_stocks = bm.get_total_stocks()
        print(f"Total stocks on blockchain: {total_stocks}")
        
        # Check total stock requests
        total_requests = bm.get_total_stock_requests()
        print(f"Total stock requests on blockchain: {total_requests}")
        
        # Try to create a test stock
        print("\nAttempting to create a test stock...")
        
        # Get the account from private key for testing
        private_key = os.environ.get('PRIVATE_KEY')
        if not private_key:
            print("No private key found in environment variables")
            return
        
        if not private_key.startswith('0x'):
            private_key = f'0x{private_key}'
        
        from eth_account import Account
        account = Account.from_key(private_key)
        address = account.address
        
        # Create a test stock
        result = bm.create_stock(
            crop_type="Test Crop",
            quantity=1000,  # 1 ton = 1000 kg
            requested_quantity=1000,
            farmer_address=address,
            warehouse_address=address
        )
        
        if result:
            print(f"Test stock created successfully!")
            print(f"Blockchain ID: {result['blockchain_id']}")
            print(f"Transaction hash: {result['tx_hash']}")
            
            # Verify the stock was created
            new_total_stocks = bm.get_total_stocks()
            print(f"New total stocks on blockchain: {new_total_stocks}")
            
            if new_total_stocks > total_stocks:
                print("Stock count increased, stock was created successfully!")
            else:
                print("Stock count did not increase, stock creation may have failed!")
        else:
            print("Failed to create test stock!")

if __name__ == "__main__":
    check_blockchain_stock() 