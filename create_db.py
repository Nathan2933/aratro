from app import app, db
from models import User, Farmer, Warehouse, Stock, StockRequest, WarehouseRequest
import datetime
from sqlalchemy import text

# Create all tables
with app.app_context():
    # Drop existing tables
    db.drop_all()
    
    # Create tables
    db.create_all()
    
    # Explicitly create stock_request table with correct schema
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS stock_request (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER NOT NULL,
            to_id INTEGER NOT NULL,
            stock_id INTEGER NOT NULL,
            request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'pending'
        )
    """))
    db.session.commit()
    
    # Check if we need to add some sample warehouse requests
    if not WarehouseRequest.query.first():
        print("Adding sample warehouse requests...")
        
        # Get warehouses
        warehouses = Warehouse.query.all()
        
        if warehouses:
            # Add sample warehouse requests
            sample_requests = [
                WarehouseRequest(
                    warehouse_id=warehouses[0].id,
                    stock_type="Rice",
                    quantity=50.0,
                    price_per_ton=2500.0,
                    description="Looking for high-quality rice for storage. Premium rates offered for early delivery.",
                    status="open",
                    date_posted=datetime.datetime.utcnow(),
                    expiry_date=datetime.datetime.utcnow() + datetime.timedelta(days=30)
                ),
                WarehouseRequest(
                    warehouse_id=warehouses[-1].id if len(warehouses) > 1 else warehouses[0].id,
                    stock_type="Wheat",
                    quantity=75.0,
                    price_per_ton=2200.0,
                    description="Urgent requirement for wheat. Storage space available immediately.",
                    status="open",
                    date_posted=datetime.datetime.utcnow(),
                    expiry_date=datetime.datetime.utcnow() + datetime.timedelta(days=15)
                ),
                WarehouseRequest(
                    warehouse_id=warehouses[0].id,
                    stock_type="Corn",
                    quantity=30.0,
                    price_per_ton=1800.0,
                    description="Looking for corn for long-term storage. Climate-controlled facilities available.",
                    status="open",
                    date_posted=datetime.datetime.utcnow(),
                    expiry_date=datetime.datetime.utcnow() + datetime.timedelta(days=45)
                )
            ]
            
            for request in sample_requests:
                db.session.add(request)
            
            db.session.commit()
            print("Sample warehouse requests added successfully!")
        else:
            print("No warehouses found. Please add warehouses first.")
    
    print("Database setup complete!")
