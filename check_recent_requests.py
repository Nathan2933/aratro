from app import app, db
from models import StockRequest, RationStockRequest, Warehouse, Farmer, RationShop
from datetime import datetime

def debug_request(req):
    """Print detailed debug info for a request"""
    if req.__class__.__name__ == 'StockRequest':
        print(f"StockRequest ID: {req.id}")
        print(f"  Status: {req.status}")
        print(f"  Date: {req.request_date}")
        print(f"  Farmer ID: {req.from_id}")
        print(f"  Warehouse ID: {req.to_id}")
        print(f"  Stock ID: {req.stock_id}")
        
        # Check if relationships are loaded
        try:
            print(f"  Farmer name: {req.farmer.name}")
        except Exception as e:
            print(f"  Error accessing farmer: {str(e)}")
            
        try:
            print(f"  Stock type: {req.stock.type}")
            print(f"  Stock quantity: {req.stock.requested_quantity}")
        except Exception as e:
            print(f"  Error accessing stock: {str(e)}")
    
    elif req.__class__.__name__ == 'RationStockRequest':
        print(f"RationStockRequest ID: {req.id}")
        print(f"  Status: {req.status}")
        print(f"  Date: {req.request_date}")
        print(f"  Ration Shop ID: {req.ration_shop_id}")
        print(f"  Warehouse ID: {req.warehouse_id}")
        print(f"  Stock Type: {req.stock_type}")
        print(f"  Quantity: {req.quantity}")
        
        # Check if relationships are loaded
        try:
            print(f"  Ration Shop name: {req.ration_shop.name}")
        except Exception as e:
            print(f"  Error accessing ration shop: {str(e)}")

with app.app_context():
    # Get a sample warehouse
    warehouse = Warehouse.query.first()
    if not warehouse:
        print("No warehouses found in the database.")
        exit()
    
    print(f"Testing with Warehouse ID: {warehouse.id}, Name: {warehouse.name}")
    
    # Get recent requests (both farmer and ration shop)
    farmer_recent_requests = StockRequest.query.filter_by(to_id=warehouse.id).order_by(StockRequest.request_date.desc()).limit(5).all()
    ration_recent_requests = RationStockRequest.query.filter_by(warehouse_id=warehouse.id).order_by(RationStockRequest.request_date.desc()).limit(5).all()
    
    print(f"\nRecent farmer requests: {len(farmer_recent_requests)}")
    print(f"Recent ration requests: {len(ration_recent_requests)}")
    
    # Test combining and sorting
    try:
        combined_requests = farmer_recent_requests + ration_recent_requests
        print(f"\nCombined requests: {len(combined_requests)}")
        
        # Try sorting
        try:
            sorted_requests = sorted(
                combined_requests,
                key=lambda x: x.request_date,
                reverse=True
            )
            print(f"Sorted requests: {len(sorted_requests)}")
            
            # Print the sorted dates to verify
            print("\nSorted request dates:")
            for i, req in enumerate(sorted_requests[:5]):
                print(f"{i+1}. {req.__class__.__name__} {req.id}: {req.request_date}")
                
            # Debug the first few requests in detail
            print("\nDetailed request information:")
            for i, req in enumerate(sorted_requests[:5]):
                print(f"\nRequest #{i+1}:")
                debug_request(req)
                
        except Exception as e:
            print(f"Error sorting requests: {str(e)}")
            
            # Debug each request to find the issue
            print("\nDebugging individual requests:")
            for i, req in enumerate(combined_requests):
                print(f"\nRequest #{i+1}:")
                try:
                    print(f"Class: {req.__class__.__name__}, ID: {req.id}, Date: {req.request_date}")
                except Exception as e:
                    print(f"Error accessing request data: {str(e)}")
                    print(f"Request object: {req}")
    
    except Exception as e:
        print(f"Error combining requests: {str(e)}") 