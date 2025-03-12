from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash
from datetime import datetime
from sqlalchemy import text

def reset_database():
    """
    Reset the database by dropping all tables and recreating them.
    Also creates a default admin user.
    """
    with app.app_context():
        print("Dropping all tables with CASCADE...")
        # Use raw SQL with CASCADE option instead of db.drop_all()
        db.session.execute(text("DROP SCHEMA public CASCADE"))
        db.session.execute(text("CREATE SCHEMA public"))
        db.session.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        db.session.execute(text("GRANT ALL ON SCHEMA public TO public"))
        db.session.commit()
        
        print("Creating all tables...")
        db.create_all()
        
        print("Creating default admin user...")
        admin = Admin(
            email="admin@aratro.com",
            password_hash=generate_password_hash("admin123"),
            created_at=datetime.utcnow()
        )
        db.session.add(admin)
        
        try:
            db.session.commit()
            print("Default admin user created successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {str(e)}")
        
        print("Database reset complete!")

if __name__ == "__main__":
    print("WARNING: This will erase ALL data in the database!")
    print("Are you sure you want to continue? (yes/no)")
    
    confirmation = input().strip().lower()
    if confirmation == "yes":
        reset_database()
    else:
        print("Database reset cancelled.") 