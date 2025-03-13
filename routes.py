from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, session
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Farmer, Warehouse, Stock, StockRequest, WarehouseRequest, Notification, Admin, RationShop, RationStockRequest, OTP, BlockchainTransaction, CropPrice, StockQualityRating
from blockchain_integration import create_stock_on_blockchain, create_stock_request_on_blockchain, update_stock_request_status_on_blockchain
import re
from datetime import datetime, timedelta
from functools import wraps
from email_utils import send_credentials_email, send_rejection_email, send_password_reset_email, generate_otp, send_otp_via_email, send_otp_via_sms
import uuid
import os
import logging
import traceback
from sqlalchemy import func
from blockchain import get_eth_address

logger = logging.getLogger(__name__)

auth = Blueprint('auth', __name__)
main = Blueprint('main', __name__)
farmer_dashboard = Blueprint('farmer_dashboard', __name__, url_prefix='/farmer')
warehouse_dashboard = Blueprint('warehouse_dashboard', __name__, url_prefix='/warehouse')
admin = Blueprint('admin', __name__, url_prefix='/admin')

@auth.before_request
def before_request():
    if current_user.is_authenticated:
        # Refresh the user session on each request
        session.modified = True

@auth.route('/register')
def register():
    # If user is logged in, show a warning but still allow access to the page
    if current_user.is_authenticated:
        flash('You are already logged in. If you want to create a new account, please log out first.', 'warning')
    return render_template('register.html')

