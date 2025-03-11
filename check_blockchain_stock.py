#!/usr/bin/env python3
"""
Script to check if a stock exists on the blockchain.
"""
import logging
import sys
from app import app
from models import Stock
from blockchain import blockchain_manager, init_blockchain

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('check_blockchain_stock')

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

if __name__ == "__main__":
    main() 