#!/usr/bin/env python3
"""
Add more crop prices to the database.
"""
from app import app, db
from models import CropPrice
from datetime import datetime

def add_more_crop_prices():
    """Add more crop prices to the database."""
    with app.app_context():
        # Define crop prices
        crops = [
            {"type": "Wheat", "price": 22.00},
            {"type": "Corn", "price": 18.00},
            {"type": "Barley", "price": 20.00},
            {"type": "Sorghum", "price": 19.00},
            {"type": "Millet", "price": 21.00},
            {"type": "Oats", "price": 23.00},
            {"type": "Rye", "price": 24.00},
            {"type": "Soybeans", "price": 30.00},
            {"type": "Pulses", "price": 35.00}
        ]
        
        added_count = 0
        
        for crop in crops:
            # Check if crop price already exists
            existing_price = CropPrice.query.filter_by(crop_type=crop["type"]).first()
            
            if existing_price:
                print(f"Price for {crop['type']} already exists: ₹{existing_price.price_per_kg} per kg")
                continue
            
            # Create new crop price
            new_price = CropPrice(
                crop_type=crop["type"],
                price_per_kg=crop["price"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add to database
            db.session.add(new_price)
            added_count += 1
        
        # Commit all changes
        if added_count > 0:
            db.session.commit()
            print(f"Added {added_count} new crop prices")
        else:
            print("No new crop prices added")
        
        # List all crop prices
        all_prices = CropPrice.query.all()
        print("\nAll crop prices:")
        for price in all_prices:
            print(f"{price.crop_type}: ₹{price.price_per_kg} per kg")

if __name__ == "__main__":
    add_more_crop_prices() 