#!/usr/bin/env python3
"""
Create the CropPrice table in the database.
"""
from app import app, db
from models import CropPrice

def create_crop_price_table():
    """Create the CropPrice table in the database."""
    with app.app_context():
        # Create the CropPrice table
        db.create_all()
        print("CropPrice table created successfully!")

if __name__ == "__main__":
    create_crop_price_table() 