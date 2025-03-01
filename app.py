from flask import Flask, session
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User
from routes import auth, main, farmer_dashboard, warehouse_dashboard
import os
from datetime import timedelta
import requests
from flask import jsonify

app = Flask(__name__)
# Security configurations
app.config['SECRET_KEY'] = os.urandom(24)  # Generate a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///supply_chain.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['GOOGLE_MAPS_API_KEY'] = 'AIzaSyBN9xaw0Vida_n03yQpXL0dGawEqPUS3Jg'

# Session security settings
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session expires after 7 days
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=14)  # Remember me duration
app.config['REMEMBER_COOKIE_HTTPONLY'] = True

# In development, we'll disable secure cookies since we're not using HTTPS
if app.debug:
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['REMEMBER_COOKIE_SECURE'] = False
else:
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_SECURE'] = True

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Specify the login view
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'  # Enable strong session protection

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Session management
@app.before_request
def before_request():
    session.permanent = True  # Use permanent session with lifetime set above

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(main)
app.register_blueprint(farmer_dashboard)
app.register_blueprint(warehouse_dashboard)

@app.route('/test_maps_api')
def test_maps_api():
    api_key = app.config['GOOGLE_MAPS_API_KEY']
    # Test the Geocoding API
    test_url = f"https://maps.googleapis.com/maps/api/geocode/json?address=Chennai&key={api_key}"
    
    try:
        response = requests.get(test_url)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'OK':
                return jsonify({'status': 'success', 'message': 'Google Maps API is working correctly!'})
            else:
                return jsonify({'status': 'error', 'message': f"API Error: {data['status']}"})
        else:
            return jsonify({'status': 'error', 'message': f"HTTP Error: {response.status_code}"})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Connection Error: {str(e)}"})

# Create database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)  # Run without HTTPS in development
