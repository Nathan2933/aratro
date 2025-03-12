#!/usr/bin/env python3
"""
Update the database schema to match the models.
"""
import os
import subprocess
from dotenv import load_dotenv
from app import app, db
from models import User, Farmer, Warehouse, Admin, Stock, StockRequest, RationShop, RationStockRequest, BlockchainTransaction, Notification, WarehouseRequest, OTP
from flask_migrate import Migrate

# Load environment variables
load_dotenv()

def update_schema():
    """Update the database schema to match the models."""
    with app.app_context():
        # Create a migration repository if it doesn't exist
        migrate = Migrate(app, db)
        
        # Check if migrations directory exists
        if not os.path.exists('migrations'):
            print("Initializing migrations repository...")
            subprocess.run(['flask', 'db', 'init'])
        
        # Create a migration
        print("Creating migration...")
        subprocess.run(['flask', 'db', 'migrate', '-m', 'Update schema'])
        
        # Apply the migration
        print("Applying migration...")
        subprocess.run(['flask', 'db', 'upgrade'])
        
        print("Database schema updated successfully!")

if __name__ == "__main__":
    # Check if using local database
    if os.environ.get('USE_LOCAL_DB', 'false').lower() != 'true':
        print("Error: USE_LOCAL_DB is not set to 'true' in .env file.")
        print("Please set USE_LOCAL_DB=true in .env file to use local database.")
        exit(1)
    
    # Set Flask app environment variable
    os.environ['FLASK_APP'] = 'app.py'
    
    # Update schema
    update_schema() 