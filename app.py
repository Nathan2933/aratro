from flask import Flask, session, render_template, request, jsonify
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User, Admin
from routes import auth, main, farmer_dashboard, warehouse_dashboard, admin as admin_blueprint
import os
from datetime import timedelta, datetime
import requests
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app')

# Load environment variables from .env file if it exists
logger.info("Loading environment variables from .env file")
load_dotenv()

app = Flask(__name__)
# Security configurations
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Database configuration
supabase_url = os.environ.get('SUPABASE_DB_URL')
if not supabase_url:
    logger.error("SUPABASE_DB_URL not found in environment variables")
    raise ValueError("SUPABASE_DB_URL must be set in .env file")

app.config['SQLALCHEMY_DATABASE_URI'] = supabase_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,  # Reduced from 20 to prevent too many connections
    'max_overflow': 10,  # Allow up to 10 additional connections when pool is full
    'pool_timeout': 30,  # Timeout after 30 seconds of waiting for a connection
    'pool_recycle': 1800,  # Recycle connections every 30 minutes
    'pool_pre_ping': True,  # Check connection health before using
    'connect_args': {
        'sslmode': 'require',
        'connect_timeout': 10,  # Connection timeout in seconds
        'keepalives': 1,  # Enable TCP keepalive
        'keepalives_idle': 30,  # Time between keepalive probes
        'keepalives_interval': 10,  # Time between probes if previous probe failed
        'keepalives_count': 5,  # Number of failed probes before connection is considered dead
        'application_name': 'aratro'  # Identify your application in database logs
    }
}

app.config['GOOGLE_MAPS_API_KEY'] = os.environ.get('GOOGLE_MAPS_API_KEY', 'AIzaSyCRhQb3mjxdmiYnS3K1NihMxYOO5NULF48')

# Email configuration
# For Gmail:
# 1. If you have 2-factor authentication enabled:
#    - Go to https://myaccount.google.com/apppasswords
#    - Generate an App Password for this application
#    - Use that App Password instead of your regular Gmail password
# 2. If you don't have 2-factor authentication:
#    - Go to https://myaccount.google.com/lesssecureapps
#    - Turn on "Allow less secure apps"
#    - Note: Google may still block the login attempt
app.config['EMAIL_USER'] = os.environ.get('EMAIL_USER', 'aratrocorp@gmail.com')
app.config['EMAIL_PASSWORD'] = os.environ.get('EMAIL_PASSWORD', 'your-app-password-here')
os.environ['EMAIL_USER'] = app.config['EMAIL_USER']
os.environ['EMAIL_PASSWORD'] = app.config['EMAIL_PASSWORD']

# Log email configuration (masking the password)
logger.info(f"Email User: {app.config['EMAIL_USER']}")
logger.info(f"Email Password set: {'Yes' if app.config['EMAIL_PASSWORD'] else 'No'}")
logger.info(f"Email Password length: {len(app.config['EMAIL_PASSWORD']) if app.config['EMAIL_PASSWORD'] else 0}")

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

# Define custom Jinja2 filters
@app.template_filter('timeago')
def timeago_filter(date):
    """Format a date as a human-readable time ago string."""
    if not date:
        return ''
    
    now = datetime.now()
    diff = now - date
    
    seconds = diff.total_seconds()
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24
    
    if seconds < 60:
        return 'just now'
    elif minutes < 60:
        return f'{int(minutes)} minute{"s" if int(minutes) > 1 else ""} ago'
    elif hours < 24:
        return f'{int(hours)} hour{"s" if int(hours) > 1 else ""} ago'
    elif days < 7:
        return f'{int(days)} day{"s" if int(days) > 1 else ""} ago'
    else:
        return date.strftime('%Y-%m-%d')

@login_manager.user_loader
def load_user(user_id):
    try:
        # Check if the user_id has a prefix
        if user_id.startswith('admin_'):
            # Extract the actual ID
            admin_id = int(user_id.split('_')[1])
            return Admin.query.get(admin_id)
        else:
            # Regular user
            return User.query.get(int(user_id))
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

# Session management
@app.before_request
def before_request():
    session.permanent = True  # Use permanent session with lifetime set above

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(main)
app.register_blueprint(farmer_dashboard)
app.register_blueprint(warehouse_dashboard)
app.register_blueprint(admin_blueprint)

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

# Create database and admin user
with app.app_context():
    db.create_all()
    
    # Create admin user if it doesn't exist
    admin_email = 'admin@aratro.com'
    admin_password = 'Admin@123456'  # This should be changed in production
    
    admin = Admin.query.filter_by(email=admin_email).first()
    print(f"Checking for admin user: {admin_email}")
    if not admin:
        print("Admin user not found, creating new admin user")
        admin = Admin(
            email=admin_email,
            password_hash=generate_password_hash(admin_password)
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created successfully with ID: {admin.id}")
    else:
        print(f"Admin user already exists with ID: {admin.id}")
        # Update password if needed
        admin.password_hash = generate_password_hash(admin_password)
        db.session.commit()
        print("Admin password updated")

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Aratro Flask application')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the application on')
    args = parser.parse_args()
    
    # Run the application on the specified port
    app.run(debug=True, port=args.port)  # Run without HTTPS in development
