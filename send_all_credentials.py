#!/usr/bin/env python3
"""
Script to send credentials to all approved ration shops.
Usage: python send_all_credentials.py
"""

from app import app
from models import db, RationShop
from email_utils import send_credentials_email
from datetime import datetime

def send_all_credentials():
    """Send credentials to all approved shops"""
    with app.app_context():
        # Find all approved shops
        shops = RationShop.query.filter_by(status='approved').all()
        
        if not shops:
            print("No approved ration shops found.")
            return
        
        print(f"Found {len(shops)} approved shops.")
        
        sent_count = 0
        failed_count = 0
        skipped_count = 0
        
        for shop in shops:
            # Skip if no email
            if not shop.email:
                print(f"Shop ID {shop.id} ({shop.name}) has no email address. Skipping.")
                skipped_count += 1
                continue
                
            # Skip if no credentials
            if not shop.unique_id or not shop.temp_password:
                print(f"Shop ID {shop.id} ({shop.name}) has no credentials. Skipping.")
                skipped_count += 1
                continue
            
            # Send email
            print(f"Sending credentials to {shop.name} ({shop.email})...")
            success = send_credentials_email(
                shop.email,
                shop.name,
                shop.unique_id,
                shop.temp_password
            )
            
            if success:
                print(f"✓ Credentials sent to {shop.name} ({shop.email})")
                sent_count += 1
            else:
                print(f"✗ Failed to send credentials to {shop.name} ({shop.email})")
                failed_count += 1
        
        print("\nSummary:")
        print(f"Total shops: {len(shops)}")
        print(f"Sent: {sent_count}")
        print(f"Failed: {failed_count}")
        print(f"Skipped: {skipped_count}")

if __name__ == "__main__":
    print("Sending credentials to all approved ration shops...")
    send_all_credentials() 