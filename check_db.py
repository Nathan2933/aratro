from app import app, db
from models import StockRequest, RationStockRequest, Warehouse

with app.app_context():
    print("StockRequests:", StockRequest.query.count())
    print("RationStockRequests:", RationStockRequest.query.count())
    
    # Get a sample warehouse
    warehouse = Warehouse.query.first()
    if warehouse:
        print(f"Warehouse ID: {warehouse.id}")
        
        # Check requests for this warehouse
        stock_requests = StockRequest.query.filter_by(to_id=warehouse.id).all()
        ration_requests = RationStockRequest.query.filter_by(warehouse_id=warehouse.id).all()
        
        print(f"Stock requests for warehouse {warehouse.id}: {len(stock_requests)}")
        print(f"Ration requests for warehouse {warehouse.id}: {len(ration_requests)}")
        
        # Check recent requests
        recent_stock = StockRequest.query.filter_by(to_id=warehouse.id).order_by(StockRequest.request_date.desc()).limit(5).all()
        recent_ration = RationStockRequest.query.filter_by(warehouse_id=warehouse.id).order_by(RationStockRequest.request_date.desc()).limit(5).all()
        
        print(f"Recent stock requests: {len(recent_stock)}")
        print(f"Recent ration requests: {len(recent_ration)}")
        
        # Print details of recent stock requests
        print("\nRecent Stock Requests:")
        for req in recent_stock:
            print(f"ID: {req.id}, Status: {req.status}, Date: {req.request_date}")
        
        # Print details of recent ration requests
        print("\nRecent Ration Requests:")
        for req in recent_ration:
            print(f"ID: {req.id}, Status: {req.status}, Date: {req.request_date}")
    else:
        print("No warehouses found in the database.") 