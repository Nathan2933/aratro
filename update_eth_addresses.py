from app import app, db
from models import Farmer, Warehouse, User
import logging
from dotenv import load_dotenv
import os
from eth_account import Account
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('update_eth_addresses')

# Load environment variables
load_dotenv()

def generate_private_key():
    """Generate a random private key."""
    return "0x" + secrets.token_hex(32)

def update_eth_addresses():
    """Update Ethereum addresses for existing farmers and warehouses."""
    with app.app_context():
        # Get the main account from private key (for contract owner)
        private_key = os.environ.get('PRIVATE_KEY')
        if not private_key:
            print("No private key found in environment variables")
            return
        
        if not private_key.startswith('0x'):
            private_key = f'0x{private_key}'
        
        main_account = Account.from_key(private_key)
        main_address = main_account.address
        
        print(f"Using main Ethereum address: {main_address}")
        
        # Update farmers with unique addresses
        farmers = Farmer.query.all()
        print(f"Found {len(farmers)} farmers")
        
        # First farmer gets the main address (contract owner)
        if farmers:
            farmers[0].eth_address = main_address
            print(f"Updated farmer {farmers[0].id} ({farmers[0].name}) with main ETH address: {main_address}")
            
            # Other farmers get unique addresses
            for farmer in farmers[1:]:
                new_key = generate_private_key()
                new_address = Account.from_key(new_key).address
                farmer.eth_address = new_address
                print(f"Updated farmer {farmer.id} ({farmer.name}) with new ETH address: {new_address}")
                print(f"Private key for farmer {farmer.id}: {new_key} (SAVE THIS SECURELY)")
        
        # Update warehouses with unique addresses
        warehouses = Warehouse.query.all()
        print(f"Found {len(warehouses)} warehouses")
        
        for warehouse in warehouses:
            new_key = generate_private_key()
            new_address = Account.from_key(new_key).address
            warehouse.eth_address = new_address
            print(f"Updated warehouse {warehouse.id} ({warehouse.name}) with ETH address: {new_address}")
            print(f"Private key for warehouse {warehouse.id}: {new_key} (SAVE THIS SECURELY)")
        
        # Update users with unique addresses
        users = User.query.all()
        print(f"Found {len(users)} users")
        
        for user in users:
            # Skip users that already have an ETH address
            if user.eth_address:
                print(f"User {user.id} already has ETH address: {user.eth_address}")
                continue
                
            new_key = generate_private_key()
            new_address = Account.from_key(new_key).address
            user.eth_address = new_address
            print(f"Updated user {user.id} with ETH address: {new_address}")
            print(f"Private key for user {user.id}: {new_key} (SAVE THIS SECURELY)")
        
        # Commit changes
        try:
            db.session.commit()
            print("Successfully updated Ethereum addresses")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating Ethereum addresses: {e}")

if __name__ == "__main__":
    update_eth_addresses() 