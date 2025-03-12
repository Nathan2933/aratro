"""
Script to integrate the blockchain with the existing stock creation process.
This script provides functions to:
1. Create a stock on the blockchain when a stock is created in the database
2. Update a stock's status on the blockchain when it's updated in the database
3. Create a stock request on the blockchain when a request is created in the database
4. Update a stock request's status on the blockchain when it's updated in the database
"""
import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import hashlib
import secrets
import traceback
import time

# Add the parent directory to the path so we can import from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, Stock, StockRequest, WarehouseRequest, RationStockRequest, BlockchainTransaction, Farmer, Warehouse, RationShop, Notification
from blockchain import blockchain_manager, init_blockchain

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('blockchain_integration')

# Load environment variables
load_dotenv()

# Initialize blockchain manager
if blockchain_manager is None:
    blockchain_manager = init_blockchain()

def create_stock_on_blockchain(stock_id):
    """Create a stock on the blockchain when a stock is created in the database."""
    try:
        logger.info(f"Starting to create stock {stock_id} on blockchain")
        
        # Get stock from database
        stock = Stock.query.get(stock_id)
        if not stock:
            logger.error(f"Stock {stock_id} not found in database")
            return False
        
        logger.info(f"Found stock: ID={stock.id}, Type={stock.type}, Quantity={stock.quantity}, Status={stock.status}")
        
        # Get farmer and warehouse
        farmer = Farmer.query.get(stock.farmer_id)
        warehouse = Warehouse.query.get(stock.warehouse_id)
        
        if not farmer:
            logger.error(f"Farmer {stock.farmer_id} not found in database")
            return False
            
        if not warehouse:
            logger.error(f"Warehouse {stock.warehouse_id} not found in database")
            return False
        
        # Get Ethereum addresses
        farmer_address = farmer.eth_address
        warehouse_address = warehouse.eth_address
        
        logger.info(f"Farmer ETH Address: {farmer_address}")
        logger.info(f"Warehouse ETH Address: {warehouse_address}")
        
        if not farmer_address or not warehouse_address:
            logger.error(f"Ethereum addresses not found for stock {stock_id}")
            return False
        
        # Convert quantity from tons to kg (blockchain uses kg)
        quantity_kg = int(stock.quantity * 1000)
        requested_quantity_kg = int(stock.requested_quantity * 1000)
        
        logger.info(f"Calling blockchain_manager.create_stock with type={stock.type}, quantity={quantity_kg}, requested_quantity={requested_quantity_kg}")
        
        # Create stock on blockchain
        result = blockchain_manager.create_stock(
            stock.type,
            quantity_kg,
            requested_quantity_kg,
            farmer_address,
            warehouse_address
        )
        
        logger.info(f"Result from blockchain_manager.create_stock: {result}")
        
        if not result:
            logger.error(f"Failed to create stock {stock_id} on blockchain - result is None or False")
            return False
            
        if not isinstance(result, dict) and not isinstance(result, int):
            logger.error(f"Failed to create stock {stock_id} on blockchain - unexpected result type: {type(result)}")
            return False
        
        # Handle both old and new return formats
        if isinstance(result, dict):
            blockchain_id = result.get('blockchain_id')
            tx_hash = result.get('tx_hash')
            
            if not blockchain_id:
                logger.error(f"Failed to create stock {stock_id} on blockchain - blockchain_id not in result: {result}")
                return False
        else:
            # Old format returns just the blockchain ID
            blockchain_id = result
            
            # Try to get the transaction hash
            try:
                # Get the most recent transaction
                tx_count = blockchain_manager.w3.eth.get_transaction_count(blockchain_manager.account)
                receipt = blockchain_manager.w3.eth.get_transaction_receipt(tx_count - 1)
                tx_hash = receipt.transactionHash.hex()
                logger.info(f"Got transaction hash from receipt: {tx_hash}")
            except Exception as e:
                logger.error(f"Could not get transaction hash: {e}")
                return False
        
        logger.info(f"Blockchain ID: {blockchain_id}, Transaction Hash: {tx_hash}")
        
        # Update stock in database with blockchain ID
        stock.blockchain_id = blockchain_id
        
        # Create blockchain transaction record
        transaction = BlockchainTransaction(
            tx_hash=tx_hash,
            tx_type='create_stock',
            entity_type='stock',
            entity_id=stock.id,
            blockchain_id=blockchain_id,
            status='pending',  # Mark as pending until confirmed
            data=json.dumps({
                'type': stock.type,
                'quantity': stock.quantity,
                'requested_quantity': stock.requested_quantity,
                'farmer_address': farmer_address,
                'warehouse_address': warehouse_address
            })
        )
        
        # Save changes to database
        db.session.add(transaction)
        db.session.commit()
        
        logger.info(f"Stock {stock_id} created on blockchain with ID {blockchain_id} and transaction hash {tx_hash}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating stock {stock_id} on blockchain: {e}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        return False

def update_stock_status_on_blockchain(stock_id, status):
    """Update a stock's status on the blockchain when it's updated in the database."""
    try:
        # Get stock from database
        stock = Stock.query.get(stock_id)
        if not stock:
            logger.error(f"Stock {stock_id} not found in database")
            return False
        
        # Check if stock has a blockchain ID
        if not stock.blockchain_id:
            logger.error(f"Stock {stock_id} does not have a blockchain ID")
            return False
        
        # Update stock status on blockchain
        success = blockchain_manager.update_stock_status(stock.blockchain_id, status)
        
        if not success:
            logger.error(f"Failed to update stock {stock_id} status on blockchain")
            return False
        
        # Create blockchain transaction record
        transaction = BlockchainTransaction(
            tx_hash=blockchain_manager.w3.eth.get_transaction_receipt(blockchain_manager.w3.eth.get_transaction_count(blockchain_manager.account) - 1).transactionHash.hex(),
            tx_type='update_stock_status',
            entity_type='stock',
            entity_id=stock.id,
            blockchain_id=stock.blockchain_id,
            status='confirmed',
            confirmed_at=datetime.utcnow(),
            data=json.dumps({
                'status': status
            })
        )
        
        # Save changes to database
        db.session.add(transaction)
        db.session.commit()
        
        logger.info(f"Stock {stock_id} status updated on blockchain to {status}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating stock {stock_id} status on blockchain: {e}")
        return False

def create_stock_request_on_blockchain(stock_request_id):
    """Create a stock request on the blockchain when a request is created in the database."""
    try:
        logger.info(f"========== STARTING BLOCKCHAIN REQUEST CREATION ==========")
        logger.info(f"Starting to create stock request {stock_request_id} on blockchain")
        
        # Get stock request from database
        stock_request = StockRequest.query.get(stock_request_id)
        if not stock_request:
            logger.error(f"Stock request {stock_request_id} not found in database")
            return False
        
        logger.info(f"Found stock request: ID={stock_request.id}, From={stock_request.from_id}, To={stock_request.to_id}, Stock={stock_request.stock_id}, Status={stock_request.status}")
        
        # Get stock from database
        stock = Stock.query.get(stock_request.stock_id)
        if not stock:
            logger.error(f"Stock {stock_request.stock_id} not found in database")
            return False
        
        logger.info(f"Found stock: ID={stock.id}, Type={stock.type}, Quantity={stock.quantity}, Status={stock.status}, Blockchain ID={stock.blockchain_id}")
        
        # Check if stock has a blockchain ID
        if not stock.blockchain_id:
            logger.error(f"Stock {stock_request.stock_id} does not have a blockchain ID")
            logger.info(f"Attempting to create stock on blockchain first...")
            
            # Create stock on blockchain
            stock_blockchain_success = create_stock_on_blockchain(stock.id)
            if not stock_blockchain_success:
                logger.error(f"Failed to create stock {stock.id} on blockchain")
                return False
            
            # Refresh stock object to get the updated blockchain_id
            db.session.refresh(stock)
            logger.info(f"Stock created on blockchain with ID: {stock.blockchain_id}")
        
        # Get farmer and warehouse Ethereum addresses
        farmer = Farmer.query.get(stock_request.from_id)
        warehouse = Warehouse.query.get(stock_request.to_id)
        
        if not farmer:
            logger.error(f"Farmer {stock_request.from_id} not found in database")
            return False
            
        if not warehouse:
            logger.error(f"Warehouse {stock_request.to_id} not found in database")
            return False
        
        farmer_address = farmer.eth_address
        warehouse_address = warehouse.eth_address
        
        logger.info(f"Farmer ETH Address: {farmer_address}")
        logger.info(f"Warehouse ETH Address: {warehouse_address}")
        
        if not farmer_address or not warehouse_address:
            logger.error(f"Ethereum addresses not found for stock request {stock_request_id}")
            return False
        
        # Create stock request on blockchain
        logger.info(f"Calling blockchain_manager.create_stock_request with farmer_address={farmer_address}, warehouse_address={warehouse_address}, stock_id={stock.blockchain_id}")
        
        try:
            result = blockchain_manager.create_stock_request(
                farmer_address,
                warehouse_address,
                stock.blockchain_id
            )
            
            logger.info(f"Result from blockchain_manager.create_stock_request: {result}")
        except Exception as e:
            logger.error(f"Exception during blockchain_manager.create_stock_request: {e}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            return False
        
        if not result:
            logger.error(f"Failed to create stock request {stock_request_id} on blockchain - result is None or False")
            return False
            
        if not isinstance(result, dict):
            logger.error(f"Failed to create stock request {stock_request_id} on blockchain - result is not a dictionary: {type(result)}")
            return False
            
        if 'blockchain_id' not in result:
            logger.error(f"Failed to create stock request {stock_request_id} on blockchain - blockchain_id not in result: {result}")
            return False
        
        blockchain_id = result['blockchain_id']
        tx_hash = result.get('tx_hash')
        
        logger.info(f"Blockchain ID: {blockchain_id}, Transaction Hash: {tx_hash}")
        
        if not tx_hash:
            logger.error(f"No transaction hash returned for stock request {stock_request_id}")
            return False
        
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
                'farmer_address': farmer_address,
                'warehouse_address': warehouse_address,
                'stock_id': stock.blockchain_id
            })
        )
        
        # Save changes to database
        try:
            db.session.add(transaction)
            db.session.commit()
            logger.info(f"Successfully saved transaction to database")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save transaction to database: {e}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            return False
        
        logger.info(f"Stock request {stock_request_id} created on blockchain with ID {blockchain_id} and transaction hash {tx_hash}")
        logger.info(f"========== BLOCKCHAIN REQUEST CREATION COMPLETED SUCCESSFULLY ==========")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating stock request {stock_request_id} on blockchain: {e}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        logger.error(f"========== BLOCKCHAIN REQUEST CREATION FAILED ==========")
        return False

