#!/usr/bin/env python3
"""
Script to check the blockchain ID of a stock in the database.
"""
import sys
from app import app
from models import db, Stock, BlockchainTransaction

def main():
    """Main function to check the blockchain ID of a stock."""
    if len(sys.argv) < 2:
        print("Usage: python check_stock.py <stock_id>")
        return
    
    stock_id = int(sys.argv[1])
    
    with app.app_context():
        stock = Stock.query.get(stock_id)
        if not stock:
            print(f"Stock {stock_id} not found in database")
            return
        
        print(f"Stock {stock_id} details:")
        print(f"  Type: {stock.type}")
        print(f"  Quantity: {stock.quantity}")
        print(f"  Status: {stock.status}")
        print(f"  Blockchain ID: {stock.blockchain_id}")
        print(f"  Blockchain TX Hash: {stock.blockchain_tx_hash}")
        
        # Check for blockchain transactions
        transactions = BlockchainTransaction.query.filter_by(
            entity_type='stock',
            entity_id=stock_id
        ).all()
        
        print(f"\nFound {len(transactions)} blockchain transactions:")
        for tx in transactions:
            print(f"  Transaction ID: {tx.id}")
            print(f"  TX Hash: {tx.tx_hash}")
            print(f"  TX Type: {tx.tx_type}")
            print(f"  Status: {tx.status}")
            print(f"  Blockchain ID: {tx.blockchain_id}")
            print(f"  Created At: {tx.created_at}")
            print(f"  Confirmed At: {tx.confirmed_at}")
            print(f"  Data: {tx.data}")
            print("")

if __name__ == "__main__":
    main() 