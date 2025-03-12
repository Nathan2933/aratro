from flask import Flask, session, render_template, request, jsonify, flash, redirect, url_for
from flask_login import LoginManager, current_user, logout_user
from flask_migrate import Migrate
from models import db, User, Admin
from routes import auth, main, farmer_dashboard, warehouse_dashboard, admin as admin_blueprint
from blockchain_routes import blockchain
from blockchain import blockchain_manager as blockchain_mgr, init_blockchain
import os
from datetime import timedelta, datetime, timezone
import requests
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app')

# Load environment variables from .env file if it exists
logger.info("Loading environment variables from .env file")
load_dotenv()

# Determine environment
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
IS_PRODUCTION = FLASK_ENV == 'production'

if IS_PRODUCTION:
    logger.info("Running in PRODUCTION mode")
else:
    logger.info("Running in DEVELOPMENT mode")

app = Flask(__name__)
# Security configurations
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Database configuration
local_db_url = os.environ.get('LOCAL_DB_URL')
supabase_url = os.environ.get('SUPABASE_DB_URL')

# Use local database if specified, otherwise use Supabase
if local_db_url and os.environ.get('USE_LOCAL_DB', 'false').lower() == 'true':
    logger.info("Using LOCAL database")
    app.config['SQLALCHEMY_DATABASE_URI'] = local_db_url
elif supabase_url:
    logger.info("Using SUPABASE database")
    app.config['SQLALCHEMY_DATABASE_URI'] = supabase_url
else:
    logger.error("No database URL found in environment variables")
    raise ValueError("Either LOCAL_DB_URL or SUPABASE_DB_URL must be set in .env file")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,  # Reduced from 20 to prevent too many connections
    'max_overflow': 10,  # Allow up to 10 additional connections when pool is full
    'pool_timeout': 30,  # Timeout after 30 seconds of waiting for a connection
    'pool_recycle': 1800,  # Recycle connections every 30 minutes
    'pool_pre_ping': True,  # Check connection health before using
    'isolation_level': 'AUTOCOMMIT',  # Use autocommit mode to avoid transaction issues
    'connect_args': {
        'sslmode': 'prefer' if not os.environ.get('USE_LOCAL_DB', 'false').lower() == 'true' else 'disable',
        'connect_timeout': 10,  # Connection timeout in seconds
        'keepalives': 1,  # Enable TCP keepalive
        'keepalives_idle': 30,  # Time between keepalive probes
        'keepalives_interval': 10,  # Time between probes if previous probe failed
        'keepalives_count': 5,  # Number of failed probes before connection is considered dead
        'application_name': 'aratro',  # Identify your application in database logs
        'options': '-c statement_timeout=30000'  # 30 second statement timeout
    }
}

app.config['GOOGLE_MAPS_API_KEY'] = os.environ.get('GOOGLE_MAPS_API_KEY', 'AIzaSyCRhQb3mjxdmiYnS3K1NihMxYOO5NULF48')

# Email configuration
app.config['EMAIL_USER'] = os.environ.get('EMAIL_USER', 'aratrocorp@gmail.com')
app.config['EMAIL_PASSWORD'] = os.environ.get('EMAIL_PASSWORD', 'your-app-password-here')
os.environ['EMAIL_USER'] = app.config['EMAIL_USER']
os.environ['EMAIL_PASSWORD'] = app.config['EMAIL_PASSWORD']

# Log email configuration (masking the password)
logger.info(f"Email User: {app.config['EMAIL_USER']}")
logger.info(f"Email Password set: {'Yes' if app.config['EMAIL_PASSWORD'] else 'No'}")
logger.info(f"Email Password length: {len(app.config['EMAIL_PASSWORD']) if app.config['EMAIL_PASSWORD'] else 0}")

# Blockchain configuration
app.config['BLOCKCHAIN_URL'] = os.environ.get('BLOCKCHAIN_URL', 'http://127.0.0.1:7545')
app.config['PRIVATE_KEY'] = os.environ.get('PRIVATE_KEY', '0x0000000000000000000000000000000000000000000000000000000000000000')
os.environ['BLOCKCHAIN_URL'] = app.config['BLOCKCHAIN_URL']
os.environ['PRIVATE_KEY'] = app.config['PRIVATE_KEY']

# Initialize blockchain manager
if blockchain_mgr is None:
    logger.info("Initializing blockchain manager during application startup")
    blockchain_mgr = init_blockchain()
    if blockchain_mgr:
        logger.info(f"Blockchain manager initialized successfully. Connected to {blockchain_mgr.w3.provider.endpoint_uri}")
        logger.info(f"Contract address: {blockchain_mgr.contract_address}")
    else:
        logger.error("Failed to initialize blockchain manager")

