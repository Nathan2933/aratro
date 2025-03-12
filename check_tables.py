from app import app, db
from models import User, Admin, Farmer, Warehouse, Stock, StockRequest, WarehouseRequest
from models import RationShop, RationStockRequest, Notification, OTP, BlockchainTransaction

def check_tables():
    """
    Check the count of records in all database tables.
    """
    with app.app_context():
        print("Database Tables Status:")
        print("-----------------------")
        print(f"Users: {User.query.count()}")
        print(f"Admins: {Admin.query.count()}")
        print(f"Farmers: {Farmer.query.count()}")
        print(f"Warehouses: {Warehouse.query.count()}")
        print(f"Stocks: {Stock.query.count()}")
        print(f"Stock Requests: {StockRequest.query.count()}")
        print(f"Warehouse Requests: {WarehouseRequest.query.count()}")
        print(f"Ration Shops: {RationShop.query.count()}")
        print(f"Ration Stock Requests: {RationStockRequest.query.count()}")
        print(f"Notifications: {Notification.query.count()}")
        print(f"OTPs: {OTP.query.count()}")
        print(f"Blockchain Transactions: {BlockchainTransaction.query.count()}")
        print("-----------------------")
        print("Database reset verification complete!")

if __name__ == "__main__":
    check_tables() 