@auth.route('/farmer/register', methods=['GET', 'POST'])
def farmer_register():
    # If user is logged in and trying to submit the form, prevent registration
    if current_user.is_authenticated and request.method == 'POST':
        flash('You are already logged in. Please log out first to create a new account.', 'warning')
        return redirect(url_for('auth.farmer_register'))
    
    # For GET requests, show a warning but allow viewing the page
    if current_user.is_authenticated and request.method == 'GET':
        flash('You are already logged in. If you want to create a new account, please log out first.', 'warning')

    if request.method == 'POST':
        print("Received farmer registration POST request")  # Debug log
        name = request.form.get('name')
        address = request.form.get('address')
        aadhar_number = request.form.get('aadharNumber')
        phone_number = request.form.get('phoneNumber')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')

        print(f"Form data: name={name}, address={address}, aadhar={aadhar_number}, phone={phone_number}")  # Debug log

        # Validate required fields
        if not all([name, address, aadhar_number, phone_number, password, confirm_password]):
            missing = []
            if not name: missing.append('name')
            if not address: missing.append('address')
            if not aadhar_number: missing.append('aadhar number')
            if not phone_number: missing.append('phone number')
            if not password: missing.append('password')
            if not confirm_password: missing.append('confirm password')
            print(f"Missing fields: {', '.join(missing)}")  # Debug log
            flash('All fields are required', 'error')
            return redirect(url_for('auth.farmer_register'))

        # Validate password match
        if password != confirm_password:
            print("Password mismatch")  # Debug log
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.farmer_register'))

        # Validate password length
        if len(password) < 8:
            print("Password too short")  # Debug log
            flash('Password must be at least 8 characters long', 'error')
            return redirect(url_for('auth.farmer_register'))

        # Validate Aadhar number format
        if not aadhar_number.isdigit() or len(aadhar_number) != 12:
            print(f"Invalid Aadhar number format: {aadhar_number}")  # Debug log
            flash('Invalid Aadhar number. Must be 12 digits', 'error')
            return redirect(url_for('auth.farmer_register'))

        # Validate phone number format
        if not phone_number.isdigit() or len(phone_number) != 10:
            print(f"Invalid phone number format: {phone_number}")  # Debug log
            flash('Invalid phone number. Must be 10 digits', 'error')
            return redirect(url_for('auth.farmer_register'))

        # Check if user already exists
        user = User.query.filter_by(phone_number=phone_number).first()
        if user:
            print(f"Phone number {phone_number} already registered")  # Debug log
            flash('Phone number already registered', 'error')
            return redirect(url_for('auth.farmer_register'))

        # Check if Aadhar is already registered
        farmer = Farmer.query.filter_by(aadhar_number=aadhar_number).first()
        if farmer:
            print(f"Aadhar number {aadhar_number} already registered")  # Debug log
            flash('Aadhar number already registered', 'error')
            return redirect(url_for('auth.farmer_register'))

        try:
            print("Creating new user and farmer records")  # Debug log
            # Create new user
            user = User(
                phone_number=phone_number,
                password_hash=generate_password_hash(password),
                role='farmer'
            )
            db.session.add(user)
            db.session.flush()  # Get user.id before committing
            print(f"Created user with ID: {user.id}")  # Debug log

            # Create farmer profile
            farmer = Farmer(
                user_id=user.id,
                name=name,
                address=address,
                aadhar_number=aadhar_number,
                phone_number=phone_number
            )
            db.session.add(farmer)
            print("Added farmer to session")  # Debug log
            
            # Import the function to generate Ethereum addresses
            from blockchain import get_eth_address
            
            # Assign Ethereum address to user
            user.eth_address = get_eth_address(user.id, user.role)
            print(f"Assigned Ethereum address to user: {user.eth_address}")  # Debug log
            
            # Assign Ethereum address to farmer
            farmer.eth_address = get_eth_address(farmer.id, 'farmer')
            print(f"Assigned Ethereum address to farmer: {farmer.eth_address}")  # Debug log
            
            db.session.commit()
            print("Database commit successful")  # Debug log
            login_user(user)
            flash('Registration successful!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            print(f"Error during registration: {str(e)}")  # Debug log
            flash(f'Error during registration: {str(e)}', 'error')
            return redirect(url_for('auth.farmer_register'))

    return render_template('farmer_register.html')

@auth.route('/warehouse/register', methods=['GET', 'POST'])
def warehouse_register():
    # If user is logged in and trying to submit the form, prevent registration
    if current_user.is_authenticated and request.method == 'POST':
        flash('You are already logged in. Please log out first to create a new account.', 'warning')
        return redirect(url_for('auth.warehouse_register'))
    
    # For GET requests, show a warning but allow viewing the page
    if current_user.is_authenticated and request.method == 'GET':
        flash('You are already logged in. If you want to create a new account, please log out first.', 'warning')

    if request.method == 'POST':
        print("Form Data:", request.form)  # Debug print
        manager_name = request.form.get('managerName')
        warehouse_name = request.form.get('warehouseName')
        phone_number = request.form.get('phoneNumber')
        warehouse_type = request.form.get('warehouseType')
        capacity = request.form.get('capacity')
        location = request.form.get('location')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        password = request.form.get('password')

        print(f"Debug - Received data: manager={manager_name}, warehouse={warehouse_name}, type={warehouse_type}, capacity={capacity}")  # Debug print

        # Validate required fields
        if not all([manager_name, warehouse_name, phone_number, warehouse_type, capacity, location, latitude, longitude, password]):
            missing_fields = []
            if not manager_name: missing_fields.append("Manager Name")
            if not warehouse_name: missing_fields.append("Warehouse Name")
            if not phone_number: missing_fields.append("Phone Number")
            if not warehouse_type: missing_fields.append("Warehouse Type")
            if not capacity: missing_fields.append("Capacity")
            if not location: missing_fields.append("Location")
            if not latitude or not longitude: missing_fields.append("Map Location")
            if not password: missing_fields.append("Password")
            
            flash(f'Missing required fields: {", ".join(missing_fields)}', 'error')
            return redirect(url_for('auth.warehouse_register'))

        try:
            capacity = float(capacity)
        except (TypeError, ValueError):
            flash('Invalid capacity value. Please enter a valid number.', 'error')
            return redirect(url_for('auth.warehouse_register'))

        # Check if user already exists
        user = User.query.filter_by(phone_number=phone_number).first()
        if user:
            flash('Phone number already registered')
            return redirect(url_for('auth.warehouse_register'))

        try:
            # Create new user
            user = User(
                phone_number=phone_number,
                password_hash=generate_password_hash(password),
                role='warehouse_manager'
            )
            db.session.add(user)
            db.session.flush()
            
            # Import the function to generate Ethereum addresses
            from blockchain import get_eth_address
            
            # Assign Ethereum address to user
            user.eth_address = get_eth_address(user.id, user.role)
            print(f"Assigned Ethereum address to user: {user.eth_address}")  # Debug log

            # Create warehouse profile
            warehouse = Warehouse(
                user_id=user.id,
                manager_name=manager_name,
                name=warehouse_name,
                location=location,
                latitude=float(latitude),
                longitude=float(longitude),
                warehouse_type=warehouse_type,
                phone_number=phone_number,
                capacity=capacity,
                available_space=capacity
            )
            db.session.add(warehouse)
            db.session.flush()
            
            # Assign Ethereum address to warehouse
            warehouse.eth_address = get_eth_address(warehouse.id, 'warehouse')
            print(f"Assigned Ethereum address to warehouse: {warehouse.eth_address}")  # Debug log
            
            db.session.commit()
            print("Database commit successful")  # Debug print
            login_user(user)
            flash('Registration successful!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            print(f"Error during registration: {str(e)}")  # Debug print
            flash(f'Error during registration: {str(e)}', 'error')
            return redirect(url_for('auth.warehouse_register'))

    return render_template('warehouse_register.html', maps_api_key=current_app.config['GOOGLE_MAPS_API_KEY'])

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        password = request.form.get('password')
        selected_role = request.form.get('role')
        remember = True if request.form.get('remember') else False
        
        if not phone_number or not password or not selected_role:
            flash('Please enter all required fields', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(phone_number=phone_number).first()
        
        if not user:
            flash('No account found with this phone number. Please check your number or register.', 'error')
            return redirect(url_for('auth.login'))
        
        # Map selected role to database role
        role_mapping = {
            'farmer': 'farmer',
            'warehouse': 'warehouse_manager',
            'ration': 'ration_manager'
        }
        
        # Check if the selected role matches the user's actual role
        if role_mapping.get(selected_role) != user.role:
            flash('Invalid login attempt. Please select the correct role for your account.', 'error')
            return redirect(url_for('auth.login'))
        
        if not check_password_hash(user.password_hash, password):
            flash('Incorrect password. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        try:
            login_user(user, remember=remember)
            
            # Redirect to appropriate dashboard based on role
            if user.role == 'ration_manager':
                return redirect(url_for('main.ration_dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        except Exception as e:
            flash('An error occurred during login. Please try again.', 'error')
            return redirect(url_for('auth.login'))
    
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    # Clear all session data
    session.clear()
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Route for initiating the forgot password process"""
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        role = request.form.get('role')
        
        if not phone_number or not role:
            flash('Please enter your phone number and select your role', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        # Validate phone number format
        if not phone_number.isdigit() or len(phone_number) != 10:
            flash('Invalid phone number. Must be 10 digits', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        # Map selected role to database role
        role_mapping = {
            'farmer': 'farmer',
            'warehouse': 'warehouse_manager',
            'ration': 'ration_manager'
        }
        
        db_role = role_mapping.get(role)
        if not db_role:
            flash('Invalid role selected', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        # Check if user exists with this phone number and role
        user = User.query.filter_by(phone_number=phone_number, role=db_role).first()
        if not user:
            flash('No account found with this phone number and role', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        # Generate OTP
        otp_code = generate_otp()
        
        # Set expiration time (10 minutes from now)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Save OTP to database
        otp = OTP(
            phone_number=phone_number,
            otp_code=otp_code,
            expires_at=expires_at
        )
        db.session.add(otp)
        db.session.commit()
        
        # Send OTP via SMS using Twilio
        send_otp_via_sms(phone_number, otp_code)
        
        # If user is a farmer, also send OTP via email if available
        if db_role == 'farmer':
            farmer = Farmer.query.filter_by(user_id=user.id).first()
            if farmer:
                # In a real application, you would check if the farmer has an email
                # For now, we'll simulate sending to a dummy email
                dummy_email = f"{phone_number}@example.com"
                send_otp_via_email(dummy_email, phone_number, otp_code)
        
        # If user is a warehouse manager, also send OTP via email if available
        elif db_role == 'warehouse_manager':
            warehouse = Warehouse.query.filter_by(user_id=user.id).first()
            if warehouse:
                # In a real application, you would check if the warehouse has an email
                # For now, we'll simulate sending to a dummy email
                dummy_email = f"{phone_number}@example.com"
                send_otp_via_email(dummy_email, phone_number, otp_code)
        
        # If user is a ration shop manager, also send OTP via email
        elif db_role == 'ration_manager':
            ration_shop = RationShop.query.filter_by(user_id=user.id).first()
            if ration_shop and ration_shop.email:
                send_otp_via_email(ration_shop.email, phone_number, otp_code)
        
        # Store phone number and role in session for the next step
        session['reset_phone_number'] = phone_number
        session['reset_role'] = db_role
        
        flash('OTP has been sent to your phone number. Please enter it to reset your password.', 'success')
        return redirect(url_for('auth.verify_otp'))
    
    return render_template('forgot_password.html')

@auth.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Route for verifying the OTP"""
    # Check if we have the necessary session data
    if 'reset_phone_number' not in session or 'reset_role' not in session:
        flash('Please start the password reset process again', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    phone_number = session['reset_phone_number']
    
    if request.method == 'POST':
        otp_code = request.form.get('otp_code')
        
        if not otp_code:
            flash('Please enter the OTP sent to your phone', 'error')
            return redirect(url_for('auth.verify_otp'))
        
        # Find the most recent valid OTP for this phone number
        otp = OTP.query.filter_by(
            phone_number=phone_number,
            is_used=False
        ).order_by(OTP.created_at.desc()).first()
        
        if not otp:
            flash('No valid OTP found. Please request a new one.', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        # Check if OTP has expired
        if datetime.utcnow() > otp.expires_at:
            flash('OTP has expired. Please request a new one.', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        # Verify OTP
        if otp.otp_code != otp_code:
            flash('Invalid OTP. Please try again.', 'error')
            return redirect(url_for('auth.verify_otp'))
        
        # Mark OTP as used
        otp.is_used = True
        db.session.commit()
        
        # Store verification in session
        session['otp_verified'] = True
        
        flash('OTP verified successfully. Please set your new password.', 'success')
        return redirect(url_for('auth.reset_password'))
    
    return render_template('verify_otp.html', phone_number=phone_number)

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Route for setting a new password after OTP verification"""
    # Check if we have the necessary session data and OTP verification
    if 'reset_phone_number' not in session or 'reset_role' not in session or 'otp_verified' not in session:
        flash('Please complete the verification process first', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    phone_number = session['reset_phone_number']
    role = session['reset_role']
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or not confirm_password:
            flash('Please enter and confirm your new password', 'error')
            return redirect(url_for('auth.reset_password'))
        
        # Validate password match
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.reset_password'))
        
        # Validate password length
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return redirect(url_for('auth.reset_password'))
        
        # Find the user
        user = User.query.filter_by(phone_number=phone_number, role=role).first()
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        # Update the password
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        # Clear session data
        session.pop('reset_phone_number', None)
        session.pop('reset_role', None)
        session.pop('otp_verified', None)
        
        flash('Your password has been reset successfully. Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html')

@auth.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Route for resending OTP"""
    # Check if we have the necessary session data
    if 'reset_phone_number' not in session or 'reset_role' not in session:
        flash('Please start the password reset process again', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    phone_number = session['reset_phone_number']
    role = session['reset_role']
    
    # Find the user
    user = User.query.filter_by(phone_number=phone_number, role=role).first()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    # Generate new OTP
    otp_code = generate_otp()
    
    # Set expiration time (10 minutes from now)
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Save OTP to database
    otp = OTP(
        phone_number=phone_number,
        otp_code=otp_code,
        expires_at=expires_at
    )
    db.session.add(otp)
    db.session.commit()
    
    # Send OTP via SMS using Twilio
    send_otp_via_sms(phone_number, otp_code)
    
    # If user is a farmer, also send OTP via email if available
    if role == 'farmer':
        farmer = Farmer.query.filter_by(user_id=user.id).first()
        if farmer:
            # In a real application, you would check if the farmer has an email
            # For now, we'll simulate sending to a dummy email
            dummy_email = f"{phone_number}@example.com"
            send_otp_via_email(dummy_email, phone_number, otp_code)
    
    # If user is a warehouse manager, also send OTP via email if available
    elif role == 'warehouse_manager':
        warehouse = Warehouse.query.filter_by(user_id=user.id).first()
        if warehouse:
            # In a real application, you would check if the warehouse has an email
            # For now, we'll simulate sending to a dummy email
            dummy_email = f"{phone_number}@example.com"
            send_otp_via_email(dummy_email, phone_number, otp_code)
    
    # If user is a ration shop manager, also send OTP via email if available
    elif role == 'ration_manager':
        ration_shop = RationShop.query.filter_by(user_id=user.id).first()
        if ration_shop and ration_shop.email:
            send_otp_via_email(ration_shop.email, phone_number, otp_code)
    
    flash('A new OTP has been sent to your phone number', 'success')
    return redirect(url_for('auth.verify_otp'))

@main.before_request
def check_user_account():
    if current_user.is_authenticated:
        # Check if the user's role matches their account type
        if current_user.role == 'warehouse_manager':
            warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
            if not warehouse:
                logout_user()
                flash('Account verification failed. Please log in again.', 'error')
                return redirect(url_for('auth.login'))
        elif current_user.role == 'farmer':
            farmer = Farmer.query.filter_by(user_id=current_user.id).first()
            if not farmer:
                logout_user()
                flash('Account verification failed. Please log in again.', 'error')
                return redirect(url_for('auth.login'))

# Farmer Dashboard Routes
@farmer_dashboard.route('/')
@login_required
def farmer_home():
    # Check if user is a farmer
    if current_user.role != 'farmer':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get the farmer object
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    
    if not farmer:
        flash('Farmer profile not found', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get all stock requests for this farmer
    stock_requests = StockRequest.query.filter_by(from_id=farmer.id).all()
    
    # Get all warehouse announcements
    warehouse_announcements = WarehouseRequest.query.filter_by(status='open').all()
    
    # Get all crop prices set by admin
    crop_prices = CropPrice.query.all()
    
    # Count statistics for the dashboard
    pending_count = StockRequest.query.filter_by(from_id=farmer.id, status='pending').count()
    accepted_count = StockRequest.query.filter_by(from_id=farmer.id, status='stored').count()
    rejected_count = StockRequest.query.filter_by(from_id=farmer.id, status='rejected').count()
    partial_count = StockRequest.query.filter_by(from_id=farmer.id, status='partial').count()
    
    # Get all warehouses for the create request form
    warehouses = Warehouse.query.all()
    
    return render_template('farmer_dashboard.html', 
                          farmer=farmer,
                          stock_requests=stock_requests,
                          warehouse_announcements=warehouse_announcements,
                          pending_count=pending_count,
                          accepted_count=accepted_count,
                          rejected_count=rejected_count,
                          partial_count=partial_count,
                          warehouses=warehouses,
                          crop_prices=crop_prices)

@farmer_dashboard.route('/create_request', methods=['GET', 'POST'])
@login_required
def create_request_page():
    # Check if user is a farmer
    if current_user.role != 'farmer':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get the farmer object
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    
    if not farmer:
        flash('Farmer profile not found', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get all warehouses for the create request form
    warehouses = Warehouse.query.all()
    
    # Get all crop prices set by admin
    crop_prices = CropPrice.query.all()
    
    # Get warehouse request if specified in URL
    warehouse_request_id = request.args.get('warehouse_request_id')
    warehouse_request = None
    if warehouse_request_id:
        warehouse_request = WarehouseRequest.query.get(warehouse_request_id)
    
    return render_template('create_request.html', 
                          farmer=farmer,
                          warehouses=warehouses,
                          warehouse_request=warehouse_request,
                          crop_prices=crop_prices)

@farmer_dashboard.route('/view_requests')
@login_required
def view_requests_page():
    if current_user.role != 'farmer':
        flash('Access denied: You must be a farmer to view this page', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get open warehouse requests
    try:
        warehouse_requests = WarehouseRequest.query.filter_by(status='open').order_by(WarehouseRequest.date_posted.desc()).all()
    except Exception as e:
        warehouse_requests = []
        flash('Error loading warehouse requests', 'error')
    
    return render_template('view_requests.html', warehouse_requests=warehouse_requests)

@farmer_dashboard.route('/warehouse_request_details/<int:request_id>')
@login_required
def warehouse_request_details(request_id):
    if current_user.role != 'farmer':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        warehouse_request = WarehouseRequest.query.get(request_id)
        if not warehouse_request:
            return jsonify({'success': False, 'message': 'Warehouse request not found'})
        
        warehouse = Warehouse.query.get(warehouse_request.warehouse_id)
        
        request_data = {
            'id': warehouse_request.id,
            'warehouse_id': warehouse_request.warehouse_id,
            'warehouse_name': warehouse.name,
            'stock_type': warehouse_request.stock_type,
            'quantity': warehouse_request.quantity,
            'price_per_ton': warehouse_request.price_per_ton,
            'date_posted': warehouse_request.date_posted.strftime('%Y-%m-%d'),
            'expiry_date': warehouse_request.expiry_date.strftime('%Y-%m-%d'),
            'description': warehouse_request.description
        }
        
        return jsonify({'success': True, 'request': request_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@farmer_dashboard.route('/submit_request', methods=['POST'])
@login_required
def submit_request():
    if current_user.role != 'farmer':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    warehouse_id = request.form.get('warehouse_id')
    stock_type = request.form.get('stock_type')
    quantity = request.form.get('quantity')
    
    if stock_type == 'Other':
        stock_type = request.form.get('other_stock_type')
    
    if not all([warehouse_id, stock_type, quantity]):
        flash('All required fields must be filled', 'error')
        return redirect(url_for('farmer_dashboard.create_request_page'))
    
    try:
        quantity = float(quantity)
        warehouse = Warehouse.query.get(warehouse_id)
        
        if not warehouse:
            flash('Selected warehouse not found', 'error')
            return redirect(url_for('farmer_dashboard.create_request_page'))
        
        if quantity <= 0:
            flash('Quantity must be greater than zero', 'error')
            return redirect(url_for('farmer_dashboard.create_request_page'))
        
        farmer = Farmer.query.filter_by(user_id=current_user.id).first()
        
        # Create a stock entry with requested quantity
        stock = Stock(
            type=stock_type,
            quantity=quantity,
            farmer_id=farmer.id,
            warehouse_id=warehouse.id,
            status='pending',
            requested_quantity=quantity  # Store the original requested quantity
        )
        db.session.add(stock)
        db.session.flush()
        
        # Create request
        new_request = StockRequest(
            from_id=farmer.id,
            to_id=warehouse.id,
            stock_id=stock.id,
            status='pending'
        )
        db.session.add(new_request)
        db.session.commit()
        
        # Add blockchain integration
        try:
            # Import the blockchain integration functions
            from blockchain_integration import create_stock_on_blockchain, create_stock_request_on_blockchain, update_stock_request_status_on_blockchain
            
            # Create stock on blockchain
            stock_blockchain_success = create_stock_on_blockchain(stock.id)
            if stock_blockchain_success:
                # Create stock request on blockchain
                request_blockchain_success = create_stock_request_on_blockchain(new_request.id)
                if request_blockchain_success:
                    flash('Stock request submitted and recorded on blockchain successfully', 'success')
                else:
                    # Log the error for debugging
                    logger.error(f"Failed to create stock request {new_request.id} on blockchain")
                    flash('Stock request submitted but failed to record on blockchain', 'warning')
            else:
                # Log the error for debugging
                logger.error(f"Failed to create stock {stock.id} on blockchain")
                flash('Stock request submitted but failed to record stock on blockchain', 'warning')
        except Exception as e:
            # Log the exception for debugging
            logger.error(f"Blockchain integration failed: {str(e)}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            flash(f'Stock request submitted but blockchain integration failed: {str(e)}', 'warning')
        
        return redirect(url_for('farmer_dashboard.farmer_home'))
        
    except ValueError:
        flash('Invalid quantity value', 'error')
        return redirect(url_for('farmer_dashboard.create_request_page'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting request: {str(e)}', 'error')
        return redirect(url_for('farmer_dashboard.create_request_page'))

@farmer_dashboard.route('/request_details/<int:request_id>')
@login_required
def request_details(request_id):
    if current_user.role != 'farmer':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    
    # Try to get request using new schema
    try:
        stock_request = StockRequest.query.filter_by(id=request_id, farmer_id=farmer.id).first()
        if stock_request:
            warehouse = Warehouse.query.get(stock_request.warehouse_id)
            
            request_data = {
                'id': stock_request.id,
                'warehouse_id': stock_request.warehouse_id,
                'warehouse_name': warehouse.name,
                'stock_type': stock_request.stock_type,
                'quantity': stock_request.quantity,
                'status': stock_request.status,
                'date_requested': stock_request.date_requested.strftime('%Y-%m-%d %H:%M'),
                'notes': stock_request.notes,
                'admin_notes': stock_request.admin_notes
            }
            
            if hasattr(stock_request, 'date_processed') and stock_request.date_processed:
                request_data['date_processed'] = stock_request.date_processed.strftime('%Y-%m-%d %H:%M')
            
            return jsonify({'success': True, 'request': request_data})
    except Exception as e:
        # If new schema fails, try old schema
        try:
            stock_request = StockRequest.query.filter_by(id=request_id, to_id=farmer.id).first()
            if stock_request:
                warehouse = Warehouse.query.get(stock_request.from_id)
                
                request_data = {
                    'id': stock_request.id,
                    'warehouse_id': stock_request.from_id,
                    'warehouse_name': warehouse.name if warehouse else "Unknown",
                    'stock_type': stock_request.crop_type if hasattr(stock_request, 'crop_type') else "Unknown",
                    'quantity': stock_request.quantity,
                    'status': stock_request.status,
                    'date_requested': stock_request.request_date.strftime('%Y-%m-%d %H:%M') if hasattr(stock_request, 'request_date') else "Unknown",
                    'notes': "",
                    'admin_notes': ""
                }
                
                return jsonify({'success': True, 'request': request_data})
        except Exception as inner_e:
            pass
    
    return jsonify({'success': False, 'message': 'Request not found'})

@farmer_dashboard.route('/cancel_request/<int:request_id>', methods=['POST'])
@login_required
def cancel_request(request_id):
    if current_user.role != 'farmer':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    if not farmer:
        return jsonify({'success': False, 'message': 'Farmer profile not found'})
    
    try:
        stock_request = StockRequest.query.filter_by(id=request_id, from_id=farmer.id, status='pending').first()
        if stock_request:
            stock_request.status = 'canceled'
            stock_request.stock.status = 'canceled'  # Update the associated stock status
            
            # Create notification for warehouse manager
            notification = Notification(
                user_id=stock_request.warehouse.user.id,
                title='Stock Request Canceled',
                message=f'Stock request for {stock_request.stock.requested_quantity} tons of {stock_request.stock.type} has been canceled by {farmer.name}',
                type='request_canceled'
            )
            db.session.add(notification)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Request canceled successfully'})
        else:
            return jsonify({'success': False, 'message': 'Request not found or cannot be canceled'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@farmer_dashboard.route('/rejected-requests')
@login_required
def rejected_requests():
    if current_user.role != 'farmer':
        flash('Access denied. Farmers only.', 'error')
        return redirect(url_for('main.dashboard'))
    
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    if not farmer:
        flash('Farmer profile not found.', 'error')
        return redirect(url_for('main.dashboard'))
    
    requests = StockRequest.query.filter_by(
        from_id=farmer.id,
        status='rejected'
    ).order_by(StockRequest.updated_at.desc()).all()
    
    warehouses = Warehouse.query.all()
    
    return render_template('rejected_requests.html', requests=requests, warehouses=warehouses)

@farmer_dashboard.route('/partial-acceptances')
@login_required
def partial_acceptances():
    if current_user.role != 'farmer':
        flash('Access denied: You must be a farmer to view this page', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get the farmer's ID
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    if not farmer:
        flash('Farmer profile not found', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get partially accepted requests
    partial_requests = StockRequest.query.filter_by(farmer_id=farmer.id, status='partially_accepted').order_by(StockRequest.date_requested.desc()).all()
    
    return render_template('partial_acceptances.html', partial_requests=partial_requests)

@farmer_dashboard.route('/accepted-requests')
@login_required
def accepted_requests():
    if current_user.role != 'farmer':
        flash('Access denied: You must be a farmer to view this page', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get the farmer's ID
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    if not farmer:
        flash('Farmer profile not found', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get accepted requests with quality rating and price info
    accepted_requests = (StockRequest.query
        .filter_by(from_id=farmer.id, status='stored')
        .join(Stock)
        .outerjoin(StockQualityRating)
        .join(CropPrice, CropPrice.crop_type == Stock.type)
        .add_columns(CropPrice.price_per_kg)
        .order_by(StockRequest.request_date.desc())
        .all())
    
    return render_template('accepted_requests.html', accepted_requests=accepted_requests)

@farmer_dashboard.route('/pending-requests')
@login_required
def pending_requests():
    """
    Display pending requests for the farmer
    """
    if current_user.role != 'farmer':
        flash('Access denied. You must be a farmer to view this page.', 'error')
        return redirect(url_for('main.index'))
    
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    if not farmer:
        flash('Farmer profile not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get pending requests for this farmer
    pending_requests = StockRequest.query.filter_by(
        from_id=farmer.id, 
        status='pending'
    ).order_by(StockRequest.request_date.desc()).all()
    
    return render_template(
        'pending_requests.html',
        pending_requests=pending_requests,
        user_farmer=farmer
    )

# Warehouse Dashboard Routes
@warehouse_dashboard.route('/')
@login_required
def warehouse_home():
    # Check if user is a warehouse manager
    if current_user.role != 'warehouse_manager':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get the warehouse object
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    
    if not warehouse:
        flash('Warehouse profile not found', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get all stock requests for this warehouse
    stock_requests = StockRequest.query.filter_by(to_id=warehouse.id).all()
    
    # Get all ration shop requests for this warehouse
    ration_requests = RationStockRequest.query.filter_by(warehouse_id=warehouse.id).all()
    
    # Get all crop prices set by admin
    crop_prices = CropPrice.query.all()
    
    # Count statistics for the dashboard
    pending_count = StockRequest.query.filter_by(to_id=warehouse.id, status='pending').count()
    accepted_count = StockRequest.query.filter_by(to_id=warehouse.id, status='stored').count()
    rejected_count = StockRequest.query.filter_by(to_id=warehouse.id, status='rejected').count()
    
    # Count ration shop request statistics
    ration_pending_count = RationStockRequest.query.filter_by(warehouse_id=warehouse.id, status='pending').count()
    ration_accepted_count = RationStockRequest.query.filter_by(warehouse_id=warehouse.id, status='approved').count()
    ration_rejected_count = RationStockRequest.query.filter_by(warehouse_id=warehouse.id, status='rejected').count()
    
    # Total counts (farmer + ration shop)
    total_pending_count = pending_count + ration_pending_count
    total_accepted_count = accepted_count + ration_accepted_count
    total_rejected_count = rejected_count + ration_rejected_count
    
    # Get all stocks in this warehouse
    stocks = Stock.query.filter_by(warehouse_id=warehouse.id, status='stored').all()
    
    # Calculate total stock by type
    stock_by_type = {}
    for stock in stocks:
        if stock.type in stock_by_type:
            stock_by_type[stock.type] += stock.quantity
        else:
            stock_by_type[stock.type] = stock.quantity
    
    # Calculate total allocated space
    total_allocated_space = sum(stock.quantity for stock in stocks)
    
    # Update the available space in the warehouse model
    warehouse.available_space = warehouse.capacity - total_allocated_space
    
    # Get recent requests (both farmer and ration shop)
    farmer_recent_requests = StockRequest.query.filter_by(to_id=warehouse.id).order_by(StockRequest.request_date.desc()).limit(5).all()
    ration_recent_requests = RationStockRequest.query.filter_by(warehouse_id=warehouse.id).order_by(RationStockRequest.request_date.desc()).limit(5).all()
    
    # Combine and sort recent requests
    recent_requests = sorted(
        farmer_recent_requests + ration_recent_requests,
        key=lambda x: x.request_date,
        reverse=True
    )[:5]  # Get the 5 most recent requests
    
    return render_template('warehouse_dashboard.html', 
                          warehouse=warehouse,
                          stock_requests=stock_requests,
                          ration_requests=ration_requests,
                          pending_requests=StockRequest.query.filter_by(to_id=warehouse.id, status='pending').all(),
                          accepted_requests=StockRequest.query.filter_by(to_id=warehouse.id, status='stored').all(),
                          rejected_requests=StockRequest.query.filter_by(to_id=warehouse.id, status='rejected').all(),
                          ration_pending_requests=RationStockRequest.query.filter_by(warehouse_id=warehouse.id, status='pending').all(),
                          ration_accepted_requests=RationStockRequest.query.filter_by(warehouse_id=warehouse.id, status='approved').all(),
                          ration_rejected_requests=RationStockRequest.query.filter_by(warehouse_id=warehouse.id, status='rejected').all(),
                          recent_requests=recent_requests,
                          pending_count=pending_count,
                          accepted_count=accepted_count,
                          rejected_count=rejected_count,
                          ration_pending_count=ration_pending_count,
                          ration_accepted_count=ration_accepted_count,
                          ration_rejected_count=ration_rejected_count,
                          total_pending_count=total_pending_count,
                          total_accepted_count=total_accepted_count,
                          total_rejected_count=total_rejected_count,
                          stocks=stocks,
                          stock_by_type=stock_by_type,
                          total_allocated_space=total_allocated_space,
                          crop_prices=crop_prices)

@warehouse_dashboard.route('/respond_to_ration_request', methods=['POST'])
@login_required
def respond_to_ration_request():
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    # Get the warehouse data
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    if not warehouse:
        return jsonify({'success': False, 'message': 'Warehouse not found'}), 404

    # Get form data
    data = request.json if request.is_json else request.form
    request_id = data.get('request_id')
    action = data.get('action')
    notes = data.get('notes', '')
    
    if not request_id or not action:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Find the request
    stock_request = RationStockRequest.query.get(request_id)
    if not stock_request or stock_request.warehouse_id != warehouse.id:
        return jsonify({'success': False, 'message': 'Request not found'}), 404

    if stock_request.status != 'pending':
        return jsonify({'success': False, 'message': 'Request has already been processed'}), 400

    # Get ration shop
    ration_shop = RationShop.query.get(stock_request.ration_shop_id)
    if not ration_shop:
        return jsonify({'success': False, 'message': 'Ration shop not found'}), 404

    # Process the request based on action
    if action == 'approve':
        # Check if warehouse has enough stock of the requested type
        available_stocks = Stock.query.filter_by(
            warehouse_id=warehouse.id,
            type=stock_request.stock_type,
            status='stored'
        ).order_by(Stock.created_at).all()
        
        total_available_quantity = sum(stock.quantity for stock in available_stocks)
        
        if total_available_quantity < stock_request.quantity:
            return jsonify({
                'success': False, 
                'message': f'Not enough stock available. Available: {total_available_quantity} tons, Requested: {stock_request.quantity} tons'
            }), 400
        
        # Approve the request
        stock_request.status = 'approved'
        stock_request.processed_date = datetime.utcnow()
        stock_request.admin_notes = notes
        
        # Reduce stock from warehouse (FIFO - First In First Out)
        remaining_quantity_to_reduce = stock_request.quantity
        for stock in available_stocks:
            if remaining_quantity_to_reduce <= 0:
                break
                
            if stock.quantity <= remaining_quantity_to_reduce:
                # Use entire stock
                remaining_quantity_to_reduce -= stock.quantity
                stock.quantity = 0
                stock.status = 'transferred'  # Mark as transferred to ration shop
            else:
                # Use partial stock
                stock.quantity -= remaining_quantity_to_reduce
                remaining_quantity_to_reduce = 0
        
        # Create notification for ration shop
        notification = Notification(
            user_id=ration_shop.user_id,
            title='Stock Request Approved',
            message=f'Your request for {stock_request.quantity} tons of {stock_request.stock_type} has been approved by {warehouse.name}.',
            type='ration_stock_request_approved'
        )
        db.session.add(notification)
        
    elif action == 'reject':
        # Reject the request
        stock_request.status = 'rejected'
        stock_request.processed_date = datetime.utcnow()
        stock_request.admin_notes = notes
        
        # Create notification for ration shop
        notification = Notification(
            user_id=ration_shop.user_id,
            title='Stock Request Rejected',
            message=f'Your request for {stock_request.quantity} tons of {stock_request.stock_type} has been rejected by {warehouse.name}.',
            type='ration_stock_request_rejected'
        )
        db.session.add(notification)
    else:
        return jsonify({'success': False, 'message': 'Invalid action'}), 400
    
    try:
        db.session.commit()
        
        # Add blockchain integration
        try:
            # Import the blockchain integration functions
            from blockchain_integration import update_ration_stock_request_status_on_blockchain
            
            # Update ration stock request status on blockchain
            blockchain_success = update_ration_stock_request_status_on_blockchain(
                stock_request.id, 
                stock_request.status, 
                stock_request.admin_notes or ""
            )
            
            if blockchain_success:
                # Create blockchain notification for ration shop
                blockchain_notification = Notification(
                    user_id=ration_shop.user_id,
                    title='Blockchain Update',
                    message=f'Your request status update to "{stock_request.status}" has been recorded on the blockchain.',
                    type='blockchain_notification'
                )
                db.session.add(blockchain_notification)
                db.session.commit()
                
                return jsonify({
                    'success': True, 
                    'message': f'Request {action}d and recorded on blockchain successfully',
                    'blockchain': True,
                    'request_id': stock_request.id
                }), 200
            else:
                # Log the error for debugging
                logger.error(f"Failed to update ration stock request {stock_request.id} status on blockchain")
                return jsonify({
                    'success': True, 
                    'message': f'Request {action}d but failed to record on blockchain. The system will retry automatically.',
                    'blockchain': False,
                    'request_id': stock_request.id
                }), 200
        except Exception as e:
            # Log the exception for debugging
            logger.error(f"Blockchain integration failed: {str(e)}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            return jsonify({
                'success': True, 
                'message': f'Request {action}d but blockchain integration failed: {str(e)}. The system will retry automatically.',
                'blockchain': False,
                'request_id': stock_request.id
            }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error processing request: {str(e)}'}), 500

@warehouse_dashboard.route('/respond_to_request', methods=['GET', 'POST'])
@login_required
def respond_to_request():
    # Import blockchain functions
    from blockchain_integration import create_stock_on_blockchain, create_stock_request_on_blockchain, update_stock_request_status_on_blockchain
    
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    
    # Get the warehouse data
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    if not warehouse:
        return jsonify({'success': False, 'message': 'Warehouse not found'}), 404
    
    if request.method == 'GET':
        # Get all pending requests for this warehouse
        pending_requests = StockRequest.query.filter_by(to_id=warehouse.id, status='pending').order_by(StockRequest.created_at.desc()).all()
        
        # Get all pending ration shop requests for this warehouse
        ration_pending_requests = RationStockRequest.query.filter_by(warehouse_id=warehouse.id, status='pending').order_by(RationStockRequest.created_at.desc()).all()
        
        # Calculate total allocated space
        total_allocated_space = sum(stock.quantity for stock in warehouse.stocks if stock.status == 'stored')
        
        return render_template('view_requests.html', 
                             warehouse=warehouse,
                             pending_requests=pending_requests,
                             ration_pending_requests=ration_pending_requests,
                             total_allocated_space=total_allocated_space)
    
    # Handle both form data and JSON data
    data = request.json if request.is_json else request.form
    request_id = data.get('request_id')
    approved_quantity = float(data.get('approved_quantity', 0))
    price_per_kg = float(data.get('price_per_kg', 0))  # Get the price per kg
    notes = data.get('notes', '')
    action = data.get('action')
    
    if not request_id:
        return jsonify({'success': False, 'message': 'Request ID is required'}), 400
    
    try:
        stock_request = StockRequest.query.get(request_id)
        if not stock_request or stock_request.to_id != warehouse.id:
            return jsonify({'success': False, 'message': 'Request not found'}), 404
        
        if stock_request.status in ['approved', 'rejected']:
            return jsonify({'success': False, 'message': f"Request cannot be modified. Current status: '{stock_request.status}'"}), 400
        
        if action == 'approve':
            # Check if quality rating exists for this stock
            quality_rating = StockQualityRating.query.filter_by(stock_id=stock_request.stock_id).first()
            if not quality_rating:
                return jsonify({'success': False, 'message': 'Quality rating must be set before approving the request', 'needs_rating': True, 'request_id': request_id}), 400
            
            # Validate the approved quantity
            if approved_quantity <= 0:
                return jsonify({'success': False, 'message': 'Approved quantity must be greater than zero'}), 400
            
            # Check if warehouse has enough remaining space
            total_allocated = sum([
                s.quantity for s in Stock.query.filter_by(
                    warehouse_id=warehouse.id, 
                    status='stored'
                ).all()
            ])
            
            remaining_space = warehouse.capacity - total_allocated
            
            if approved_quantity > remaining_space:
                return jsonify({
                    'success': False, 
                    'message': f'Insufficient warehouse space. Only {remaining_space:.2f} tons available.'
                }), 400
            
            # Validate price per kg
            if price_per_kg <= 0:
                return jsonify({'success': False, 'message': 'Price per kg must be greater than zero'}), 400
            
            # Get base price from CropPrice table
            base_price = CropPrice.query.filter_by(crop_type=stock_request.stock.type).first()
            if not base_price:
                return jsonify({'success': False, 'message': 'Base price not found for this stock type'}), 400
            
            if price_per_kg < base_price.price_per_kg:
                return jsonify({
                    'success': False,
                    'message': f'Price cannot be lower than the base price (₹{base_price.price_per_kg} per kg)'
                }), 400
            
            # Update the stock with approved quantity and price
            stock_request.stock.quantity = approved_quantity
            stock_request.stock.price_per_kg = price_per_kg
            stock_request.stock.status = 'stored'
            stock_request.status = 'stored'  # Changed from 'approved' to 'stored' for consistency
            stock_request.response_date = datetime.utcnow()
            stock_request.notes = notes
            
            # Create stock on blockchain if not already created
            if not stock_request.stock.blockchain_id:
                blockchain_success = create_stock_on_blockchain(stock_request.stock.id)
                if not blockchain_success:
                    return jsonify({
                        'success': False,
                        'message': 'Failed to create stock on blockchain. Please try again.'
                    }), 500
                db.session.refresh(stock_request.stock)  # Refresh to get blockchain_id
            
            # Create stock request on blockchain if not already created
            if not stock_request.blockchain_id:
                blockchain_success = create_stock_request_on_blockchain(stock_request.id)
                if not blockchain_success:
                    return jsonify({
                        'success': False,
                        'message': 'Failed to create stock request on blockchain. Please try again.'
                    }), 500
                db.session.refresh(stock_request)  # Refresh to get blockchain_id
            
            # Update stock request status on blockchain
            blockchain_success = update_stock_request_status_on_blockchain(stock_request.id, 'stored')
            if not blockchain_success:
                # Create a notification about blockchain delay
                notification = Notification(
                    user_id=stock_request.farmer.user_id,
                    title='Blockchain Update Pending',
                    message='Your stock request has been approved but the blockchain update is pending. The system will retry automatically.',
                    type='blockchain_pending'
                )
                db.session.add(notification)
            
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Request approved successfully',
                'blockchain': blockchain_success
            })
            
        elif action == 'reject':
            stock_request.status = 'rejected'
            stock_request.response_date = datetime.utcnow()
            stock_request.notes = notes
            
            # Update stock request status on blockchain if it exists
            if stock_request.blockchain_id:
                blockchain_success = update_stock_request_status_on_blockchain(stock_request.id, 'rejected')
                if not blockchain_success:
                    # Create a notification about blockchain delay
                    notification = Notification(
                        user_id=stock_request.farmer.user_id,
                        title='Blockchain Update Pending',
                        message='Your stock request has been rejected but the blockchain update is pending. The system will retry automatically.',
                        type='blockchain_pending'
                    )
                    db.session.add(notification)
            
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Request rejected successfully',
                'blockchain': blockchain_success if stock_request.blockchain_id else True
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@warehouse_dashboard.route('/rate_stock_quality', methods=['POST'])
@login_required
def rate_stock_quality():
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    
    # Get the warehouse data
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    if not warehouse:
        return jsonify({'success': False, 'message': 'Warehouse not found'}), 404
    
    # Get form data
    data = request.json if request.is_json else request.form
    request_id = data.get('request_id')
    stock_type = data.get('stock_type')  # 'perishable' or 'non_perishable'
    
    # Common parameters
    hygiene_rating = int(data.get('hygiene_rating', 0))
    damaged_goods_rating = int(data.get('damaged_goods_rating', 0))
    
    # Perishable specific parameters
    perishability_level = int(data.get('perishability_level', 0)) if stock_type == 'perishable' else None
    preservation_rating = int(data.get('preservation_rating', 0)) if stock_type == 'perishable' else None
    
    # Non-perishable specific parameters
    water_content_rating = int(data.get('water_content_rating', 0)) if stock_type == 'non_perishable' else None
    grain_grade_rating = int(data.get('grain_grade_rating', 0)) if stock_type == 'non_perishable' else None
    
    if not request_id or not stock_type:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Validate ratings
    if hygiene_rating < 1 or hygiene_rating > 10 or damaged_goods_rating < 1 or damaged_goods_rating > 10:
        return jsonify({'success': False, 'message': 'Ratings must be between 1 and 10'}), 400
    
    try:
        # Find the stock request
        stock_request = StockRequest.query.get(request_id)
        if not stock_request or stock_request.to_id != warehouse.id:
            return jsonify({'success': False, 'message': 'Request not found'}), 404
        
        # Calculate overall rating
        if stock_type == 'perishable':
            if perishability_level < 1 or perishability_level > 10 or preservation_rating < 1 or preservation_rating > 10:
                return jsonify({'success': False, 'message': 'Perishable ratings must be between 1 and 10'}), 400
            overall_rating = (hygiene_rating + damaged_goods_rating + perishability_level + preservation_rating) / 4.0
        else:  # non_perishable
            if water_content_rating < 1 or water_content_rating > 10 or grain_grade_rating < 1 or grain_grade_rating > 10:
                return jsonify({'success': False, 'message': 'Non-perishable ratings must be between 1 and 10'}), 400
            overall_rating = (hygiene_rating + damaged_goods_rating + water_content_rating + grain_grade_rating) / 4.0
        
        # Determine grade based on overall rating
        grade = 'C'
        if overall_rating >= 8:
            grade = 'A'
        elif overall_rating >= 6:
            grade = 'B'
        
        # Check if rating already exists
        existing_rating = StockQualityRating.query.filter_by(stock_id=stock_request.stock_id).first()
        if existing_rating:
            # Update existing rating
            existing_rating.stock_type = stock_type
            existing_rating.hygiene_rating = hygiene_rating
            existing_rating.damaged_goods_rating = damaged_goods_rating
            existing_rating.perishability_level = perishability_level
            existing_rating.preservation_rating = preservation_rating
            existing_rating.water_content_rating = water_content_rating
            existing_rating.grain_grade_rating = grain_grade_rating
            existing_rating.overall_rating = overall_rating
        else:
            # Create new rating
            new_rating = StockQualityRating(
                stock_id=stock_request.stock_id,
                stock_type=stock_type,
                hygiene_rating=hygiene_rating,
                damaged_goods_rating=damaged_goods_rating,
                perishability_level=perishability_level,
                preservation_rating=preservation_rating,
                water_content_rating=water_content_rating,
                grain_grade_rating=grain_grade_rating,
                overall_rating=overall_rating,
                rated_by=current_user.id
            )
            db.session.add(new_rating)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Quality rating saved successfully',
            'overall_rating': overall_rating,
            'grade': grade,
            'stock_type': stock_type
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@warehouse_dashboard.route('/accepted_requests')
@login_required
def accepted_requests():
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        flash('You need to be logged in as a warehouse manager to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the warehouse data
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    if not warehouse:
        flash('Warehouse not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get all accepted requests for this warehouse
    # Note: For StockRequests, 'stored' is the status for accepted requests
    approved_requests = StockRequest.query.filter_by(to_id=warehouse.id, status='stored').all()
    
    # Get all accepted ration shop requests for this warehouse
    # Note: For RationStockRequests, 'approved' is the status for accepted requests
    ration_approved_requests = RationStockRequest.query.filter_by(warehouse_id=warehouse.id, status='approved').all()
    
    # Calculate total allocated space
    total_allocated_space = sum(stock.quantity for stock in warehouse.stocks if stock.status == 'stored')
    
    # Update the available space in the warehouse model
    warehouse.available_space = warehouse.capacity - total_allocated_space
    
    return render_template('warehouse_accepted_requests.html', 
                          warehouse=warehouse,
                          approved_requests=approved_requests,
                          ration_approved_requests=ration_approved_requests)

@warehouse_dashboard.route('/rejected_requests')
@login_required
def rejected_requests():
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        flash('You need to be logged in as a warehouse manager to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the warehouse data
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    if not warehouse:
        flash('Warehouse not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get all rejected requests for this warehouse
    # Note: For both StockRequests and RationStockRequests, 'rejected' is the status for rejected requests
    rejected_requests = StockRequest.query.filter_by(to_id=warehouse.id, status='rejected').all()
    
    # Get all rejected ration shop requests for this warehouse
    ration_rejected_requests = RationStockRequest.query.filter_by(warehouse_id=warehouse.id, status='rejected').all()
    
    # Calculate total allocated space
    total_allocated_space = sum(stock.quantity for stock in warehouse.stocks if stock.status == 'stored')
    
    # Update the available space in the warehouse model
    warehouse.available_space = warehouse.capacity - total_allocated_space
    
    return render_template('warehouse_rejected_requests.html', 
                          warehouse=warehouse,
                          rejected_requests=rejected_requests,
                          ration_rejected_requests=ration_rejected_requests)

@warehouse_dashboard.route('/request_details/<int:request_id>')
@login_required
def request_details(request_id):
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        flash('You need to be logged in as a warehouse manager to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the warehouse data
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    if not warehouse:
        flash('Warehouse not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get the request
    stock_request = StockRequest.query.get_or_404(request_id)
    
    # Check if the request belongs to this warehouse
    if stock_request.to_id != warehouse.id:
        flash('You do not have permission to view this request.', 'error')
        return redirect(url_for('warehouse_dashboard.warehouse_home'))
    
    # Get quality rating if it exists
    quality_rating = StockQualityRating.query.filter_by(stock_id=stock_request.stock_id).first()
    
    return render_template('request_details.html', 
                          warehouse=warehouse,
                          request=stock_request,
                          quality_rating=quality_rating)

@warehouse_dashboard.route('/ration_request_details/<int:request_id>')
@login_required
def ration_request_details(request_id):
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        flash('You need to be logged in as a warehouse manager to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the warehouse data
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    if not warehouse:
        flash('Warehouse not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get the request
    ration_request = RationStockRequest.query.get_or_404(request_id)
    
    # Check if the request belongs to this warehouse
    if ration_request.warehouse_id != warehouse.id:
        flash('You do not have permission to view this request.', 'error')
        return redirect(url_for('warehouse_dashboard.warehouse_home'))
    
    return render_template('ration_request_details.html', 
                          warehouse=warehouse,
                          request=ration_request)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'farmer':
        return redirect(url_for('farmer_dashboard.farmer_home'))
    elif current_user.role == 'warehouse_manager':
        return redirect(url_for('warehouse_dashboard.warehouse_home'))
    elif current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'ration_manager':
        return redirect(url_for('main.ration_dashboard'))
    else:
        flash('Unknown user role', 'error')
        return redirect(url_for('main.index'))

# Template Context Processor
@auth.context_processor
@main.context_processor
@farmer_dashboard.context_processor
@warehouse_dashboard.context_processor
def inject_user_data():
    data = {}
    if current_user.is_authenticated:
        # Skip admin users since they don't have associated entities
        if hasattr(current_user, 'role'):  # Check if the user has a role attribute
            if current_user.role == 'warehouse_manager':
                data['user_warehouse'] = Warehouse.query.filter_by(user_id=current_user.id).first()
            elif current_user.role == 'farmer':
                data['user_farmer'] = Farmer.query.filter_by(user_id=current_user.id).first()
            elif current_user.role == 'ration_shop':
                data['shop'] = RationShop.query.filter_by(user_id=current_user.id).first()
            elif current_user.role == 'ration_manager':
                # Add ration shop data if needed
                pass
    return data

# Admin routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"Admin required check for user: {current_user}")
        if not current_user.is_authenticated:
            print("User not authenticated")
            flash('You need to be logged in as an admin to view this page.', 'error')
            return redirect(url_for('admin.login'))
        
        # Check if the current user ID has the admin prefix
        user_id = current_user.get_id()
        print(f"User ID: {user_id}")
        if not user_id.startswith('admin_'):
            print(f"User {user_id} is not an admin (no admin prefix)")
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('admin.login'))
        
        # Extract admin ID and get the admin user
        admin_id = int(user_id.split('_')[1])
        admin = Admin.query.get(admin_id)
        print(f"Admin access granted for user: {admin.email}")
        
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/login', methods=['GET', 'POST'])
def login():
    print("Admin login route accessed")
    # If admin is already logged in, redirect to admin dashboard
    if current_user.is_authenticated:
        admin = Admin.query.get(current_user.id)
        print(f"Current user: {current_user.id}, Is admin: {admin is not None}")
        if admin:
            return redirect(url_for('admin.dashboard'))
        else:
            # If a regular user is trying to access admin, log them out first
            logout_user()
            flash('Please log in with admin credentials.', 'warning')
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"Login attempt with email: {email}")
        
        if not email or not password:
            flash('Please enter both email and password', 'error')
            return redirect(url_for('admin.login'))
        
        admin_user = Admin.query.filter_by(email=email).first()
        print(f"Admin user found: {admin_user is not None}")
        
        if not admin_user:
            # Use a generic error message to prevent email enumeration
            flash('Invalid credentials', 'error')
            return redirect(url_for('admin.login'))
        
        if not check_password_hash(admin_user.password_hash, password):
            flash('Invalid credentials', 'error')
            return redirect(url_for('admin.login'))
        
        # Update last login time
        admin_user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Log in the admin
        login_user(admin_user)
        
        # Set admin login time in session for timeout tracking
        session['admin_login_time'] = datetime.utcnow().isoformat()
        
        print(f"Admin logged in successfully: {admin_user.id}")
        flash('Logged in successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/login.html')

@admin.route('/logout')
@login_required
def logout():
    # Clear all session data
    session.clear()
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('admin.login'))

@admin.route('/')
@admin_required
def dashboard():
    print(f"Admin dashboard accessed by user: {current_user.id}")
    # Get the admin object
    admin_user = Admin.query.get(current_user.id)
    
    # Count statistics for the dashboard
    farmer_count = Farmer.query.count()
    warehouse_count = Warehouse.query.count()
    stock_count = Stock.query.count()
    pending_requests = StockRequest.query.filter_by(status='pending').count()
    
    print(f"Dashboard stats: farmers={farmer_count}, warehouses={warehouse_count}, stocks={stock_count}, pending={pending_requests}")
    
    return render_template('admin/dashboard.html', 
                          admin_user=admin_user,
                          farmer_count=farmer_count,
                          warehouse_count=warehouse_count,
                          stock_count=stock_count,
                          pending_requests=pending_requests)

@admin.route('/farmers')
@admin_required
def farmers():
    farmers = Farmer.query.all()
    return render_template('admin/farmers.html', farmers=farmers)

@admin.route('/warehouses')
@admin_required
def warehouses():
    warehouses = Warehouse.query.all()
    
    # Calculate actual available space for each warehouse
    for warehouse in warehouses:
        total_allocated = db.session.query(db.func.sum(Stock.quantity))\
            .filter(Stock.warehouse_id == warehouse.id)\
            .filter(Stock.status == 'stored')\
            .scalar() or 0
        warehouse.available_space = warehouse.capacity - total_allocated
    
    return render_template('admin/warehouses.html', warehouses=warehouses)

@admin.route('/stocks')
@admin_required
def stocks():
    stocks = Stock.query.all()
    return render_template('admin/stocks.html', stocks=stocks)

@admin.route('/requests')
@admin_required
def requests():
    stock_requests = StockRequest.query.all()
    return render_template('admin/requests.html', stock_requests=stock_requests)

@admin.route('/crop-prices')
@admin_required
def crop_prices():
    crop_prices = CropPrice.query.all()
    return render_template('admin/crop_prices.html', crop_prices=crop_prices)

@admin.route('/add-crop-price', methods=['POST'])
@admin_required
def add_crop_price():
    crop_type = request.form.get('crop_type')
    other_crop_type = request.form.get('other_crop_type')
    price_per_kg = request.form.get('price_per_kg')
    
    # If "Other" is selected, use the custom crop type
    if crop_type == 'Other' and other_crop_type:
        crop_type = other_crop_type
    
    # Validate input
    if not crop_type or not price_per_kg:
        flash('Crop type and price are required', 'danger')
        return redirect(url_for('admin.crop_prices'))
    
    try:
        price_per_kg = float(price_per_kg)
        if price_per_kg <= 0:
            raise ValueError("Price must be positive")
    except ValueError:
        flash('Price must be a positive number', 'danger')
        return redirect(url_for('admin.crop_prices'))
    
    # Check if crop type already exists
    existing_price = CropPrice.query.filter_by(crop_type=crop_type).first()
    if existing_price:
        flash(f'Price for {crop_type} already exists', 'warning')
        return redirect(url_for('admin.crop_prices'))
    
    # Create new crop price
    new_price = CropPrice(
        crop_type=crop_type,
        price_per_kg=price_per_kg
    )
    
    db.session.add(new_price)
    db.session.commit()
    
    flash(f'Price for {crop_type} added successfully', 'success')
    return redirect(url_for('admin.crop_prices'))

@admin.route('/update-crop-price', methods=['POST'])
@admin_required
def update_crop_price():
    price_id = request.form.get('price_id')
    price_per_kg = request.form.get('price_per_kg')
    
    # Validate input
    if not price_id or not price_per_kg:
        flash('Price ID and new price are required', 'danger')
        return redirect(url_for('admin.crop_prices'))
    
    try:
        price_per_kg = float(price_per_kg)
        if price_per_kg <= 0:
            raise ValueError("Price must be positive")
    except ValueError:
        flash('Price must be a positive number', 'danger')
        return redirect(url_for('admin.crop_prices'))
    
    # Find the crop price
    crop_price = CropPrice.query.get(price_id)
    if not crop_price:
        flash('Crop price not found', 'danger')
        return redirect(url_for('admin.crop_prices'))
    
    # Update the price
    crop_price.price_per_kg = price_per_kg
    crop_price.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Price for {crop_price.crop_type} updated successfully', 'success')
    return redirect(url_for('admin.crop_prices'))

@admin.route('/delete-crop-price', methods=['POST'])
@admin_required
def delete_crop_price():
    price_id = request.form.get('price_id')
    
    # Validate input
    if not price_id:
        flash('Price ID is required', 'danger')
        return redirect(url_for('admin.crop_prices'))
    
    # Find the crop price
    crop_price = CropPrice.query.get(price_id)
    if not crop_price:
        flash('Crop price not found', 'danger')
        return redirect(url_for('admin.crop_prices'))
    
    crop_type = crop_price.crop_type
    
    # Delete the price
    db.session.delete(crop_price)
    db.session.commit()
    
    flash(f'Price for {crop_type} deleted successfully', 'success')
    return redirect(url_for('admin.crop_prices'))

@admin.route('/ration-shops')
@admin_required
def ration_shops():
    ration_shops = RationShop.query.all()
    return render_template('admin/ration_shops.html', ration_shops=ration_shops)

@admin.route('/approve-ration-shop', methods=['POST'])
@admin_required
def approve_ration_shop():
    data = request.json if request.is_json else request.form
    
    shop_id = data.get('shop_id')
    unique_id = data.get('unique_id')
    password = data.get('password')
    
    if not all([shop_id, unique_id, password]):
        if request.is_json:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        else:
            flash('Missing required fields', 'error')
            return redirect(url_for('admin.ration_shops'))
    
    try:
        # Get the ration shop
        shop = RationShop.query.get(shop_id)
        if not shop:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Ration shop not found'})
            else:
                flash('Ration shop not found', 'error')
                return redirect(url_for('admin.ration_shops'))
        
        # Check if shop is already approved or rejected
        if shop.status != 'pending':
            if request.is_json:
                return jsonify({'success': False, 'message': f'Ration shop is already {shop.status}'})
            else:
                flash(f'Ration shop is already {shop.status}', 'error')
                return redirect(url_for('admin.ration_shops'))
        
        # Check if unique ID is already in use
        existing_shop = RationShop.query.filter_by(unique_id=unique_id).first()
        if existing_shop and existing_shop.id != int(shop_id):
            if request.is_json:
                return jsonify({'success': False, 'message': 'Unique ID is already in use'})
            else:
                flash('Unique ID is already in use', 'error')
                return redirect(url_for('admin.ration_shops'))
        
        # Create a new user for the ration shop
        user = User(
            phone_number=unique_id,  # Using unique_id as phone_number
            password_hash=generate_password_hash(password),
            role='ration_shop'
        )
        db.session.add(user)
        db.session.flush()  # Flush to get the user ID
        
        # Import the function to generate Ethereum addresses
        from blockchain import get_eth_address
        
        # Assign Ethereum address to the user
        user.eth_address = get_eth_address(user.id, user.role)
        print(f"Assigned Ethereum address to user: {user.eth_address}")  # Debug log
        
        # Update the ration shop
        shop.status = 'approved'
        shop.unique_id = unique_id
        shop.temp_password = password  # Store the temporary password
        shop.user_id = user.id
        shop.approved_at = datetime.utcnow()
        
        # Make sure the ration shop has an Ethereum address
        if not shop.eth_address:
            shop.eth_address = get_eth_address(shop.id, 'ration_shop')
            print(f"Assigned Ethereum address to ration shop: {shop.eth_address}")  # Debug log
        
        db.session.commit()
        
        # Send an email to the shop owner with their credentials
        email_sent = False
        try:
            email_sent = send_credentials_email(shop.email, shop.name, unique_id, password)
        except Exception as e:
            # Log the error but continue with the approval process
            print(f"Error sending email: {str(e)}")
        
        if request.is_json:
            return jsonify({
                'success': True, 
                'email_sent': email_sent,
                'message': 'Ration shop approved successfully' + ('' if email_sent else ', but email could not be sent')
            })
        else:
            if email_sent:
                flash('Ration shop approved successfully and credentials email sent!', 'success')
            else:
                flash('Ration shop approved successfully, but credentials email could not be sent. Please check email settings.', 'warning')
            return redirect(url_for('admin.ration_shops'))
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'message': str(e)})
        else:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('admin.ration_shops'))

@admin.context_processor
def inject_admin_data():
    admin_data = {'current_user': current_user}
    if current_user.is_authenticated:
        admin_user = Admin.query.get(current_user.id)
        if admin_user:
            admin_data['admin_user'] = admin_user
    return admin_data

@auth.route('/ration/register', methods=['GET', 'POST'])
def ration_register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    # Create a simple form object for CSRF protection
    class SimpleForm:
        def hidden_tag(self):
            return ''
    
    form = SimpleForm()
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        location = request.form.get('location')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        aadhar_number = request.form.get('aadhar_number')
        
        # Validate form data
        if not name or not email or not location or not aadhar_number or not latitude or not longitude:
            flash('All fields are required', 'error')
            return redirect(url_for('auth.ration_register'))
            
        # Check if Aadhar is already registered
        existing_shop = RationShop.query.filter_by(aadhar_number=aadhar_number).first()
        if existing_shop:
            flash('Aadhar number already registered', 'error')
            return redirect(url_for('auth.ration_register'))
            
        # Create new ration shop registration
        shop_id = str(uuid.uuid4())[:8].upper()  # Generate a unique shop ID
        
        new_shop = RationShop(
            shop_id=shop_id,  # Add the shop_id field
            user_id=None,  # Explicitly set user_id to None
            name=name,
            email=email,
            location=location,
            latitude=float(latitude),
            longitude=float(longitude),
            aadhar_number=aadhar_number,
            status='pending'
        )
        
        try:
            db.session.add(new_shop)
            db.session.flush()  # Flush to get the shop ID
            
            # Import the function to generate Ethereum addresses
            from blockchain import get_eth_address
            
            # Assign Ethereum address to the ration shop
            new_shop.eth_address = get_eth_address(new_shop.id, 'ration_shop')
            print(f"Assigned Ethereum address to ration shop: {new_shop.eth_address}")  # Debug log
            
            db.session.commit()
            flash('Registration successful! Your application is pending approval by an administrator.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'error')
            return redirect(url_for('auth.ration_register'))
    
    return render_template('ration_register.html', form=form, maps_api_key=current_app.config['GOOGLE_MAPS_API_KEY'])

@auth.route('/ration/login', methods=['GET', 'POST'])
def ration_login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Create a simple form object for CSRF protection
    class SimpleForm:
        def hidden_tag(self):
            return ''
    
    form = SimpleForm()
    
    if request.method == 'POST':
        unique_id = request.form.get('unique_id')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # Validate form data
        if not unique_id or not password:
            flash('Please fill in all fields', 'error')
            return render_template('ration/login.html', form=form)
        
        # Find the ration shop by unique ID
        ration_shop = RationShop.query.filter_by(unique_id=unique_id, status='approved').first()
        
        if not ration_shop:
            flash('Ration shop not found or not approved yet', 'error')
            return render_template('ration/login.html', form=form)
        
        # Get the associated user
        user = User.query.get(ration_shop.user_id)
        
        if not user:
            flash('User account not found', 'error')
            return render_template('ration/login.html', form=form)
        
        # Check password
        if check_password_hash(user.password_hash, password):
            # Log in the user
            login_user(user, remember=remember)
            flash('Login successful!', 'success')
            return redirect(url_for('main.ration_dashboard'))
        else:
            flash('Invalid password', 'error')
            return render_template('ration/login.html', form=form)
    
    return render_template('ration/login.html', form=form)

@main.route('/ration/dashboard')
@login_required
def ration_dashboard():
    # Check if user is a ration shop manager
    if not current_user.is_authenticated or current_user.role != 'ration_shop':
        flash('You need to be logged in as a ration shop manager to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the ration shop data
    shop = RationShop.query.filter_by(user_id=current_user.id).first()
    if not shop:
        flash('Ration shop not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get statistics
    pending_requests = db.session.query(func.count(RationStockRequest.id)).filter(
        RationStockRequest.ration_shop_id == shop.id,
        RationStockRequest.status == 'pending'
    ).scalar()
    approved_requests = db.session.query(func.count(RationStockRequest.id)).filter(
        RationStockRequest.ration_shop_id == shop.id,
        RationStockRequest.status == 'approved'
    ).scalar()
    rejected_requests = db.session.query(func.count(RationStockRequest.id)).filter(
        RationStockRequest.ration_shop_id == shop.id,
        RationStockRequest.status == 'rejected'
    ).scalar()
    total_requests = db.session.query(func.count(RationStockRequest.id)).filter(
        RationStockRequest.ration_shop_id == shop.id
    ).scalar()
    
    # Calculate total inventory
    total_inventory = 0  # This would be calculated from actual inventory
    
    stats = {
        'customers': 0,  # This would be calculated from actual customer data
        'inventory_items': total_inventory,
        'transactions': 0,  # This would be calculated from actual transaction data
        'pending_requests': pending_requests
    }
    
    # Get notifications
    notifications = Notification.query.filter_by(user_id=current_user.id, read=False).all()
    
    # Get all warehouses for making requests
    warehouses = Warehouse.query.all()
    
    # Get all stock requests made by this ration shop
    stock_requests = RationStockRequest.query.filter_by(ration_shop_id=shop.id).order_by(RationStockRequest.request_date.desc()).all()
    
    # Get blockchain transactions for this ration shop's requests
    blockchain_transactions = []
    for request in stock_requests:
        if request.blockchain_id:
            transactions = BlockchainTransaction.query.filter_by(entity_type='ration_stock_request', entity_id=request.id).all()
            for tx in transactions:
                blockchain_transactions.append({
                    'request_id': request.id,
                    'tx_hash': tx.tx_hash,
                    'tx_type': tx.tx_type,
                    'status': tx.status,
                    'created_at': tx.created_at
                })
    
    # Sort blockchain transactions by created_at
    blockchain_transactions = sorted(blockchain_transactions, key=lambda x: x['created_at'], reverse=True)
    
    # Get recent activities
    recent_activities = []
    
    # Add recent request activities
    for request in sorted(stock_requests, key=lambda x: x.created_at if hasattr(x, 'created_at') else x.request_date, reverse=True)[:5]:
        warehouse_name = Warehouse.query.get(request.warehouse_id).name if Warehouse.query.get(request.warehouse_id) else 'Unknown'
        
        if request.status == 'pending':
            activity_type = 'request_created'
            description = f"Created a new request for {request.quantity} tons of {request.stock_type} to {warehouse_name}"
            timestamp = request.created_at if hasattr(request, 'created_at') else request.request_date
        elif request.status == 'approved':
            activity_type = 'request_approved'
            description = f"Request #{request.id} for {request.stock_type} was approved by {warehouse_name}"
            timestamp = request.updated_at if hasattr(request, 'updated_at') else request.processed_date or request.request_date
        elif request.status == 'rejected':
            activity_type = 'request_rejected'
            description = f"Request #{request.id} for {request.stock_type} was rejected by {warehouse_name}"
            timestamp = request.updated_at if hasattr(request, 'updated_at') else request.processed_date or request.request_date
        elif request.status == 'canceled':
            activity_type = 'request_canceled'
            description = f"Request #{request.id} for {request.stock_type} was canceled"
            timestamp = request.updated_at if hasattr(request, 'updated_at') else request.processed_date or request.request_date
        else:
            activity_type = 'request_updated'
            description = f"Request #{request.id} status updated to {request.status}"
            timestamp = request.updated_at if hasattr(request, 'updated_at') else request.processed_date or request.request_date
            
        recent_activities.append({
            'type': activity_type,
            'description': description,
            'timestamp': timestamp
        })
    
    # Add blockchain activities
    for tx in blockchain_transactions[:5]:
        if 'create_ration_stock_request' in tx['tx_type']:
            activity_type = 'blockchain_create'
            description = f"Request #{tx['request_id']} for stock was recorded on blockchain"
        elif 'update_ration_stock_request_status' in tx['tx_type']:
            activity_type = 'blockchain_update'
            description = f"Request #{tx['request_id']} status update was recorded on blockchain"
        else:
            activity_type = 'blockchain_transaction'
            description = f"Blockchain transaction for request #{tx['request_id']}: {tx['tx_type']}"
        
        recent_activities.append({
            'type': activity_type,
            'description': description,
            'timestamp': tx['created_at'],
            'blockchain': True,
            'tx_hash': tx['tx_hash']
        })
    
    # Sort activities by timestamp
    recent_activities = sorted(recent_activities, key=lambda x: x['timestamp'], reverse=True)
    
    # Add current date and time for the dashboard
    now = datetime.utcnow()
    
    return render_template('ration/dashboard.html',
                          shop=shop,
                          stats=stats,
                          notifications=notifications,
                          warehouses=warehouses,
                          stock_requests=stock_requests[:5],  # Limit to 5 most recent
                          blockchain_transactions=blockchain_transactions[:5],  # Limit to 5 most recent
                          recent_activities=recent_activities,
                          pending_count=pending_requests,
                          approved_count=approved_requests,
                          rejected_count=rejected_requests,
                          total_count=total_requests,
                          now=now,
                          maps_api_key=current_app.config['GOOGLE_MAPS_API_KEY'])

@main.route('/ration/request_stock')
@login_required
def ration_request_stock():
    # Check if user is a ration shop manager
    if not current_user.is_authenticated or current_user.role != 'ration_shop':
        flash('You need to be logged in as a ration shop manager to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the ration shop data
    shop = RationShop.query.filter_by(user_id=current_user.id).first()
    if not shop:
        flash('Ration shop not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get all warehouses for making requests
    warehouses = Warehouse.query.all()
    
    return render_template('ration/request_stock.html', 
                          shop=shop,
                          warehouses=warehouses)

@main.route('/ration/stock_requests')
@login_required
def ration_stock_requests():
    # Check if user is a ration shop manager
    if not current_user.is_authenticated or current_user.role != 'ration_shop':
        flash('You need to be logged in as a ration shop manager to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the ration shop data
    shop = RationShop.query.filter_by(user_id=current_user.id).first()
    if not shop:
        flash('Ration shop not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get all stock requests made by this ration shop
    stock_requests = RationStockRequest.query.filter_by(ration_shop_id=shop.id).order_by(RationStockRequest.request_date.desc()).all()
    
    return render_template('ration/stock_requests.html', 
                          shop=shop,
                          stock_requests=stock_requests)

@main.route('/ration/get_warehouse_stock/<int:warehouse_id>')
@login_required
def get_warehouse_stock(warehouse_id):
    # Check if user is a ration shop manager
    if not current_user.is_authenticated or current_user.role != 'ration_shop':
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    
    # Get the warehouse data
    warehouse = Warehouse.query.get(warehouse_id)
    if not warehouse:
        return jsonify({'success': False, 'message': 'Warehouse not found'}), 404
    
    # Get all stored stock in the warehouse
    stocks = Stock.query.filter_by(
        warehouse_id=warehouse_id,
        status='stored'
    ).all()
    
    # Format the stock data
    stock_data = []
    for stock in stocks:
        stock_data.append({
            'id': stock.id,
            'type': stock.type,
            'quantity': stock.quantity,
            'farmer_name': stock.farmer.name if stock.farmer else 'Unknown'
        })
    
    # Get warehouse capacity information
    total_allocated = sum([stock.quantity for stock in stocks])
    available_space = warehouse.capacity - total_allocated
    
    return jsonify({
        'success': True,
        'warehouse': {
            'id': warehouse.id,
            'name': warehouse.name,
            'location': warehouse.location,
            'capacity': warehouse.capacity,
            'total_allocated': total_allocated,
            'available_space': available_space
        },
        'stocks': stock_data
    })

@main.route('/ration/make_request', methods=['POST'])
@login_required
def ration_make_request():
    # Check if user is a ration shop manager
    if not current_user.is_authenticated or current_user.role != 'ration_shop':
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    
    # Get the ration shop data
    shop = RationShop.query.filter_by(user_id=current_user.id).first()
    if not shop:
        return jsonify({'success': False, 'message': 'Ration shop not found'}), 404
    
    # Get form data
    data = request.form
    warehouse_id = data.get('warehouse_id')
    stock_type = data.get('stock_type')
    quantity = data.get('quantity')
    notes = data.get('notes', '')
    
    # Validate data
    if not warehouse_id or not stock_type or not quantity:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    try:
        quantity = float(quantity)
        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Quantity must be greater than 0'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid quantity format'}), 400
    
    # Check if warehouse exists
    warehouse = Warehouse.query.get(warehouse_id)
    if not warehouse:
        return jsonify({'success': False, 'message': 'Warehouse not found'}), 404
    
    # Create stock request
    stock_request = RationStockRequest(
        ration_shop_id=shop.id,
        warehouse_id=warehouse_id,
        stock_type=stock_type,
        quantity=quantity,
        notes=notes,
        status='pending'
    )
    
    try:
        db.session.add(stock_request)
        db.session.commit()
        
        # Create notification for warehouse manager
        notification = Notification(
            user_id=warehouse.user_id,
            title='New Stock Request',
            message=f'Ration shop {shop.name} has requested {quantity} tons of {stock_type}.',
            type='ration_stock_request'
        )
        db.session.add(notification)
        db.session.commit()
        
        # Add blockchain integration
        try:
            # Import the blockchain integration functions
            from blockchain_integration import create_ration_stock_request_on_blockchain
            
            # Create ration stock request on blockchain
            blockchain_success = create_ration_stock_request_on_blockchain(stock_request.id)
            
            if blockchain_success:
                # Create notification for ration shop manager about blockchain
                blockchain_notification = Notification(
                    user_id=current_user.id,
                    title='Blockchain Integration',
                    message=f'Your request for {quantity} tons of {stock_type} has been successfully recorded on the blockchain.',
                    type='blockchain_notification'
                )
                db.session.add(blockchain_notification)
                db.session.commit()
                
                return jsonify({
                    'success': True, 
                    'message': 'Stock request submitted and recorded on blockchain successfully',
                    'blockchain': True,
                    'request_id': stock_request.id
                }), 200
            else:
                # Log the error for debugging
                logger.error(f"Failed to create ration stock request {stock_request.id} on blockchain")
                return jsonify({
                    'success': True, 
                    'message': 'Stock request submitted but failed to record on blockchain. The system will retry automatically.',
                    'blockchain': False,
                    'request_id': stock_request.id
                }), 200
        except Exception as e:
            # Log the exception for debugging
            logger.error(f"Blockchain integration failed: {str(e)}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            return jsonify({
                'success': True, 
                'message': f'Stock request submitted but blockchain integration failed: {str(e)}. The system will retry automatically.',
                'blockchain': False,
                'request_id': stock_request.id
            }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error creating request: {str(e)}'}), 500

@main.route('/ration/cancel_request/<int:request_id>', methods=['POST'])
@login_required
def ration_cancel_request(request_id):
    # Check if user is a ration shop manager
    if not current_user.is_authenticated or current_user.role != 'ration_shop':
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    
    # Get the ration shop data
    shop = RationShop.query.filter_by(user_id=current_user.id).first()
    if not shop:
        return jsonify({'success': False, 'message': 'Ration shop not found'}), 404
    
    # Find the request
    stock_request = RationStockRequest.query.filter_by(id=request_id, ration_shop_id=shop.id, status='pending').first()
    if not stock_request:
        return jsonify({'success': False, 'message': 'Request not found or cannot be canceled'}), 404
    
    # Cancel the request
    stock_request.status = 'canceled'
    
    try:
        db.session.commit()
        
        # Create notification for warehouse manager
        notification = Notification(
            user_id=stock_request.warehouse.user_id,
            title='Request Canceled',
            message=f'Ration shop {shop.name} has canceled their request for {stock_request.quantity} tons of {stock_request.stock_type}.',
            type='ration_stock_request_canceled'
        )
        db.session.add(notification)
        db.session.commit()
        
        # Add blockchain integration
        try:
            # Import the blockchain integration functions
            from blockchain_integration import update_ration_stock_request_status_on_blockchain
            
            # Update ration stock request status on blockchain
            blockchain_success = update_ration_stock_request_status_on_blockchain(
                stock_request.id, 
                'rejected',  # Use 'rejected' status for canceled requests on blockchain
                "Canceled by ration shop"
            )
            
            if blockchain_success:
                # Create blockchain notification for ration shop
                blockchain_notification = Notification(
                    user_id=current_user.id,
                    title='Blockchain Update',
                    message=f'Your request cancellation has been recorded on the blockchain.',
                    type='blockchain_notification'
                )
                db.session.add(blockchain_notification)
                db.session.commit()
                
                return jsonify({
                    'success': True, 
                    'message': 'Request canceled and recorded on blockchain successfully',
                    'blockchain': True,
                    'request_id': stock_request.id
                }), 200
            else:
                # Log the error for debugging
                logger.error(f"Failed to update ration stock request {stock_request.id} status on blockchain")
                return jsonify({
                    'success': True, 
                    'message': 'Request canceled but failed to record on blockchain. The system will retry automatically.',
                    'blockchain': False,
                    'request_id': stock_request.id
                }), 200
        except Exception as e:
            # Log the exception for debugging
            logger.error(f"Blockchain integration failed: {str(e)}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            return jsonify({
                'success': True, 
                'message': f'Request canceled but blockchain integration failed: {str(e)}. The system will retry automatically.',
                'blockchain': False,
                'request_id': stock_request.id
            }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error canceling request: {str(e)}'}), 500

@auth.route('/test-maps-api')
def test_maps_api():
    """Test route to verify Google Maps API key"""
    api_key = current_app.config['GOOGLE_MAPS_API_KEY']
    return render_template('test_maps.html', maps_api_key=api_key)

@admin.route('/get-ration-shop-credentials/<int:shop_id>')
@admin_required
def get_ration_shop_credentials(shop_id):
    try:
        # Get the ration shop
        shop = RationShop.query.get(shop_id)
        if not shop:
            return jsonify({'success': False, 'message': 'Ration shop not found'})
        
        # Check if shop is approved
        if shop.status != 'approved':
            return jsonify({'success': False, 'message': 'Ration shop is not approved'})
        
        # Return the credentials
        return jsonify({
            'success': True,
            'shop_name': shop.name,
            'unique_id': shop.unique_id,
            'password': shop.temp_password
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin.route('/reset-ration-shop-password', methods=['POST'])
@admin_required
def reset_ration_shop_password():
    data = request.json if request.is_json else request.form
    
    shop_id = data.get('shop_id')
    new_password = data.get('new_password')
    
    if not all([shop_id, new_password]):
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    try:
        # Get the ration shop
        shop = RationShop.query.get(shop_id)
        if not shop:
            return jsonify({'success': False, 'message': 'Ration shop not found'})
        
        # Check if shop is approved
        if shop.status != 'approved':
            return jsonify({'success': False, 'message': 'Ration shop is not approved'})
        
        # Get the user associated with the shop
        user = User.query.get(shop.user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        # Update the password
        user.password_hash = generate_password_hash(new_password)
        shop.temp_password = new_password  # Store the new temporary password
        
        db.session.commit()
        
        # Send an email to the shop owner with their new credentials
        email_sent = False
        try:
            email_sent = send_password_reset_email(shop.email, shop.unique_id, new_password)
        except Exception as e:
            # Log the error but continue with the password reset process
            print(f"Error sending email: {str(e)}")
        
        return jsonify({
            'success': True, 
            'email_sent': email_sent,
            'message': 'Password reset successfully' + ('' if email_sent else ', but email could not be sent')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@main.route('/ration/request_details/<int:request_id>')
@login_required
def ration_request_details(request_id):
    # Check if user is a ration shop manager
    if not current_user.is_authenticated or current_user.role != 'ration_shop':
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    
    # Get the ration shop data
    shop = RationShop.query.filter_by(user_id=current_user.id).first()
    if not shop:
        return jsonify({'success': False, 'message': 'Ration shop not found'}), 404
    
    # Find the request
    stock_request = RationStockRequest.query.filter_by(id=request_id, ration_shop_id=shop.id).first()
    if not stock_request:
        return jsonify({'success': False, 'message': 'Request not found'}), 404
    
    # Get warehouse name
    warehouse_name = Warehouse.query.get(stock_request.warehouse_id).name if Warehouse.query.get(stock_request.warehouse_id) else 'Unknown'
    
    # Format request data
    request_data = {
        'id': stock_request.id,
        'warehouse_id': stock_request.warehouse_id,
        'warehouse_name': warehouse_name,
        'stock_type': stock_request.stock_type,
        'quantity': stock_request.quantity,
        'status': stock_request.status,
        'request_date': stock_request.request_date.strftime('%Y-%m-%d %H:%M:%S'),
        'processed_date': stock_request.processed_date.strftime('%Y-%m-%d %H:%M:%S') if stock_request.processed_date else None,
        'notes': stock_request.notes,
        'admin_notes': stock_request.admin_notes,
        'blockchain_id': stock_request.blockchain_id,
        'blockchain_tx_hash': stock_request.blockchain_tx_hash
    }
    
    # Add blockchain URL if available
    if stock_request.blockchain_id:
        request_data['blockchain_url'] = url_for('blockchain.view_ration_stock_request', request_id=stock_request.id)
    
    return jsonify({
        'success': True,
        'request': request_data
    })

@warehouse_dashboard.route('/create_announcement', methods=['GET', 'POST'])
@login_required
def create_announcement():
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        flash('You need to be logged in as a warehouse manager to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the warehouse data
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    if not warehouse:
        flash('Warehouse not found.', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        stock_type = request.form.get('stock_type')
        quantity = request.form.get('quantity')
        price_per_ton = request.form.get('price_per_ton')
        description = request.form.get('description')
        expiry_date = request.form.get('expiry_date')
        
        if stock_type == 'Other':
            stock_type = request.form.get('other_stock_type')
        
        if not all([stock_type, quantity, price_per_ton, expiry_date]):
            flash('All required fields must be filled', 'error')
            return redirect(url_for('warehouse_dashboard.create_announcement'))
        
        try:
            quantity = float(quantity)
            price_per_ton = float(price_per_ton)
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d')
            
            if quantity <= 0:
                flash('Quantity must be greater than zero', 'error')
                return redirect(url_for('warehouse_dashboard.create_announcement'))
            
            if price_per_ton <= 0:
                flash('Price per ton must be greater than zero', 'error')
                return redirect(url_for('warehouse_dashboard.create_announcement'))
            
            if expiry_date < datetime.now():
                flash('Expiry date must be in the future', 'error')
                return redirect(url_for('warehouse_dashboard.create_announcement'))
            
            # Create warehouse request
            warehouse_request = WarehouseRequest(
                warehouse_id=warehouse.id,
                stock_type=stock_type,
                quantity=quantity,
                price_per_ton=price_per_ton,
                description=description,
                expiry_date=expiry_date,
                status='open'
            )
            db.session.add(warehouse_request)
            
            # Create notifications for all farmers
            farmers = Farmer.query.all()
            for farmer in farmers:
                notification = Notification(
                    user_id=farmer.user_id,
                    title='New Warehouse Announcement',
                    message=f'{warehouse.name} is requesting {quantity} tons of {stock_type}.',
                    type='warehouse_announcement'
                )
                db.session.add(notification)
            
            db.session.commit()
            
            # Add blockchain integration if needed
            try:
                # Import the blockchain integration functions
                from blockchain_integration import create_warehouse_request_on_blockchain
                
                # Create warehouse request on blockchain
                blockchain_success = create_warehouse_request_on_blockchain(warehouse_request.id)
                
                if not blockchain_success:
                    logger.warning(f"Warehouse request created but blockchain update failed")
            except Exception as e:
                logger.error(f"Blockchain integration error: {str(e)}")
            
            flash('Announcement created successfully', 'success')
            return redirect(url_for('warehouse_dashboard.view_announcements'))
            
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
            return redirect(url_for('warehouse_dashboard.create_announcement'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating announcement: {str(e)}', 'error')
            return redirect(url_for('warehouse_dashboard.create_announcement'))
    
    # Handle GET request
    return render_template('create_announcement.html', warehouse=warehouse)

@warehouse_dashboard.route('/view_announcements')
@login_required
def view_announcements():
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        flash('You need to be logged in as a warehouse manager to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the warehouse data
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    if not warehouse:
        flash('Warehouse not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get all announcements for this warehouse
    announcements = WarehouseRequest.query.filter_by(warehouse_id=warehouse.id).order_by(WarehouseRequest.date_posted.desc()).all()
    
    # Calculate total allocated space
    total_allocated_space = sum(stock.quantity for stock in warehouse.stocks if stock.status == 'stored')
    
    # Update the available space in the warehouse model
    warehouse.available_space = warehouse.capacity - total_allocated_space
    
    return render_template('warehouse_announcements.html', 
                          warehouse=warehouse,
                          announcements=announcements)

@warehouse_dashboard.route('/edit_announcement/<int:announcement_id>', methods=['GET', 'POST'])
@login_required
def edit_announcement(announcement_id):
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        flash('You need to be logged in as a warehouse manager to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the warehouse data
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    if not warehouse:
        flash('Warehouse not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get the announcement
    announcement = WarehouseRequest.query.get_or_404(announcement_id)
    
    # Check if the announcement belongs to this warehouse
    if announcement.warehouse_id != warehouse.id:
        flash('You do not have permission to edit this announcement.', 'error')
        return redirect(url_for('warehouse_dashboard.view_announcements'))
    
    if request.method == 'POST':
        stock_type = request.form.get('stock_type')
        quantity = request.form.get('quantity')
        price_per_ton = request.form.get('price_per_ton')
        description = request.form.get('description')
        expiry_date = request.form.get('expiry_date')
        status = request.form.get('status')
        
        if stock_type == 'Other':
            stock_type = request.form.get('other_stock_type')
        
        if not all([stock_type, quantity, price_per_ton, expiry_date, status]):
            flash('All required fields must be filled', 'error')
            return redirect(url_for('warehouse_dashboard.edit_announcement', announcement_id=announcement_id))
        
        try:
            quantity = float(quantity)
            price_per_ton = float(price_per_ton)
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d')
            
            if quantity <= 0:
                flash('Quantity must be greater than zero', 'error')
                return redirect(url_for('warehouse_dashboard.edit_announcement', announcement_id=announcement_id))
            
            if price_per_ton <= 0:
                flash('Price per ton must be greater than zero', 'error')
                return redirect(url_for('warehouse_dashboard.edit_announcement', announcement_id=announcement_id))
            
            # Update announcement
            announcement.stock_type = stock_type
            announcement.quantity = quantity
            announcement.price_per_ton = price_per_ton
            announcement.description = description
            announcement.expiry_date = expiry_date
            announcement.status = status
            
            db.session.commit()
            
            # Add blockchain integration if needed
            try:
                # Import the blockchain integration functions
                from blockchain_integration import update_warehouse_request_on_blockchain
                
                # Update warehouse request on blockchain
                blockchain_success = update_warehouse_request_on_blockchain(announcement.id)
                
                if not blockchain_success:
                    logger.warning(f"Warehouse request updated but blockchain update failed")
            except Exception as e:
                logger.error(f"Blockchain integration error: {str(e)}")
            
            flash('Announcement updated successfully', 'success')
            return redirect(url_for('warehouse_dashboard.view_announcements'))
            
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
            return redirect(url_for('warehouse_dashboard.edit_announcement', announcement_id=announcement_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating announcement: {str(e)}', 'error')
            return redirect(url_for('warehouse_dashboard.edit_announcement', announcement_id=announcement_id))
    
    # Handle GET request
    return render_template('edit_announcement.html', warehouse=warehouse, announcement=announcement)

@warehouse_dashboard.route('/delete_announcement/<int:announcement_id>', methods=['POST'])
@login_required
def delete_announcement(announcement_id):
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        flash('Unauthorized access', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the warehouse data
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    if not warehouse:
        flash('Warehouse not found', 'error')
        return redirect(url_for('main.index'))
    
    # Get the announcement
    announcement = WarehouseRequest.query.get_or_404(announcement_id)
    
    # Check if the announcement belongs to this warehouse
    if announcement.warehouse_id != warehouse.id:
        flash('You do not have permission to delete this announcement', 'error')
        return redirect(url_for('warehouse_dashboard.view_announcements'))
    
    try:
        db.session.delete(announcement)
        db.session.commit()
        
        flash('Announcement deleted successfully', 'success')
        return redirect(url_for('warehouse_dashboard.view_announcements'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting announcement: {str(e)}', 'error')
        return redirect(url_for('warehouse_dashboard.view_announcements'))

# Farmer routes to view warehouse announcements
@farmer_dashboard.route('/warehouse_announcements')
@login_required
def view_warehouse_announcements():
    # Check if user is a farmer
    if not current_user.is_authenticated or current_user.role != 'farmer':
        flash('You need to be logged in as a farmer to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the farmer data
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    if not farmer:
        flash('Farmer not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get all active warehouse announcements
    current_date = datetime.now()
    announcements = WarehouseRequest.query.filter(
        WarehouseRequest.status == 'open',
        WarehouseRequest.expiry_date > current_date
    ).order_by(WarehouseRequest.date_posted.desc()).all()
    
    return render_template('farmer_warehouse_announcements.html', 
                          farmer=farmer,
                          announcements=announcements)

@farmer_dashboard.route('/respond_to_announcement/<int:announcement_id>')
@login_required
def respond_to_announcement(announcement_id):
    # Check if user is a farmer
    if not current_user.is_authenticated or current_user.role != 'farmer':
        flash('You need to be logged in as a farmer to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the farmer data
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    if not farmer:
        flash('Farmer not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get the announcement
    announcement = WarehouseRequest.query.get_or_404(announcement_id)
    
    # Check if the announcement is still open
    if announcement.status != 'open' or announcement.expiry_date < datetime.now():
        flash('This announcement is no longer active.', 'error')
        return redirect(url_for('farmer_dashboard.view_warehouse_announcements'))
    
    # Redirect to create request page with pre-filled data
    return redirect(url_for('farmer_dashboard.create_request_page', 
                           warehouse_id=announcement.warehouse_id,
                           warehouse_request_id=announcement.id,
                           stock_type=announcement.stock_type,
                           quantity=announcement.quantity))

@auth.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.role == 'farmer':
        return redirect(url_for('auth.edit_farmer_profile'))
    elif current_user.role == 'warehouse_manager':
        return redirect(url_for('auth.edit_warehouse_profile'))
    elif current_user.role == 'ration_shop':
        return redirect(url_for('auth.edit_ration_profile'))
    else:
        flash('Profile editing not available for this role', 'error')
        return redirect(url_for('main.dashboard'))

@auth.route('/profile/edit/farmer', methods=['GET', 'POST'])
@login_required
def edit_farmer_profile():
    # Check if user is a farmer
    if not current_user.is_authenticated or current_user.role != 'farmer':
        flash('You need to be logged in as a farmer to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the farmer data
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    if not farmer:
        flash('Farmer profile not found.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        
        # Validate form data
        if not name or not address:
            flash('Name and address are required', 'error')
            return redirect(url_for('auth.edit_farmer_profile'))
        
        try:
            # Update farmer profile
            farmer.name = name
            farmer.address = address
            
            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('farmer_dashboard.farmer_home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
            return redirect(url_for('auth.edit_farmer_profile'))
    
    return render_template('edit_farmer_profile.html', farmer=farmer)

@auth.route('/profile/edit/warehouse', methods=['GET', 'POST'])
@login_required
def edit_warehouse_profile():
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        flash('You need to be logged in as a warehouse manager to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the warehouse data
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    if not warehouse:
        flash('Warehouse profile not found.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        manager_name = request.form.get('manager_name')
        warehouse_name = request.form.get('warehouse_name')
        location = request.form.get('location')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        warehouse_type = request.form.get('warehouse_type')
        capacity = request.form.get('capacity')
        
        # Validate form data
        if not all([manager_name, warehouse_name, location, latitude, longitude, warehouse_type, capacity]):
            flash('All fields are required', 'error')
            return redirect(url_for('auth.edit_warehouse_profile'))
        
        try:
            # Update warehouse profile
            warehouse.manager_name = manager_name
            warehouse.name = warehouse_name
            warehouse.location = location
            warehouse.latitude = float(latitude)
            warehouse.longitude = float(longitude)
            warehouse.warehouse_type = warehouse_type
            
            # Only update capacity if it's greater than or equal to the used space
            new_capacity = float(capacity)
            used_space = warehouse.capacity - warehouse.available_space
            if new_capacity < used_space:
                flash('New capacity cannot be less than the currently used space', 'error')
                return redirect(url_for('auth.edit_warehouse_profile'))
            
            warehouse.available_space = warehouse.available_space + (new_capacity - warehouse.capacity)
            warehouse.capacity = new_capacity
            
            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('warehouse_dashboard.warehouse_home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
            return redirect(url_for('auth.edit_warehouse_profile'))
    
    return render_template('edit_warehouse_profile.html', warehouse=warehouse, maps_api_key=current_app.config['GOOGLE_MAPS_API_KEY'])

@auth.route('/profile/edit/ration', methods=['GET', 'POST'])
@login_required
def edit_ration_profile():
    # Check if user is a ration shop manager
    if not current_user.is_authenticated or current_user.role != 'ration_shop':
        flash('You need to be logged in as a ration shop manager to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the ration shop data
    shop = RationShop.query.filter_by(user_id=current_user.id).first()
    if not shop:
        flash('Ration shop profile not found.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        location = request.form.get('location')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        # Validate form data
        if not all([name, email, location, latitude, longitude]):
            flash('All fields are required', 'error')
            return redirect(url_for('auth.edit_ration_profile'))
        
        try:
            # Update ration shop profile
            shop.name = name
            shop.email = email
            shop.location = location
            shop.latitude = float(latitude)
            shop.longitude = float(longitude)
            
            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('main.ration_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
            return redirect(url_for('auth.edit_ration_profile'))
    
    return render_template('edit_ration_profile.html', shop=shop, maps_api_key=current_app.config['GOOGLE_MAPS_API_KEY'])

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate form data
        if not all([current_password, new_password, confirm_password]):
            flash('All fields are required', 'error')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('auth.change_password'))
        
        if len(new_password) < 8:
            flash('New password must be at least 8 characters long', 'error')
            return redirect(url_for('auth.change_password'))
        
        # Check current password
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('auth.change_password'))
        
        try:
            # Update password
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Password changed successfully', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error changing password: {str(e)}', 'error')
            return redirect(url_for('auth.change_password'))
    
    return render_template('change_password.html')

@warehouse_dashboard.route('/get_base_price/<stock_type>')
@login_required
def get_base_price(stock_type):
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    
    # Get the base price from CropPrice table
    crop_price = CropPrice.query.filter_by(crop_type=stock_type).first()
    
    if not crop_price:
        return jsonify({'success': False, 'message': 'Base price not found for this stock type'}), 404
    
    return jsonify({
        'success': True,
        'base_price': crop_price.price_per_kg
    })
