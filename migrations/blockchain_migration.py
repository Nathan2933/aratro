"""
Migration script to add blockchain-related fields to the database.
"""
import os
import sys
from datetime import datetime
from sqlalchemy import text

# Add the parent directory to the path so we can import from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, User, Farmer, Warehouse, Stock, StockRequest, WarehouseRequest, RationShop, RationStockRequest, Admin, BlockchainTransaction
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('blockchain_migration')

def add_blockchain_columns():
    """Add blockchain-related columns to existing tables."""
    with app.app_context():
        try:
            # Check if the columns already exist
            inspector = db.inspect(db.engine)
            
            # Add eth_address column to User table if it doesn't exist
            if 'eth_address' not in [c['name'] for c in inspector.get_columns('user')]:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "user" ADD COLUMN eth_address VARCHAR(42) UNIQUE'))
                    conn.commit()
                logger.info("Added eth_address column to User table")
            
            # Add eth_address column to Farmer table if it doesn't exist
            if 'eth_address' not in [c['name'] for c in inspector.get_columns('farmer')]:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "farmer" ADD COLUMN eth_address VARCHAR(42) UNIQUE'))
                    conn.commit()
                logger.info("Added eth_address column to Farmer table")
            
            # Add eth_address column to Warehouse table if it doesn't exist
            if 'eth_address' not in [c['name'] for c in inspector.get_columns('warehouse')]:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "warehouse" ADD COLUMN eth_address VARCHAR(42) UNIQUE'))
                    conn.commit()
                logger.info("Added eth_address column to Warehouse table")
            
            # Add eth_address column to Admin table if it doesn't exist
            if 'eth_address' not in [c['name'] for c in inspector.get_columns('admin')]:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "admin" ADD COLUMN eth_address VARCHAR(42) UNIQUE'))
                    conn.commit()
                logger.info("Added eth_address column to Admin table")
            
            # Add eth_address column to RationShop table if it doesn't exist
            if 'eth_address' not in [c['name'] for c in inspector.get_columns('ration_shop')]:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "ration_shop" ADD COLUMN eth_address VARCHAR(42) UNIQUE'))
                    conn.commit()
                logger.info("Added eth_address column to RationShop table")
            
            # Add blockchain_id and blockchain_tx_hash columns to Stock table if they don't exist
            if 'blockchain_id' not in [c['name'] for c in inspector.get_columns('stock')]:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "stock" ADD COLUMN blockchain_id INTEGER'))
                    conn.commit()
                logger.info("Added blockchain_id column to Stock table")
            
            if 'blockchain_tx_hash' not in [c['name'] for c in inspector.get_columns('stock')]:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "stock" ADD COLUMN blockchain_tx_hash VARCHAR(66)'))
                    conn.commit()
                logger.info("Added blockchain_tx_hash column to Stock table")
            
            # Add blockchain_id and blockchain_tx_hash columns to StockRequest table if they don't exist
            if 'blockchain_id' not in [c['name'] for c in inspector.get_columns('stock_request')]:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "stock_request" ADD COLUMN blockchain_id INTEGER'))
                    conn.commit()
                logger.info("Added blockchain_id column to StockRequest table")
            
            if 'blockchain_tx_hash' not in [c['name'] for c in inspector.get_columns('stock_request')]:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "stock_request" ADD COLUMN blockchain_tx_hash VARCHAR(66)'))
                    conn.commit()
                logger.info("Added blockchain_tx_hash column to StockRequest table")
            
            # Add blockchain_id and blockchain_tx_hash columns to WarehouseRequest table if they don't exist
            if 'blockchain_id' not in [c['name'] for c in inspector.get_columns('warehouse_request')]:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "warehouse_request" ADD COLUMN blockchain_id INTEGER'))
                    conn.commit()
                logger.info("Added blockchain_id column to WarehouseRequest table")
            
            if 'blockchain_tx_hash' not in [c['name'] for c in inspector.get_columns('warehouse_request')]:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "warehouse_request" ADD COLUMN blockchain_tx_hash VARCHAR(66)'))
                    conn.commit()
                logger.info("Added blockchain_tx_hash column to WarehouseRequest table")
            
            # Add blockchain_id and blockchain_tx_hash columns to RationStockRequest table if they don't exist
            if 'blockchain_id' not in [c['name'] for c in inspector.get_columns('ration_stock_request')]:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "ration_stock_request" ADD COLUMN blockchain_id INTEGER'))
                    conn.commit()
                logger.info("Added blockchain_id column to RationStockRequest table")
            
            if 'blockchain_tx_hash' not in [c['name'] for c in inspector.get_columns('ration_stock_request')]:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "ration_stock_request" ADD COLUMN blockchain_tx_hash VARCHAR(66)'))
                    conn.commit()
                logger.info("Added blockchain_tx_hash column to RationStockRequest table")
            
            # Create BlockchainTransaction table if it doesn't exist
            if not inspector.has_table('blockchain_transaction'):
                BlockchainTransaction.__table__.create(db.engine)
                logger.info("Created BlockchainTransaction table")
            
            logger.info("Database migration completed successfully")
            
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            raise

def generate_eth_addresses():
    """Generate Ethereum addresses for existing users."""
    with app.app_context():
        try:
            # Import the function here to avoid circular imports
            from blockchain import get_eth_address
            
            # Generate addresses for users
            users = User.query.filter(User.eth_address.is_(None)).all()
            for user in users:
                user.eth_address = get_eth_address(user.id, user.role)
                logger.info(f"Generated Ethereum address for user {user.id}: {user.eth_address}")
            
            # Generate addresses for farmers
            farmers = Farmer.query.filter(Farmer.eth_address.is_(None)).all()
            for farmer in farmers:
                farmer.eth_address = get_eth_address(farmer.id, 'farmer')
                logger.info(f"Generated Ethereum address for farmer {farmer.id}: {farmer.eth_address}")
            
            # Generate addresses for warehouses
            warehouses = Warehouse.query.filter(Warehouse.eth_address.is_(None)).all()
            for warehouse in warehouses:
                warehouse.eth_address = get_eth_address(warehouse.id, 'warehouse')
                logger.info(f"Generated Ethereum address for warehouse {warehouse.id}: {warehouse.eth_address}")
            
            # Generate addresses for admins
            admins = Admin.query.filter(Admin.eth_address.is_(None)).all()
            for admin in admins:
                admin.eth_address = get_eth_address(admin.id, 'admin')
                logger.info(f"Generated Ethereum address for admin {admin.id}: {admin.eth_address}")
            
            # Generate addresses for ration shops
            ration_shops = RationShop.query.filter(RationShop.eth_address.is_(None)).all()
            for shop in ration_shops:
                shop.eth_address = get_eth_address(shop.id, 'ration_shop')
                logger.info(f"Generated Ethereum address for ration shop {shop.id}: {shop.eth_address}")
            
            # Commit changes
            db.session.commit()
            logger.info("Ethereum addresses generated successfully")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error generating Ethereum addresses: {e}")
            raise

if __name__ == '__main__':
    # Run the migration
    add_blockchain_columns()
    generate_eth_addresses()
    print("Migration completed successfully") 