def update_stock_request_status_on_blockchain(request_id, status):
    """Update a stock request's status on the blockchain when it's updated in the database."""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Get stock request from database
            request = StockRequest.query.get(request_id)
            if not request:
                logger.error(f"Stock request {request_id} not found in database")
                return False
            
            # Check if stock request has a blockchain ID
            if not request.blockchain_id:
                logger.error(f"Stock request {request_id} does not have a blockchain ID")
                return False
            
            # Update stock request status on blockchain
            logger.info(f"Attempting to update stock request {request_id} status to {status} on blockchain (attempt {retry_count + 1}/{max_retries})")
            result = blockchain_manager.update_stock_request_status(request.blockchain_id, status)
            
            if not result or not isinstance(result, dict) or not result.get('success'):
                error_msg = result.get('error', 'Unknown error') if isinstance(result, dict) else 'Unknown error'
                logger.error(f"Failed to update stock request {request_id} status on blockchain: {error_msg}")
                
                # If this is the last retry, create a pending blockchain transaction for later retry
                if retry_count == max_retries - 1:
                    # Create a pending blockchain transaction record for later retry
                    pending_tx = BlockchainTransaction(
                        tx_hash='pending_' + secrets.token_hex(16),
                        tx_type='update_stock_request_status',
                        entity_type='stock_request',
                        entity_id=request.id,
                        blockchain_id=request.blockchain_id,
                        status='pending',
                        data=json.dumps({
                            'status': status,
                            'error': error_msg
                        })
                    )
                    db.session.add(pending_tx)
                    
                    # Create notification for the farmer
                    if request.stock and request.stock.farmer:
                        create_blockchain_notification(
                            user_id=request.stock.farmer.user_id,
                            title='Blockchain Update Pending',
                            message=f'Your stock request status update to "{status}" is pending on the blockchain and will be retried automatically.',
                            notification_type='blockchain_pending'
                        )
                    
                    # Create notification for the warehouse
                    if request.to_id:
                        warehouse = Warehouse.query.get(request.to_id)
                        if warehouse:
                            create_blockchain_notification(
                                user_id=warehouse.user_id,
                                title='Blockchain Update Pending',
                                message=f'Stock request {request_id} status update to "{status}" is pending on the blockchain and will be retried automatically.',
                                notification_type='blockchain_pending'
                            )
                    
                    db.session.commit()
                    logger.info(f"Created pending blockchain transaction for stock request {request_id}")
                
                retry_count += 1
                if retry_count < max_retries:
                    # Wait before retrying (exponential backoff)
                    time.sleep(2 ** retry_count)
                    continue
                return False
            
            tx_hash = result.get('tx_hash')
            if not tx_hash:
                logger.error(f"No transaction hash returned for stock request status update {request_id}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(2 ** retry_count)
                    continue
                return False
            
            # Create blockchain transaction record
            transaction = BlockchainTransaction(
                tx_hash=tx_hash,
                tx_type='update_stock_request_status',
                entity_type='stock_request',
                entity_id=request.id,
                blockchain_id=request.blockchain_id,
                status='pending',  # Mark as pending until confirmed
                data=json.dumps({
                    'status': status
                })
            )
            
            # Save changes to database
            db.session.add(transaction)
            
            # Create notification for the farmer
            if request.stock and request.stock.farmer:
                create_blockchain_notification(
                    user_id=request.stock.farmer.user_id,
                    title='Blockchain Update Successful',
                    message=f'Your stock request status has been updated to "{status}" on the blockchain.',
                    notification_type='blockchain_success'
                )
            
            db.session.commit()
            
            logger.info(f"Stock request {request_id} status updated to {status} on blockchain with transaction hash {tx_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating stock request {request_id} status on blockchain: {e}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            
            retry_count += 1
            if retry_count < max_retries:
                # Wait before retrying (exponential backoff)
                time.sleep(2 ** retry_count)
            else:
                # Create a pending blockchain transaction record for later retry
                try:
                    request = StockRequest.query.get(request_id)
                    if request and request.blockchain_id:
                        pending_tx = BlockchainTransaction(
                            tx_hash='pending_' + secrets.token_hex(16),
                            tx_type='update_stock_request_status',
                            entity_type='stock_request',
                            entity_id=request.id,
                            blockchain_id=request.blockchain_id,
                            status='pending',
                            data=json.dumps({
                                'status': status,
                                'error': str(e)
                            })
                        )
                        db.session.add(pending_tx)
                        
                        # Create notification for the farmer
                        if request.stock and request.stock.farmer:
                            create_blockchain_notification(
                                user_id=request.stock.farmer.user_id,
                                title='Blockchain Update Failed',
                                message=f'Your stock request status update to "{status}" failed on the blockchain but will be retried automatically.',
                                notification_type='blockchain_error'
                            )
                        
                        # Create notification for the warehouse
                        if request.to_id:
                            warehouse = Warehouse.query.get(request.to_id)
                            if warehouse:
                                create_blockchain_notification(
                                    user_id=warehouse.user_id,
                                    title='Blockchain Update Failed',
                                    message=f'Stock request {request_id} status update to "{status}" failed on the blockchain but will be retried automatically.',
                                    notification_type='blockchain_error'
                                )
                        
                        db.session.commit()
                        logger.info(f"Created pending blockchain transaction for stock request {request_id}")
                except Exception as inner_e:
                    logger.error(f"Error creating pending transaction: {inner_e}")
                    db.session.rollback()
                
                return False

def sync_stock_to_blockchain(stock_id):
    """Sync a specific stock to the blockchain.
    
    Args:
        stock_id: The ID of the stock to sync
        
    Returns:
        bool: True if the stock was successfully synced, False otherwise
    """
    try:
        # Get stock from database
        stock = Stock.query.get(stock_id)
        if not stock:
            logger.error(f"Stock {stock_id} not found in database")
            return False
        
        # Check if stock already has a blockchain ID
        if stock.blockchain_id:
            logger.info(f"Stock {stock_id} already has blockchain ID {stock.blockchain_id}")
            return True
        
        # Create stock on blockchain
        result = create_stock_on_blockchain(stock_id)
        if result:
            logger.info(f"Successfully synced stock {stock_id} to blockchain")
            return True
        else:
            logger.error(f"Failed to sync stock {stock_id} to blockchain")
            return False
    except Exception as e:
        logger.error(f"Error syncing stock {stock_id} to blockchain: {e}")
        return False

def sync_existing_stocks_to_blockchain():
    """Sync existing stocks without a blockchain ID to the blockchain."""
    try:
        # Get all stocks without a blockchain ID
        stocks = Stock.query.filter(Stock.blockchain_id.is_(None)).all()
        logger.info(f"Found {len(stocks)} stocks to sync to blockchain")
        
        success_count = 0
        for stock in stocks:
            try:
                # Create stock on blockchain
                result = create_stock_on_blockchain(stock.id)
                if result:
                    success_count += 1
                else:
                    logger.error(f"Failed to sync stock {stock.id} to blockchain")
            except Exception as e:
                logger.error(f"Error syncing stock {stock.id} to blockchain: {e}")
                continue
        
        logger.info(f"Successfully synced {success_count} out of {len(stocks)} stocks to blockchain")
        return success_count
    except Exception as e:
        logger.error(f"Error syncing stocks to blockchain: {e}")
        return 0

def sync_existing_stock_requests_to_blockchain():
    """Sync existing stock requests without a blockchain ID to the blockchain."""
    try:
        # Get all stock requests without a blockchain ID
        stock_requests = StockRequest.query.filter(StockRequest.blockchain_id.is_(None)).all()
        logger.info(f"Found {len(stock_requests)} stock requests to sync to blockchain")
        
        success_count = 0
        for stock_request in stock_requests:
            try:
                # Create stock request on blockchain
                result = create_stock_request_on_blockchain(stock_request.id)
                if result:
                    success_count += 1
                else:
                    logger.error(f"Failed to sync stock request {stock_request.id} to blockchain")
            except Exception as e:
                logger.error(f"Error syncing stock request {stock_request.id} to blockchain: {e}")
                continue
        
        logger.info(f"Successfully synced {success_count} out of {len(stock_requests)} stock requests to blockchain")
        return success_count
    except Exception as e:
        logger.error(f"Error syncing stock requests to blockchain: {e}")
        return 0

def create_ration_stock_request_on_blockchain(request_id):
    """Create a ration stock request on the blockchain when a request is created in the database."""
    try:
        logger.info(f"Starting to create ration stock request {request_id} on blockchain")
        
        # Get request from database
        request = RationStockRequest.query.get(request_id)
        if not request:
            logger.error(f"Ration stock request {request_id} not found in database")
            return False
        
        logger.info(f"Found ration stock request: ID={request.id}, Type={request.stock_type}, Quantity={request.quantity}, Status={request.status}")
        
        # Get ration shop and warehouse
        ration_shop = RationShop.query.get(request.ration_shop_id)
        warehouse = Warehouse.query.get(request.warehouse_id)
        
        if not ration_shop:
            logger.error(f"Ration shop {request.ration_shop_id} not found in database")
            return False
            
        if not warehouse:
            logger.error(f"Warehouse {request.warehouse_id} not found in database")
            return False
        
        # Get Ethereum addresses
        ration_shop_address = ration_shop.eth_address
        warehouse_address = warehouse.eth_address
        
        logger.info(f"Ration Shop ETH Address: {ration_shop_address}")
        logger.info(f"Warehouse ETH Address: {warehouse_address}")
        
        if not ration_shop_address or not warehouse_address:
            logger.error(f"Ethereum addresses not found for ration stock request {request_id}")
            return False
        
        # Convert quantity from tons to kg (blockchain uses kg)
        quantity_kg = int(request.quantity * 1000)
        
        logger.info(f"Calling blockchain_manager.create_ration_stock_request with type={request.stock_type}, quantity={quantity_kg}")
        
        # Create ration stock request on blockchain
        result = blockchain_manager.create_ration_stock_request(
            ration_shop_address,
            warehouse_address,
            request.stock_type,
            quantity_kg,
            request.notes or ""
        )
        
        logger.info(f"Result from blockchain_manager.create_ration_stock_request: {result}")
        
        if not result:
            logger.error(f"Failed to create ration stock request {request_id} on blockchain - result is None or False")
            return False
            
        if not isinstance(result, dict):
            logger.error(f"Failed to create ration stock request {request_id} on blockchain - unexpected result type: {type(result)}")
            return False
        
        # Extract blockchain ID and transaction hash
        blockchain_id = result.get('blockchain_id')
        tx_hash = result.get('tx_hash')
        
        if not blockchain_id or not tx_hash:
            logger.error(f"Failed to extract blockchain ID or transaction hash for ration stock request {request_id}")
            return False
        
        # Update request with blockchain ID and transaction hash
        request.blockchain_id = blockchain_id
        request.blockchain_tx_hash = tx_hash
        
        # Create blockchain transaction record
        transaction = BlockchainTransaction(
            tx_hash=tx_hash,
            tx_type='create_ration_stock_request',
            entity_type='ration_stock_request',
            entity_id=request.id,
            blockchain_id=blockchain_id,
            status='confirmed',
            confirmed_at=datetime.utcnow(),
            data=json.dumps({
                'ration_shop_id': request.ration_shop_id,
                'warehouse_id': request.warehouse_id,
                'stock_type': request.stock_type,
                'quantity': request.quantity,
                'status': request.status
            })
        )
        
        # Save to database
        db.session.add(transaction)
        db.session.commit()
        
        logger.info(f"Successfully created ration stock request {request_id} on blockchain with ID {blockchain_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating ration stock request {request_id} on blockchain: {e}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        db.session.rollback()
        return False

def update_ration_stock_request_status_on_blockchain(request_id, status, admin_notes=""):
    """Update the status of a ration stock request on the blockchain."""
    try:
        logger.info(f"Starting to update ration stock request {request_id} status to {status} on blockchain")
        
        # Get request from database
        request = RationStockRequest.query.get(request_id)
        if not request:
            logger.error(f"Ration stock request {request_id} not found in database")
            return False
        
        # Check if request has a blockchain ID
        if not request.blockchain_id:
            logger.error(f"Ration stock request {request_id} does not have a blockchain ID")
            return False
        
        logger.info(f"Found ration stock request: ID={request.id}, Blockchain ID={request.blockchain_id}, Status={request.status}")
        
        # Update status on blockchain
        result = blockchain_manager.update_ration_stock_request_status(
            request.blockchain_id,
            status,
            admin_notes
        )
        
        logger.info(f"Result from blockchain_manager.update_ration_stock_request_status: {result}")
        
        if not result or not isinstance(result, dict) or not result.get('success'):
            logger.error(f"Failed to update ration stock request {request_id} status on blockchain")
            return False
        
        # Get transaction hash
        tx_hash = result.get('tx_hash')
        if not tx_hash:
            logger.error(f"Failed to extract transaction hash for ration stock request {request_id}")
            return False
        
        # Create blockchain transaction record
        transaction = BlockchainTransaction(
            tx_hash=tx_hash,
            tx_type='update_ration_stock_request_status',
            entity_type='ration_stock_request',
            entity_id=request.id,
            blockchain_id=request.blockchain_id,
            status='confirmed',
            confirmed_at=datetime.utcnow(),
            data=json.dumps({
                'status': status,
                'admin_notes': admin_notes
            })
        )
        
        # Save to database
        db.session.add(transaction)
        db.session.commit()
        
        logger.info(f"Successfully updated ration stock request {request_id} status to {status} on blockchain")
        return True
        
    except Exception as e:
        logger.error(f"Error updating ration stock request {request_id} status on blockchain: {e}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        db.session.rollback()
        return False

def sync_existing_ration_stock_requests_to_blockchain():
    """Sync existing ration stock requests to the blockchain."""
    try:
        logger.info("Starting to sync existing ration stock requests to blockchain")
        
        # Get all ration stock requests that don't have a blockchain ID
        ration_requests = RationStockRequest.query.filter(RationStockRequest.blockchain_id.is_(None)).all()
        
        logger.info(f"Found {len(ration_requests)} ration stock requests without blockchain IDs")
        
        success_count = 0
        for ration_request in ration_requests:
            try:
                logger.info(f"Syncing ration stock request {ration_request.id} to blockchain")
                
                # Create ration stock request on blockchain
                success = create_ration_stock_request_on_blockchain(ration_request.id)
                
                if success:
                    success_count += 1
                    logger.info(f"Successfully synced ration stock request {ration_request.id} to blockchain")
                else:
                    logger.error(f"Failed to sync ration stock request {ration_request.id} to blockchain")
            except Exception as e:
                logger.error(f"Error syncing ration stock request {ration_request.id} to blockchain: {e}")
                logger.error(f"Exception traceback: {traceback.format_exc()}")
        
        logger.info(f"Synced {success_count} out of {len(ration_requests)} ration stock requests to blockchain")
        return success_count
    except Exception as e:
        logger.error(f"Error syncing ration stock requests to blockchain: {e}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        return 0

def create_blockchain_notification(user_id, title, message, notification_type='blockchain'):
    """Create a notification for blockchain events."""
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type
        )
        db.session.add(notification)
        db.session.commit()
        logger.info(f"Created blockchain notification for user {user_id}: {title}")
        return True
    except Exception as e:
        logger.error(f"Error creating blockchain notification: {e}")
        db.session.rollback()
        return False

if __name__ == '__main__':
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python blockchain_integration.py <command> [args]")
        print("Commands:")
        print("  create_stock <stock_id>")
        print("  update_stock_status <stock_id> <status>")
        print("  create_stock_request <request_id>")
        print("  update_stock_request_status <request_id> <status>")
        print("  sync_stocks")
        print("  sync_requests")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'create_stock':
        if len(sys.argv) < 3:
            print("Usage: python blockchain_integration.py create_stock <stock_id>")
            sys.exit(1)
        
        stock_id = int(sys.argv[2])
        success = create_stock_on_blockchain(stock_id)
        sys.exit(0 if success else 1)
    
    elif command == 'update_stock_status':
        if len(sys.argv) < 4:
            print("Usage: python blockchain_integration.py update_stock_status <stock_id> <status>")
            sys.exit(1)
        
        stock_id = int(sys.argv[2])
        status = sys.argv[3]
        success = update_stock_status_on_blockchain(stock_id, status)
        sys.exit(0 if success else 1)
    
    elif command == 'create_stock_request':
        if len(sys.argv) < 3:
            print("Usage: python blockchain_integration.py create_stock_request <request_id>")
            sys.exit(1)
        
        request_id = int(sys.argv[2])
        success = create_stock_request_on_blockchain(request_id)
        sys.exit(0 if success else 1)
    
    elif command == 'update_stock_request_status':
        if len(sys.argv) < 4:
            print("Usage: python blockchain_integration.py update_stock_request_status <request_id> <status>")
            sys.exit(1)
        
        request_id = int(sys.argv[2])
        status = sys.argv[3]
        success = update_stock_request_status_on_blockchain(request_id, status)
        sys.exit(0 if success else 1)
    
    elif command == 'sync_stocks':
        success = sync_existing_stocks_to_blockchain()
        sys.exit(0 if success else 1)
    
    elif command == 'sync_requests':
        success = sync_existing_stock_requests_to_blockchain()
        sys.exit(0 if success else 1)
    
    elif command == 'sync_ration_requests':
        success = sync_existing_ration_stock_requests_to_blockchain()
        sys.exit(0 if success else 1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1) 