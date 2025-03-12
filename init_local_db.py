#!/usr/bin/env python3
"""
Initialize the local database tables.
"""
import os
from dotenv import load_dotenv
from app import app, db
from models import User, Farmer, Warehouse, Admin, Stock, StockRequest, RationShop, RationStockRequest, BlockchainTransaction, Notification, WarehouseRequest, OTP

# Load environment variables
load_dotenv()

def init_db():
    """Initialize the database tables."""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

if __name__ == "__main__":
    # Check if using local database
    if os.environ.get('USE_LOCAL_DB', 'false').lower() != 'true':
        print("Error: USE_LOCAL_DB is not set to 'true' in .env file.")
        print("Please set USE_LOCAL_DB=true in .env file to use local database.")
        exit(1)
    
    # Initialize database
    init_db() 