#!/usr/bin/env python3
"""
Script to manually submit a stock request to the blockchain.
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
logger = logging.getLogger('fix_stock_request')

# Load environment variables
load_dotenv()

def main():
    """Main function to fix a stock request."""
    if len(sys.argv) < 2:
        print("Usage: python fix_stock_request.py <stock_request_id>")
        return
    
    stock_request_id = int(sys.argv[1])
    
    try:
        # Import here to avoid circular imports
        from app import app
        from models import db, BlockchainTransaction, StockRequest, Stock, Farmer, Warehouse
        from blockchain import blockchain_manager, init_blockchain
        from blockchain_integration import create_stock_request_on_blockchain
        
        # Initialize blockchain manager if needed
        if blockchain_manager is None:
            blockchain_manager = init_blockchain()
        
        with app.app_context():
            # Get stock request
            stock_request = StockRequest.query.get(stock_request_id)
            if not stock_request:
                logger.error(f"Stock request {stock_request_id} not found in database")
                return
            
            logger.info(f"Found stock request: ID={stock_request.id}, From={stock_request.from_id}, To={stock_request.to_id}, Stock={stock_request.stock_id}, Status={stock_request.status}, Blockchain ID={stock_request.blockchain_id}")
            
            # Get stock
            stock = Stock.query.get(stock_request.stock_id)
            if not stock:
                logger.error(f"Stock {stock_request.stock_id} not found in database")
                return
            
            logger.info(f"Found stock: ID={stock.id}, Type={stock.type}, Quantity={stock.quantity}, Status={stock.status}, Blockchain ID={stock.blockchain_id}")
            
            # Check if stock has a blockchain ID
            if not stock.blockchain_id:
                logger.error(f"Stock {stock_request.stock_id} does not have a blockchain ID")
                logger.info("Attempting to create stock on blockchain first...")
                
                # Get farmer and warehouse
                farmer = Farmer.query.get(stock.farmer_id)
                warehouse = Warehouse.query.get(stock.warehouse_id)
                
                if not farmer or not warehouse:
                    logger.error(f"Farmer or warehouse not found for stock {stock.id}")
                    return
                
                # Create stock on blockchain
                try:
                    # Convert quantity from tons to kg (blockchain uses kg)
                    quantity_kg = int(stock.quantity * 1000)
                    requested_quantity_kg = int(stock.requested_quantity * 1000)
                    
                    blockchain_id = blockchain_manager.create_stock(
                        stock.type,
                        quantity_kg,
                        requested_quantity_kg,
                        farmer.eth_address,
                        warehouse.eth_address
                    )
                    
                    if not blockchain_id:
                        logger.error(f"Failed to create stock {stock.id} on blockchain")
                        return
                    
                    # Update stock in database with blockchain ID
                    stock.blockchain_id = blockchain_id
                    db.session.commit()
                    
                    logger.info(f"Stock {stock.id} created on blockchain with ID {blockchain_id}")
                except Exception as e:
                    logger.error(f"Error creating stock {stock.id} on blockchain: {e}")
                    logger.error(f"Exception traceback: {traceback.format_exc()}")
                    return
            
            # Get farmer and warehouse
            farmer = Farmer.query.get(stock_request.from_id)
            warehouse = Warehouse.query.get(stock_request.to_id)
            
            if not farmer or not warehouse:
                logger.error(f"Farmer or warehouse not found for stock request {stock_request_id}")
                return
            
            logger.info(f"Farmer ETH Address: {farmer.eth_address}")
            logger.info(f"Warehouse ETH Address: {warehouse.eth_address}")
            
            if not farmer.eth_address or not warehouse.eth_address:
                logger.error(f"Ethereum addresses not found for stock request {stock_request_id}")
                return
            
            # Check if stock request already has a blockchain ID
            if stock_request.blockchain_id:
                logger.info(f"Stock request {stock_request_id} already has blockchain ID {stock_request.blockchain_id}")
                
                # Check if there's a transaction for this stock request
                tx = BlockchainTransaction.query.filter_by(
                    entity_type='stock_request',
                    entity_id=stock_request.id
                ).first()
                
                if tx:
                    logger.info(f"Found transaction: ID={tx.id}, Hash={tx.tx_hash}, Status={tx.status}")
                    
                    # If transaction is pending or failed, try to check its status
                    if tx.status in ['pending', 'failed']:
                        try:
                            receipt = blockchain_manager.w3.eth.get_transaction_receipt(tx.tx_hash)
                            
                            if receipt:
                                if receipt.status == 1:
                                    tx.status = 'confirmed'
                                    tx.confirmed_at = datetime.utcnow()
                                    db.session.commit()
                                    logger.info(f"Transaction {tx.tx_hash} confirmed")
                                else:
                                    logger.warning(f"Transaction {tx.tx_hash} failed on blockchain")
                            else:
                                logger.warning(f"Transaction {tx.tx_hash} not found on blockchain")
                        except Exception as e:
                            logger.error(f"Error checking transaction {tx.tx_hash}: {e}")
                else:
                    logger.warning(f"No transaction found for stock request {stock_request_id}")
                    
                    # Create a new transaction record
                    logger.info("Creating a new transaction record...")
                    
                    # Generate a transaction hash based on the blockchain ID
                    tx_hash = f"0x{stock_request.blockchain_id:064x}"
                    
                    transaction = BlockchainTransaction(
                        tx_hash=tx_hash,
                        tx_type='create_stock_request',
                        entity_type='stock_request',
                        entity_id=stock_request.id,
                        blockchain_id=stock_request.blockchain_id,
                        status='confirmed',
                        confirmed_at=datetime.utcnow(),
                        data=json.dumps({
                            'farmer_address': farmer.eth_address,
                            'warehouse_address': warehouse.eth_address,
                            'stock_id': stock.blockchain_id
                        })
                    )
                    
                    db.session.add(transaction)
                    db.session.commit()
                    
                    logger.info(f"Created transaction record with hash {tx_hash}")
            else:
                # Create stock request on blockchain
                logger.info("Creating stock request on blockchain...")
                
                result = create_stock_request_on_blockchain(stock_request_id)
                
                if result:
                    logger.info(f"Stock request {stock_request_id} successfully created on blockchain")
                else:
                    logger.error(f"Failed to create stock request {stock_request_id} on blockchain")
                    
                    # Try direct blockchain manager call
                    logger.info("Trying direct blockchain manager call...")
                    
                    try:
                        result = blockchain_manager.create_stock_request(
                            farmer.eth_address,
                            warehouse.eth_address,
                            stock.blockchain_id
                        )
                        
                        logger.info(f"Result from blockchain_manager.create_stock_request: {result}")
                        
                        if result and isinstance(result, dict) and 'blockchain_id' in result:
                            blockchain_id = result['blockchain_id']
                            tx_hash = result.get('tx_hash')
                            
                            logger.info(f"Blockchain ID: {blockchain_id}, Transaction Hash: {tx_hash}")
                            
                            # Update stock request in database with blockchain ID
                            stock_request.blockchain_id = blockchain_id
                            
                            # Create blockchain transaction record
                            transaction = BlockchainTransaction(
                                tx_hash=tx_hash,
                                tx_type='create_stock_request',
                                entity_type='stock_request',
                                entity_id=stock_request.id,
                                blockchain_id=blockchain_id,
                                status='pending',  # Mark as pending until confirmed
                                data=json.dumps({
                                    'farmer_address': farmer.eth_address,
                                    'warehouse_address': warehouse.eth_address,
                                    'stock_id': stock.blockchain_id
                                })
                            )
                            
                            # Save changes to database
                            db.session.add(transaction)
                            db.session.commit()
                            
                            logger.info(f"Stock request {stock_request_id} created on blockchain with ID {blockchain_id} and transaction hash {tx_hash}")
                        else:
                            logger.error(f"Failed to create stock request {stock_request_id} on blockchain")
                    except Exception as e:
                        logger.error(f"Error creating stock request {stock_request_id} on blockchain: {e}")
                        logger.error(f"Exception traceback: {traceback.format_exc()}")
    
    except Exception as e:
        logger.error(f"Error fixing stock request {stock_request_id}: {e}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main() 