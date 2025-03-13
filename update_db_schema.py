#!/usr/bin/env python3
"""
Update the database schema to match the models.
"""
import os
import subprocess
from dotenv import load_dotenv
from app import app, db
from models import User, Farmer, Warehouse, Admin, Stock, StockRequest, RationShop, RationStockRequest, BlockchainTransaction, Notification, WarehouseRequest, OTP, CropPrice
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
        
        # Create tables if they don't exist
        db.create_all()
        
        print("Database schema updated successfully!")

if __name__ == "__main__":
    # Set Flask app environment variable
    os.environ['FLASK_APP'] = 'app.py'
    
    # Update schema
    update_schema() 