#!/usr/bin/env python3
"""
Script to fix missing Ethereum addresses for farmers and warehouses.
This script will:
1. Find all farmers and warehouses without Ethereum addresses
2. Generate Ethereum addresses for them
3. Update the database
"""
import os
import sys
import logging
import secrets
from web3 import Web3
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from the root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Farmer, Warehouse, RationShop
import app
from blockchain import get_eth_address

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('fix_missing_eth_addresses')

# Load environment variables
load_dotenv()

def generate_eth_address():
    """Generate a random Ethereum address."""
    private_key = secrets.token_hex(32)
    w3 = Web3()
    account = w3.eth.account.from_key('0x' + private_key)
    return account.address

def fix_farmer_addresses():
    """Fix missing Ethereum addresses for farmers."""
    # Find all farmers without Ethereum addresses
    farmers = Farmer.query.filter(Farmer.eth_address.is_(None)).all()
    logger.info(f"Found {len(farmers)} farmers without Ethereum addresses")
    
    for farmer in farmers:
        try:
            # Generate Ethereum address
            eth_address = get_eth_address(farmer.id, 'farmer')
            if not eth_address:
                eth_address = generate_eth_address()
            
            # Update farmer
            farmer.eth_address = eth_address
            db.session.add(farmer)
            logger.info(f"Added Ethereum address {eth_address} to farmer {farmer.id} ({farmer.name})")
        except Exception as e:
            logger.error(f"Error fixing Ethereum address for farmer {farmer.id}: {e}")
    
    # Commit changes
    try:
        db.session.commit()
        logger.info(f"Successfully updated {len(farmers)} farmers")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error committing changes: {e}")

def fix_warehouse_addresses():
    """Fix missing Ethereum addresses for warehouses."""
    # Find all warehouses without Ethereum addresses
    warehouses = Warehouse.query.filter(Warehouse.eth_address.is_(None)).all()
    logger.info(f"Found {len(warehouses)} warehouses without Ethereum addresses")
    
    for warehouse in warehouses:
        try:
            # Generate Ethereum address
            eth_address = get_eth_address(warehouse.id, 'warehouse')
            if not eth_address:
                eth_address = generate_eth_address()
            
            # Update warehouse
            warehouse.eth_address = eth_address
            db.session.add(warehouse)
            logger.info(f"Added Ethereum address {eth_address} to warehouse {warehouse.id} ({warehouse.name})")
        except Exception as e:
            logger.error(f"Error fixing Ethereum address for warehouse {warehouse.id}: {e}")
    
    # Commit changes
    try:
        db.session.commit()
        logger.info(f"Successfully updated {len(warehouses)} warehouses")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error committing changes: {e}")

def fix_ration_shop_addresses():
    """Fix missing Ethereum addresses for ration shops."""
    # Find all ration shops without Ethereum addresses
    ration_shops = RationShop.query.filter(RationShop.eth_address.is_(None)).all()
    logger.info(f"Found {len(ration_shops)} ration shops without Ethereum addresses")
    
    for shop in ration_shops:
        try:
            # Generate Ethereum address
            eth_address = get_eth_address(shop.id, 'ration_shop')
            if not eth_address:
                eth_address = generate_eth_address()
            
            # Update ration shop
            shop.eth_address = eth_address
            db.session.add(shop)
            logger.info(f"Added Ethereum address {eth_address} to ration shop {shop.id} ({shop.name})")
        except Exception as e:
            logger.error(f"Error fixing Ethereum address for ration shop {shop.id}: {e}")
    
    # Commit changes
    try:
        db.session.commit()
        logger.info(f"Successfully updated {len(ration_shops)} ration shops")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error committing changes: {e}")

def main():
    """Main function to run the script."""
    # Initialize Flask app
    flask_app = app.Flask(__name__)
    
    # Database configuration
    local_db_url = os.environ.get('LOCAL_DB_URL')
    supabase_url = os.environ.get('SUPABASE_DB_URL')

    # Use local database if specified, otherwise use Supabase
    if local_db_url and os.environ.get('USE_LOCAL_DB', 'false').lower() == 'true':
        logger.info("Using LOCAL database")
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = local_db_url
    elif supabase_url:
        logger.info("Using SUPABASE database")
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = supabase_url
    else:
        logger.error("No database URL found in environment variables")
        return 1
    
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(flask_app)
    
    with flask_app.app_context():
        try:
            # Fix farmer addresses
            fix_farmer_addresses()
            
            # Fix warehouse addresses
            fix_warehouse_addresses()
            
            # Fix ration shop addresses
            fix_ration_shop_addresses()
            
            logger.info("Successfully fixed missing Ethereum addresses")
            return 0
        except Exception as e:
            logger.error(f"Error fixing missing Ethereum addresses: {e}")
            return 1

if __name__ == "__main__":
    sys.exit(main()) 