from app import app, db
from models import User, Farmer, Warehouse, Stock, StockRequest, WarehouseRequest, Admin, RationShop, RationStockRequest
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def recreate_tables():
    # Check if Supabase connection string exists
    supabase_url = os.getenv('SUPABASE_DB_URL')
    if not supabase_url:
        print("Error: SUPABASE_DB_URL not found in .env file")
        sys.exit(1)

    print(f"\nConnecting to Supabase database...")
    
    with app.app_context():
        try:
            # Drop all existing tables
            print("Dropping all tables...")
            db.drop_all()
            
            # Create all tables with new schema
            print("Creating tables with new schema...")
            db.create_all()
            
            # Create default admin user
            print("Creating default admin user...")
            admin = Admin(
                email="admin@aratro.com",
                password_hash=generate_password_hash("admin123"),
                created_at=datetime.utcnow()
            )
            
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created successfully!")
            
            print("\nDatabase recreation completed successfully!")
            print("\nNext steps:")
            print("1. Set up Row Level Security (RLS) policies in Supabase")
            print("2. Configure backups and monitoring")
            print("3. Test the application with the new database")
            
        except Exception as e:
            db.session.rollback()
            print(f"\nError during database recreation: {str(e)}")
            print("\nPlease check:")
            print("1. Your Supabase credentials are correct")
            print("2. The connection string format is correct")
            print("3. Your IP is allowed in Supabase")
            print("4. The database user has sufficient privileges")
            sys.exit(1)

if __name__ == "__main__":
    try:
        recreate_tables()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1) 