# Log blockchain configuration (masking the private key)
logger.info(f"Blockchain URL: {app.config['BLOCKCHAIN_URL']}")
logger.info(f"Private Key set: {'Yes' if app.config['PRIVATE_KEY'] != '0x0000000000000000000000000000000000000000000000000000000000000000' else 'No'}")

# Session security settings
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Session expires after 2 hours (reduced from 7 days)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=1)  # Remember me duration (reduced from 14 days)
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['ADMIN_SESSION_LIFETIME'] = timedelta(minutes=30)  # Admin sessions expire after 30 minutes

# Set secure cookies based on environment
if IS_PRODUCTION:
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_SECURE'] = True
    # Additional production settings
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    app.config['PROPAGATE_EXCEPTIONS'] = False
else:
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['REMEMBER_COOKIE_SECURE'] = False
    # Development settings
    app.config['DEBUG'] = True
    app.config['TESTING'] = False
    app.config['PROPAGATE_EXCEPTIONS'] = True

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
    
    now = datetime.utcnow()
    if not date.tzinfo:
        # If the date has no timezone info, assume it's UTC
        diff = now - date
    else:
        # If the date has timezone info, convert now to UTC for comparison
        now = now.replace(tzinfo=timezone.utc)
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
        logger.error(f"Error loading user: {e}")
        return None

# Session management
@app.before_request
def setup_request():
    # Only make sessions permanent if explicitly requested (via remember me)
    if '_remember' in session and session['_remember']:
        session.permanent = True
    
    # Apply shorter session lifetime for admin users
    if current_user.is_authenticated and hasattr(current_user, 'role') and current_user.role == 'admin':
        app.config['PERMANENT_SESSION_LIFETIME'] = app.config['ADMIN_SESSION_LIFETIME']
        
        # Check if the session is older than the admin timeout
        if 'admin_login_time' in session:
            login_time = datetime.fromisoformat(session['admin_login_time'])
            if datetime.utcnow() - login_time > app.config['ADMIN_SESSION_LIFETIME']:
                # Session expired, log out the user
                session.clear()
                logout_user()
                flash('Your admin session has expired. Please log in again.', 'info')
                return redirect(url_for('admin.login'))
    else:
        # Reset to default session lifetime for non-admin users
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
    
    # Ensure we have a fresh session at the start of each request
    try:
        db.session.rollback()
    except Exception as e:
        logger.error(f"Error rolling back session at request start: {str(e)}")

@app.teardown_request
def teardown_request(exception=None):
    if exception:
        try:
            db.session.rollback()
            logger.warning(f"Transaction rolled back due to exception: {str(exception)}")
        except Exception as e:
            logger.error(f"Error during rollback: {str(e)}")
    try:
        # Always try to rollback any potentially aborted transaction
        db.session.rollback()
        db.session.remove()
    except Exception as e:
        logger.error(f"Error removing session: {str(e)}")

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(main)
app.register_blueprint(farmer_dashboard)
app.register_blueprint(warehouse_dashboard)
app.register_blueprint(admin_blueprint)
app.register_blueprint(blockchain)

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

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin_email = 'admin@aratro.com'
        
        # In production, use a randomly generated password or from environment variable
        if IS_PRODUCTION:
            admin_password = os.environ.get('ADMIN_PASSWORD', os.urandom(24).hex())
            logger.info(f"Using secure admin password in production")
        else:
            admin_password = 'Admin@123456'  # Only for development
            logger.warning(f"Using default admin password in development. DO NOT use in production!")
        
        admin = Admin.query.filter_by(email=admin_email).first()
        logger.info(f"Checking for admin user: {admin_email}")
        if not admin:
            logger.info("Admin user not found, creating new admin user")
            admin = Admin(
                email=admin_email,
                password_hash=generate_password_hash(admin_password)
            )
            db.session.add(admin)
            db.session.commit()
            logger.info(f"Admin user created successfully with ID: {admin.id}")
        else:
            logger.info(f"Admin user already exists with ID: {admin.id}")
            # Update password if needed
            admin.password_hash = generate_password_hash(admin_password)
            db.session.commit()
            logger.info("Admin password updated")

# This is required for Vercel
def handler(request):
    try:
        init_db()  # Initialize database on cold starts
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        
    with app.request_context(request):
        return app(request)

# Keep the app.run() for local development
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Aratro application server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 8080)), help='Port to bind the server to')
    args = parser.parse_args()
    
    print(f"Starting server on http://{args.host}:{args.port}")
    print(f"To access from another machine, use your computer's IP address instead of {args.host}")
    
    init_db()  # Initialize database for local development
    app.run(host=args.host, port=args.port, debug=(not IS_PRODUCTION))
