#!/usr/bin/env python3
"""
Add a test crop price to the database.
"""
from app import app, db
from models import CropPrice
from datetime import datetime

def add_test_crop_price():
    """Add a test crop price to the database."""
    with app.app_context():
        # Check if a test crop price already exists
        existing_price = CropPrice.query.filter_by(crop_type="Rice").first()
        
        if existing_price:
            print(f"Test crop price for Rice already exists: ₹{existing_price.price_per_kg} per kg")
            return
        
        # Create a test crop price
        test_price = CropPrice(
            crop_type="Rice",
            price_per_kg=25.00,  # Price per kg (2500 per ton / 100 = 25 per kg)
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add to database
        db.session.add(test_price)
        db.session.commit()
        
        print(f"Test crop price added: Rice - ₹{test_price.price_per_kg} per kg")
        
        # List all crop prices
        all_prices = CropPrice.query.all()
        print("\nAll crop prices:")
        for price in all_prices:
            print(f"{price.crop_type}: ₹{price.price_per_kg} per kg")

if __name__ == "__main__":
    add_test_crop_price() 