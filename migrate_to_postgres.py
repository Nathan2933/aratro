import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL reserved keywords that need quoting
RESERVED_KEYWORDS = {'user', 'group', 'order', 'table', 'select', 'where', 'from', 'index'}

def get_sqlite_tables():
    """Get all tables from SQLite database"""
    sqlite_conn = sqlite3.connect('instance/aratro.db')
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    sqlite_conn.close()
    return [table[0] for table in tables]

def get_table_schema(table_name):
    """Get schema for a specific table"""
    sqlite_conn = sqlite3.connect('instance/aratro.db')
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    sqlite_conn.close()
    return columns

def get_table_data(table_name):
    """Get all data from a specific table"""
    sqlite_conn = sqlite3.connect('instance/aratro.db')
    cursor = sqlite_conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name};")
    data = cursor.fetchall()
    sqlite_conn.close()
    return data

def quote_identifier(identifier):
    """Add quotes to identifier if it's a reserved keyword"""
    if identifier.lower() in RESERVED_KEYWORDS:
        return f'"{identifier}"'
    return identifier

def convert_row_data(columns, row):
    """Convert row data to appropriate PostgreSQL types"""
    converted_row = list(row)
    for i, col in enumerate(columns):
        col_type = col[2].upper()
        value = row[i]
        
        # Convert SQLite boolean (0/1) to PostgreSQL boolean
        if 'BOOLEAN' in col_type and value is not None:
            converted_row[i] = bool(value)
    
    return tuple(converted_row)

def create_postgres_table(pg_cursor, table_name, columns):
    """Create table in PostgreSQL"""
    # Map SQLite types to PostgreSQL types
    type_mapping = {
        'INTEGER': 'INTEGER',
        'REAL': 'DOUBLE PRECISION',
        'TEXT': 'TEXT',
        'BLOB': 'BYTEA',
        'BOOLEAN': 'BOOLEAN',
        'DATETIME': 'TIMESTAMP',
        'FLOAT': 'FLOAT',
        'VARCHAR': 'VARCHAR',
        'TIMESTAMP': 'TIMESTAMP'
    }
    
    columns_def = []
    for col in columns:
        col_name = quote_identifier(col[1])
        col_type = col[2].upper()
        
        # Handle specific type cases
        if 'VARCHAR' in col_type:
            postgres_type = col_type
        else:
            for sqlite_type, postgres_type in type_mapping.items():
                if sqlite_type in col_type:
                    break
            else:
                postgres_type = 'TEXT'  # Default to TEXT if type is unknown
        
        nullable = "NOT NULL" if col[3] else ""
        pk = "PRIMARY KEY" if col[5] else ""
        
        columns_def.append(f"{col_name} {postgres_type} {nullable} {pk}".strip())
    
    quoted_table_name = quote_identifier(table_name)
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {quoted_table_name} (
        {', '.join(columns_def)}
    );
    """
    pg_cursor.execute(create_table_sql)

def migrate_data():
    """Migrate all data from SQLite to PostgreSQL"""
    # Get PostgreSQL connection details from environment variables
    db_uri = os.getenv('DATABASE_URI')
    db_params = {
        'host': 'localhost',
        'database': 'aratro_db',
        'user': 'postgres',
        'password': '1234'
    }
    
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(**db_params)
    pg_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    pg_cursor = pg_conn.cursor()
    
    # Get all tables from SQLite
    tables = get_sqlite_tables()
    
    for table_name in tables:
        print(f"Migrating table: {table_name}")
        
        # Get table schema and data
        columns = get_table_schema(table_name)
        data = get_table_data(table_name)
        
        # Create table in PostgreSQL
        try:
            create_postgres_table(pg_cursor, table_name, columns)
            
            if data:
                # Convert data types
                converted_data = [convert_row_data(columns, row) for row in data]
                
                # Prepare INSERT statement
                quoted_table_name = quote_identifier(table_name)
                placeholders = ','.join(['%s'] * len(columns))
                insert_sql = f"INSERT INTO {quoted_table_name} VALUES ({placeholders})"
                
                # Insert data
                pg_cursor.executemany(insert_sql, converted_data)
                print(f"Successfully migrated {len(data)} rows for table {table_name}")
        except Exception as e:
            print(f"Error migrating data for table {table_name}: {str(e)}")
            continue
    
    pg_conn.close()
    print("Migration completed!")

if __name__ == "__main__":
    try:
        migrate_data()
    except Exception as e:
        print(f"Migration failed: {str(e)}") 