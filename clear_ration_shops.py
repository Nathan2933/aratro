from flask import Flask
from models import db, User, RationShop
import os
from dotenv import load_dotenv

def clear_ration_shops():
    """
    Script to erase all ration shop users from the database.
    This will:
    1. Delete all RationShop entries
    2. Delete all User entries with role='ration_manager'
    """
    # Create a minimal Flask app to work with the database
    app = Flask(__name__)
    
    # Load environment variables
    load_dotenv()
    
    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///aratro.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database with the app
    db.init_app(app)
    
    # Use the app context
    with app.app_context():
        try:
            # Get all ration shop entries
            ration_shops = RationShop.query.all()
            shop_count = len(ration_shops)
            
            # Get all user IDs associated with ration shops
            user_ids = [shop.user_id for shop in ration_shops if shop.user_id is not None]
            
            # Delete all ration shop entries
            for shop in ration_shops:
                db.session.delete(shop)
            
            print(f"Deleted {shop_count} ration shop entries")
            
            # Delete all users with role='ration_manager'
            users = User.query.filter_by(role='ration_manager').all()
            user_count = len(users)
            
            for user in users:
                db.session.delete(user)
            
            print(f"Deleted {user_count} ration shop user accounts")
            
            # Commit the changes
            db.session.commit()
            print("Database changes committed successfully")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")
            print("Changes rolled back")

if __name__ == "__main__":
    clear_ration_shops()
    print("Operation completed") 