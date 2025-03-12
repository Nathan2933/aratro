#!/usr/bin/env python3
"""
Script to retry failed blockchain transactions.
This script will:
1. Find all pending blockchain transactions
2. Attempt to retry them
3. Update their status accordingly
"""
import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import from the root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, BlockchainTransaction, StockRequest, Stock, RationStockRequest, Notification
from app import create_app
from blockchain_integration import (
    update_stock_status_on_blockchain,
    update_stock_request_status_on_blockchain,
    update_ration_stock_request_status_on_blockchain,
    create_blockchain_notification
)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('retry_blockchain_transactions')

def retry_pending_transactions():
    """Find and retry all pending blockchain transactions."""
    # Get all pending transactions that are at least 5 minutes old
    cutoff_time = datetime.utcnow() - timedelta(minutes=5)
    pending_txs = BlockchainTransaction.query.filter(
        BlockchainTransaction.status == 'pending',
        BlockchainTransaction.created_at < cutoff_time
    ).all()
    
    logger.info(f"Found {len(pending_txs)} pending blockchain transactions to retry")
    
    for tx in pending_txs:
        logger.info(f"Retrying transaction {tx.id} of type {tx.tx_type} for {tx.entity_type} {tx.entity_id}")
        
        # Extract data from the transaction
        try:
            data = json.loads(tx.data) if tx.data else {}
        except json.JSONDecodeError:
            logger.error(f"Could not parse data for transaction {tx.id}: {tx.data}")
            continue
        
        # Retry based on transaction type
        success = False
        if tx.tx_type == 'update_stock_status':
            status = data.get('status')
            if status and tx.entity_id:
                success = update_stock_status_on_blockchain(tx.entity_id, status)
        
        elif tx.tx_type == 'update_stock_request_status':
            status = data.get('status')
            if status and tx.entity_id:
                success = update_stock_request_status_on_blockchain(tx.entity_id, status)
        
        elif tx.tx_type == 'update_ration_stock_request_status':
            status = data.get('status')
            notes = data.get('admin_notes', '')
            if status and tx.entity_id:
                success = update_ration_stock_request_status_on_blockchain(tx.entity_id, status, notes)
        
        # Update transaction status
        if success:
            tx.status = 'confirmed'
            tx.confirmed_at = datetime.utcnow()
            logger.info(f"Successfully retried transaction {tx.id}")
            
            # Send notification to relevant users
            if tx.entity_type == 'stock_request':
                request = StockRequest.query.get(tx.entity_id)
                if request:
                    # Notify farmer
                    if request.stock and request.stock.farmer:
                        create_blockchain_notification(
                            user_id=request.stock.farmer.user_id,
                            title='Blockchain Update Successful',
                            message=f'Your stock request status has been successfully updated on the blockchain after retry.',
                            notification_type='blockchain_retry_success'
                        )
                    
                    # Notify warehouse
                    if request.to_id:
                        warehouse = Warehouse.query.get(request.to_id)
                        if warehouse:
                            create_blockchain_notification(
                                user_id=warehouse.user_id,
                                title='Blockchain Update Successful',
                                message=f'Stock request {request.id} status has been successfully updated on the blockchain after retry.',
                                notification_type='blockchain_retry_success'
                            )
            
            elif tx.entity_type == 'ration_stock_request':
                request = RationStockRequest.query.get(tx.entity_id)
                if request:
                    # Notify ration shop
                    if request.ration_shop:
                        create_blockchain_notification(
                            user_id=request.ration_shop.user_id,
                            title='Blockchain Update Successful',
                            message=f'Your stock request status has been successfully updated on the blockchain after retry.',
                            notification_type='blockchain_retry_success'
                        )
                    
                    # Notify warehouse
                    if request.warehouse:
                        create_blockchain_notification(
                            user_id=request.warehouse.user_id,
                            title='Blockchain Update Successful',
                            message=f'Ration shop request {request.id} status has been successfully updated on the blockchain after retry.',
                            notification_type='blockchain_retry_success'
                        )
        else:
            # Increment retry count
            tx.retry_count = (tx.retry_count or 0) + 1
            
            # If we've retried too many times, mark as failed
            if tx.retry_count >= 5:
                tx.status = 'failed'
                logger.warning(f"Transaction {tx.id} failed after {tx.retry_count} retries")
                
                # Send notification to relevant users about permanent failure
                if tx.entity_type == 'stock_request':
                    request = StockRequest.query.get(tx.entity_id)
                    if request:
                        # Notify farmer
                        if request.stock and request.stock.farmer:
                            create_blockchain_notification(
                                user_id=request.stock.farmer.user_id,
                                title='Blockchain Update Failed Permanently',
                                message=f'Your stock request status could not be updated on the blockchain after multiple retries. Please contact support.',
                                notification_type='blockchain_permanent_failure'
                            )
                        
                        # Notify warehouse
                        if request.to_id:
                            warehouse = Warehouse.query.get(request.to_id)
                            if warehouse:
                                create_blockchain_notification(
                                    user_id=warehouse.user_id,
                                    title='Blockchain Update Failed Permanently',
                                    message=f'Stock request {request.id} status could not be updated on the blockchain after multiple retries. Please contact support.',
                                    notification_type='blockchain_permanent_failure'
                                )
                
                # Notify admin about permanent failure
                create_blockchain_notification(
                    user_id=1,  # Assuming admin user ID is 1
                    title='Blockchain Update Failed Permanently',
                    message=f'Transaction {tx.id} for {tx.entity_type} {tx.entity_id} failed after {tx.retry_count} retries. Manual intervention required.',
                    notification_type='blockchain_permanent_failure'
                )
            else:
                logger.warning(f"Transaction {tx.id} retry failed, will try again later (attempt {tx.retry_count})")
        
        db.session.commit()
    
    return len(pending_txs)

def main():
    """Main function to run the script."""
    app = create_app()
    with app.app_context():
        try:
            num_retried = retry_pending_transactions()
            logger.info(f"Retried {num_retried} pending blockchain transactions")
        except Exception as e:
            logger.error(f"Error retrying blockchain transactions: {e}")
            return 1
    return 0

if __name__ == "__main__":
    sys.exit(main()) 