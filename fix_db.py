from models import db, RationShop
from app import app
import sqlalchemy as sa
from sqlalchemy import inspect

# Use the existing app context
with app.app_context():
    # Get inspector
    inspector = inspect(db.engine)
    
    # Print existing columns in the ration_shop table
    columns = inspector.get_columns('ration_shop')
    print("Current columns in ration_shop table:")
    column_names = [column['name'] for column in columns]
    for column in columns:
        print(f"- {column['name']}: {column['type']}")
    
    # Define the expected columns based on the model
    expected_columns = {
        'id': 'INTEGER',
        'shop_id': 'VARCHAR(50)',
        'user_id': 'INTEGER',
        'name': 'VARCHAR(100)',
        'email': 'VARCHAR(100)',
        'location': 'VARCHAR(200)',
        'aadhar_number': 'VARCHAR(12)',
        'status': 'VARCHAR(20)',
        'unique_id': 'VARCHAR(20)',
        'temp_password': 'VARCHAR(100)',
        'created_at': 'DATETIME',
        'approved_at': 'DATETIME',
        'admin_notes': 'TEXT'
    }
    
    # Check which columns are missing
    missing_columns = {col: type for col, type in expected_columns.items() if col not in column_names}
    
    if missing_columns:
        print("\nMissing columns detected. Adding them now...")
        with db.engine.begin() as conn:
            for col, type in missing_columns.items():
                print(f"Adding column: {col} ({type})")
                conn.execute(sa.text(f"ALTER TABLE ration_shop ADD COLUMN {col} {type}"))
        print("All missing columns added successfully!")
    else:
        print("\nAll expected columns already exist.")
    
    # Fix the user_id column to allow NULL values
    print("\nModifying user_id column to allow NULL values...")
    try:
        # Create a temporary table with the correct schema
        with db.engine.begin() as conn:
            # Create a temporary table with the correct schema
            conn.execute(sa.text("""
                CREATE TABLE ration_shop_temp (
                    id INTEGER PRIMARY KEY,
                    shop_id VARCHAR(50) UNIQUE,
                    user_id INTEGER,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    location VARCHAR(200) NOT NULL,
                    aadhar_number VARCHAR(12) UNIQUE NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    unique_id VARCHAR(20) UNIQUE,
                    temp_password VARCHAR(100),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    approved_at DATETIME,
                    admin_notes TEXT,
                    address VARCHAR(200),
                    phone_number VARCHAR(20),
                    latitude FLOAT,
                    longitude FLOAT,
                    last_login DATETIME
                )
            """))
            
            # Copy data from the original table to the temporary table
            conn.execute(sa.text("""
                INSERT INTO ration_shop_temp 
                SELECT id, shop_id, user_id, name, email, location, aadhar_number, status, unique_id, 
                       temp_password, created_at, approved_at, admin_notes, address, phone_number, 
                       latitude, longitude, last_login
                FROM ration_shop
            """))
            
            # Drop the original table
            conn.execute(sa.text("DROP TABLE ration_shop"))
            
            # Rename the temporary table to the original table name
            conn.execute(sa.text("ALTER TABLE ration_shop_temp RENAME TO ration_shop"))
            
        print("Successfully modified user_id column to allow NULL values!")
    except Exception as e:
        print(f"Error modifying user_id column: {str(e)}")
    
    # Verify the changes
    inspector = inspect(db.engine)
    columns = inspector.get_columns('ration_shop')
    print("\nUpdated columns in ration_shop table:")
    for column in columns:
        print(f"- {column['name']}: {column['type']}")
    
    # Check for extra columns that aren't in the model
    extra_columns = [col['name'] for col in columns if col['name'] not in expected_columns and col['name'] != 'id']
    if extra_columns:
        print("\nExtra columns found that aren't in the model:")
        for col in extra_columns:
            print(f"- {col}")
        print("\nYou may want to consider migrating data from these columns or updating the model.") 