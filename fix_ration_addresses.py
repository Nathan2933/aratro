#!/usr/bin/env python3
"""
Script to fix ration shop Ethereum addresses.
"""
import os
import sys
import logging
import secrets
from web3 import Web3
from app import app
from models import db, RationShop, Warehouse
from blockchain import get_eth_address

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('fix_ration_addresses')

def generate_eth_address():
    """Generate a random Ethereum address."""
    private_key = secrets.token_hex(32)
    w3 = Web3()
    account = w3.eth.account.from_key('0x' + private_key)
    return account.address

def fix_ration_shop_addresses():
    """Fix missing Ethereum addresses for ration shops."""
    with app.app_context():
        # Find all ration shops without Ethereum addresses
        ration_shops = RationShop.query.filter(RationShop.eth_address == None).all()
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
    """Main function to fix Ethereum addresses."""
    fix_ration_shop_addresses()
    
    # Check if addresses were fixed
    with app.app_context():
        total_shops = RationShop.query.count()
        shops_with_eth = RationShop.query.filter(RationShop.eth_address != None).count()
        print(f"Ration shops with Ethereum addresses: {shops_with_eth} out of {total_shops}")

if __name__ == "__main__":
    main() 