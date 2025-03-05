from app import app, db
from models import RationShop, User

def clear_ration_shops():
    with app.app_context():
        # Get all ration shops
        ration_shops = RationShop.query.all()
        
        print(f"Found {len(ration_shops)} ration shops to delete")
        
        # Delete each ration shop and its associated user
        for shop in ration_shops:
            print(f"Deleting ration shop: {shop.name} (ID: {shop.id})")
            
            # If the shop has an associated user, delete it too
            if shop.user_id:
                user = User.query.get(shop.user_id)
                if user:
                    print(f"  - Deleting associated user (ID: {user.id})")
                    db.session.delete(user)
            
            # Delete the ration shop
            db.session.delete(shop)
        
        # Commit the changes
        db.session.commit()
        print("All ration shops have been deleted successfully")

if __name__ == "__main__":
    clear_ration_shops() 