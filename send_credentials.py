from app import app
from models import db, RationShop
from email_utils import send_credentials_email
import random
import string
from datetime import datetime

def generate_unique_id(length=8):
    """Generate a unique ID with prefix RS-"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(length))
    return f"RS-{random_part}"

def generate_temp_password(length=10):
    """Generate a temporary password"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def send_pending_credentials():
    """Send credentials to all approved shops that haven't received them yet"""
    with app.app_context():
        # Find all approved shops without unique_id or temp_password
        shops = RationShop.query.filter_by(status='approved').filter(
            (RationShop.unique_id == None) | 
            (RationShop.unique_id == '') | 
            (RationShop.temp_password == None) | 
            (RationShop.temp_password == '')
        ).all()
        
        if not shops:
            print("No pending approved shops found that need credentials.")
            return
        
        print(f"Found {len(shops)} approved shops that need credentials.")
        
        for shop in shops:
            # Skip if no email
            if not shop.email:
                print(f"Shop ID {shop.id} ({shop.name}) has no email address. Skipping.")
                continue
                
            # Generate credentials if needed
            if not shop.unique_id or shop.unique_id == '':
                shop.unique_id = generate_unique_id()
                
            if not shop.temp_password or shop.temp_password == '':
                shop.temp_password = generate_temp_password()
            
            # Send email
            success = send_credentials_email(
                shop.email,
                shop.name,
                shop.unique_id,
                shop.temp_password
            )
            
            if success:
                print(f"Credentials sent to {shop.name} ({shop.email})")
                # Update the shop record
                shop.approved_at = datetime.utcnow()
                db.session.commit()
            else:
                print(f"Failed to send credentials to {shop.name} ({shop.email})")

def send_specific_credentials(shop_id):
    """Send credentials to a specific shop by ID"""
    with app.app_context():
        shop = RationShop.query.get(shop_id)
        
        if not shop:
            print(f"Shop with ID {shop_id} not found.")
            return
            
        if shop.status != 'approved':
            print(f"Shop {shop.name} (ID: {shop_id}) is not approved. Status: {shop.status}")
            return
            
        if not shop.email:
            print(f"Shop {shop.name} (ID: {shop_id}) has no email address.")
            return
            
        # Generate credentials if needed
        if not shop.unique_id or shop.unique_id == '':
            shop.unique_id = generate_unique_id()
            
        if not shop.temp_password or shop.temp_password == '':
            shop.temp_password = generate_temp_password()
        
        # Send email
        success = send_credentials_email(
            shop.email,
            shop.name,
            shop.unique_id,
            shop.temp_password
        )
        
        if success:
            print(f"Credentials sent to {shop.name} ({shop.email})")
            # Update the shop record
            shop.approved_at = datetime.utcnow()
            db.session.commit()
        else:
            print(f"Failed to send credentials to {shop.name} ({shop.email})")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        try:
            shop_id = int(sys.argv[1])
            print(f"Sending credentials to shop with ID: {shop_id}")
            send_specific_credentials(shop_id)
        except ValueError:
            print("Invalid shop ID. Please provide a valid integer ID.")
    else:
        print("Sending credentials to all pending approved shops...")
        send_pending_credentials() 