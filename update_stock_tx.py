#!/usr/bin/env python3
"""
Script to update the stock record with the transaction hash.
"""
import sys
from app import app
from models import db, Stock, BlockchainTransaction

def main():
    """Main function to update the stock record with the transaction hash."""
    if len(sys.argv) < 2:
        print("Usage: python update_stock_tx.py <stock_id>")
        return
    
    stock_id = int(sys.argv[1])
    
    with app.app_context():
        stock = Stock.query.get(stock_id)
        if not stock:
            print(f"Stock {stock_id} not found in database")
            return
        
        # Find the latest blockchain transaction for this stock
        transaction = BlockchainTransaction.query.filter_by(
            entity_type='stock',
            entity_id=stock_id,
            status='confirmed'
        ).order_by(BlockchainTransaction.created_at.desc()).first()
        
        if not transaction:
            print(f"No confirmed blockchain transaction found for stock {stock_id}")
            return
        
        # Update the stock record with the transaction hash
        stock.blockchain_tx_hash = transaction.tx_hash
        db.session.commit()
        
        print(f"Stock {stock_id} updated with transaction hash: {transaction.tx_hash}")
        print(f"Blockchain ID: {stock.blockchain_id}")

if __name__ == "__main__":
    main() 