#!/usr/bin/env python3
"""
Script to sync a specific stock to the blockchain.
"""
import sys
from app import app
from blockchain_integration import create_stock_on_blockchain

def main():
    """Main function to sync a stock to the blockchain."""
    if len(sys.argv) < 2:
        print("Usage: python sync_stock.py <stock_id>")
        return
    
    stock_id = int(sys.argv[1])
    
    with app.app_context():
        print(f"Syncing stock {stock_id} to blockchain...")
        result = create_stock_on_blockchain(stock_id)
        
        if result:
            print(f"Stock {stock_id} successfully synced to blockchain")
        else:
            print(f"Failed to sync stock {stock_id} to blockchain")

if __name__ == "__main__":
    main() 