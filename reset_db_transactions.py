#!/usr/bin/env python3
"""
Reset any aborted transactions in the database.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

def reset_transactions():
    """Reset any aborted transactions in the database."""
    # Get database URL from environment variables
    if os.environ.get('USE_LOCAL_DB', 'false').lower() == 'true':
        db_url = os.environ.get('LOCAL_DB_URL')
        print("Using LOCAL database")
    else:
        db_url = os.environ.get('SUPABASE_DB_URL')
        print("Using SUPABASE database")
    
    if not db_url:
        print("Error: No database URL found in environment variables")
        return
    
    # Create engine
    engine = create_engine(db_url)
    
    # Connect to database
    with engine.connect() as connection:
        # Rollback any active transaction
        connection.execute(text("ROLLBACK"))
        print("Rolled back any active transaction")
        
        # Get active connections
        result = connection.execute(text("SELECT pid, state, query FROM pg_stat_activity WHERE datname = current_database()"))
        active_connections = result.fetchall()
        
        print(f"Found {len(active_connections)} active connections")
        
        # Terminate idle transactions
        for conn in active_connections:
            pid = conn[0]
            state = conn[1]
            query = conn[2]
            
            if state == 'idle in transaction':
                print(f"Terminating idle transaction (PID: {pid}, Query: {query})")
                try:
                    connection.execute(text(f"SELECT pg_terminate_backend({pid})"))
                except Exception as e:
                    print(f"Error terminating connection: {e}")
        
        # Commit the transaction
        connection.commit()
        print("Database transactions reset successfully!")

if __name__ == "__main__":
    reset_transactions() 