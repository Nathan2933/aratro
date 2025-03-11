#!/usr/bin/env python3
"""
Script to check a transaction in the database and blockchain.
"""
import logging
import sys
from app import app
from models import BlockchainTransaction
from blockchain import blockchain_manager, init_blockchain

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('check_transaction')

def main():
    """Main function to check a transaction."""
    if len(sys.argv) < 2:
        print("Usage: python check_transaction.py <tx_hash>")
        return
    
    tx_hash = sys.argv[1]
    
    with app.app_context():
        logger.info(f"Checking transaction {tx_hash}")
        
        # Initialize blockchain manager if needed
        if blockchain_manager is None:
            init_blockchain()
        
        # Check transaction in database
        db_tx = BlockchainTransaction.query.filter_by(tx_hash=tx_hash).first()
        
        if db_tx:
            print("Transaction found in database:")
            print(f"ID: {db_tx.id}")
            print(f"Hash: {db_tx.tx_hash}")
            print(f"Type: {db_tx.tx_type}")
            print(f"Entity Type: {db_tx.entity_type}")
            print(f"Entity ID: {db_tx.entity_id}")
            print(f"Blockchain ID: {db_tx.blockchain_id}")
            print(f"Status: {db_tx.status}")
            print(f"Created At: {db_tx.created_at}")
            print(f"Confirmed At: {db_tx.confirmed_at}")
            print(f"Data: {db_tx.data}")
        else:
            print(f"Transaction {tx_hash} not found in database")
            return
        
        # Check transaction in blockchain
        try:
            tx = blockchain_manager.w3.eth.get_transaction(tx_hash)
            tx_receipt = blockchain_manager.w3.eth.get_transaction_receipt(tx_hash)
            
            print("\nTransaction found in blockchain:")
            print(f"Block Number: {tx.get('blockNumber')}")
            print(f"From: {tx.get('from')}")
            print(f"To: {tx.get('to')}")
            print(f"Value: {blockchain_manager.w3.from_wei(tx.get('value', 0), 'ether')} ETH")
            print(f"Gas Price: {blockchain_manager.w3.from_wei(tx.get('gasPrice', 0), 'gwei')} Gwei")
            print(f"Gas: {tx.get('gas')}")
            print(f"Nonce: {tx.get('nonce')}")
            print(f"Status: {'Success' if tx_receipt.get('status') == 1 else 'Failed'}")
        except Exception as e:
            print(f"\nTransaction {tx_hash} not found in blockchain: {e}")

if __name__ == "__main__":
    main() 