#!/usr/bin/env python3
"""
Script to optimize blockchain data transfer speed.
This script modifies the database configuration to ensure fast data transfer to the blockchain dashboard.
"""
import os
import sys
import logging
from datetime import datetime, timedelta
import time
import subprocess

# Add the parent directory to the path so we can import from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import BlockchainTransaction
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('optimize_blockchain_transfer')

def optimize_database_indexes():
    """Optimize database indexes for faster blockchain data retrieval."""
    with app.app_context():
        logger.info("Optimizing database indexes for blockchain data...")
        
        # Create indexes on frequently accessed columns
        try:
            # Index for blockchain transactions by status
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_blockchain_transactions_status 
                ON blockchain_transactions (status)
            """))
            
            # Index for blockchain transactions by created_at for faster sorting
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_blockchain_transactions_created_at 
                ON blockchain_transactions (created_at DESC)
            """))
            
            # Index for stocks by blockchain_id
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_stocks_blockchain_id 
                ON stocks (blockchain_id)
            """))
            
            # Index for stock requests by blockchain_id
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_stock_requests_blockchain_id 
                ON stock_requests (blockchain_id)
            """))
            
            # Index for ration stock requests by blockchain_id
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ration_stock_requests_blockchain_id 
                ON ration_stock_requests (blockchain_id)
            """))
            
            db.session.commit()
            logger.info("Database indexes created successfully")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating database indexes: {str(e)}")
            return False
        
        return True

def optimize_query_performance():
    """Optimize database query performance for blockchain data."""
    with app.app_context():
        logger.info("Optimizing database query performance...")
        
        try:
            # Analyze tables to update statistics for the query planner
            db.session.execute(text("ANALYZE blockchain_transactions"))
            db.session.execute(text("ANALYZE stocks"))
            db.session.execute(text("ANALYZE stock_requests"))
            db.session.execute(text("ANALYZE ration_stock_requests"))
            
            # Vacuum tables to reclaim storage and update statistics
            db.session.execute(text("VACUUM ANALYZE blockchain_transactions"))
            db.session.execute(text("VACUUM ANALYZE stocks"))
            db.session.execute(text("VACUUM ANALYZE stock_requests"))
            db.session.execute(text("VACUUM ANALYZE ration_stock_requests"))
            
            db.session.commit()
            logger.info("Database query performance optimized successfully")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error optimizing query performance: {str(e)}")
            return False
        
        return True

def clear_pending_transactions():
    """Clear any stuck pending transactions."""
    with app.app_context():
        logger.info("Clearing stuck pending transactions...")
        
        try:
            # Find transactions that have been pending for more than 1 hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            stuck_transactions = BlockchainTransaction.query.filter_by(status='pending')\
                .filter(BlockchainTransaction.created_at < one_hour_ago).all()
            
            if stuck_transactions:
                logger.info(f"Found {len(stuck_transactions)} stuck pending transactions")
                
                # Update status to 'failed'
                for tx in stuck_transactions:
                    tx.status = 'failed'
                    tx.updated_at = datetime.utcnow()
                    logger.info(f"Marked transaction {tx.id} as failed")
                
                db.session.commit()
                logger.info("Stuck transactions cleared successfully")
            else:
                logger.info("No stuck pending transactions found")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error clearing stuck transactions: {str(e)}")
            return False
        
        return True

def run_blockchain_checker():
    """Run the transaction checker in the background."""
    logger.info("Starting blockchain transaction checker...")
    try:
        # Run the transaction checker script in the background
        subprocess.Popen(['python', 'check_pending_transactions.py'])
        logger.info("Blockchain transaction checker started successfully")
        return True
    except Exception as e:
        logger.error(f"Error starting blockchain transaction checker: {str(e)}")
        return False

def optimize_blockchain_transfer():
    """Main function to optimize blockchain data transfer speed."""
    start_time = datetime.utcnow()
    logger.info("Starting blockchain data transfer optimization...")
    
    # Step 1: Optimize database indexes
    if not optimize_database_indexes():
        logger.error("Failed to optimize database indexes. Continuing anyway...")
    
    # Step 2: Optimize query performance
    if not optimize_query_performance():
        logger.error("Failed to optimize query performance. Continuing anyway...")
    
    # Step 3: Clear any stuck pending transactions
    if not clear_pending_transactions():
        logger.error("Failed to clear stuck transactions. Continuing anyway...")
    
    # Step 4: Run the blockchain transaction checker
    if not run_blockchain_checker():
        logger.error("Failed to start blockchain transaction checker. Continuing anyway...")
    
    # Calculate total time
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Blockchain data transfer optimization completed in {duration:.2f} seconds")
    
    return True

if __name__ == "__main__":
    logger.info("This script will optimize blockchain data transfer speed.")
    logger.info("Are you sure you want to continue? (yes/no)")
    
    confirmation = input().strip().lower()
    if confirmation == "yes":
        optimize_blockchain_transfer()
    else:
        logger.info("Blockchain data transfer optimization cancelled.") 