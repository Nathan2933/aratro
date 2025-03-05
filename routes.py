from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, session
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Farmer, Warehouse, Stock, StockRequest, WarehouseRequest, Notification, Admin, RationShop, RationStockRequest
import re
from datetime import datetime
from functools import wraps
from email_utils import send_credentials_email, send_rejection_email, send_password_reset_email
import uuid
import os

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
        name = request.form.get('name')
        address = request.form.get('address')
        aadhar_number = request.form.get('aadharNumber')
        phone_number = request.form.get('phoneNumber')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')

        # Validate required fields
        if not all([name, address, aadhar_number, phone_number, password, confirm_password]):
            flash('All fields are required', 'error')
            return redirect(url_for('auth.farmer_register'))

        # Validate password match
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.farmer_register'))

        # Validate password length
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return redirect(url_for('auth.farmer_register'))

        # Validate Aadhar number format
        if not aadhar_number.isdigit() or len(aadhar_number) != 12:
            flash('Invalid Aadhar number. Must be 12 digits', 'error')
            return redirect(url_for('auth.farmer_register'))

        # Validate phone number format
        if not phone_number.isdigit() or len(phone_number) != 10:
            flash('Invalid phone number. Must be 10 digits', 'error')
            return redirect(url_for('auth.farmer_register'))

        # Check if user already exists
        user = User.query.filter_by(phone_number=phone_number).first()
        if user:
            flash('Phone number already registered', 'error')
            return redirect(url_for('auth.farmer_register'))

        # Check if Aadhar is already registered
        farmer = Farmer.query.filter_by(aadhar_number=aadhar_number).first()
        if farmer:
            flash('Aadhar number already registered', 'error')
            return redirect(url_for('auth.farmer_register'))

        try:
            # Create new user
            user = User(
                phone_number=phone_number,
                password_hash=generate_password_hash(password),
                role='farmer'
            )
            db.session.add(user)
            db.session.flush()  # Get user.id before committing

            # Create farmer profile
            farmer = Farmer(
                user_id=user.id,
                name=name,
                address=address,
                aadhar_number=aadhar_number,
                phone_number=phone_number
            )
            db.session.add(farmer)
            
            db.session.commit()
            login_user(user)
            flash('Registration successful!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error occurred during registration', 'error')
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
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))

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
    if current_user.role != 'farmer':
        flash('Access denied: You must be a farmer to view this page', 'error')
        return redirect(url_for('auth.login'))

    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    if not farmer:
        flash('Farmer profile not found', 'error')
        return redirect(url_for('auth.login'))

    # Get farmer's requests
    try:
        requests = StockRequest.query.filter_by(from_id=farmer.id).all()
    except Exception as e:
        requests = []
        flash('Error loading requests', 'error')

    # Get nearby warehouses and calculate their actual available space
    try:
        warehouses = Warehouse.query.all()  # For now, showing all warehouses
        for warehouse in warehouses:
            total_allocated = db.session.query(db.func.sum(Stock.quantity))\
                .filter(Stock.warehouse_id == warehouse.id)\
                .filter(Stock.status == 'stored')\
                .scalar() or 0
            warehouse.available_space = warehouse.capacity - total_allocated
    except Exception as e:
        warehouses = []
        flash('Error loading warehouses', 'error')

    return render_template('farmer_dashboard.html', farmer=farmer, requests=requests, warehouses=warehouses)

@farmer_dashboard.route('/create_request', methods=['GET', 'POST'])
@login_required
def create_request_page():
    if current_user.role != 'farmer':
        flash('Access denied. Farmers only.', 'error')
        return redirect(url_for('main.dashboard'))
    
    farmer = current_user.farmer
    if not farmer:
        flash('Farmer profile not found.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        if request.is_json:
            # Handle AJAX request for rejected request resubmission
            data = request.get_json()
            stock_type = data.get('stock_type')
            quantity = data.get('quantity')
            warehouse_id = data.get('warehouse_id')
            
            if not all([stock_type, quantity, warehouse_id]):
                return jsonify({'success': False, 'message': 'Missing required fields'})
            
            warehouse = Warehouse.query.get(warehouse_id)
            if not warehouse:
                return jsonify({'success': False, 'message': 'Warehouse not found'})
            
            # Check warehouse capacity
            total_allocated = sum([s.quantity for s in Stock.query.filter_by(
                warehouse_id=warehouse_id, 
                status='stored'
            ).all()])
            
            if quantity > (warehouse.capacity - total_allocated):
                return jsonify({
                    'success': False,
                    'message': f'Insufficient space. Only {warehouse.capacity - total_allocated:.2f} tons available.'
                })
            
            try:
                # Create new stock entry
                stock = Stock(
                    type=stock_type,
                    quantity=0,  # Will be set when approved
                    requested_quantity=quantity,
                    status='pending',
                    farmer_id=farmer.id,
                    warehouse_id=warehouse_id
                )
                db.session.add(stock)
                db.session.flush()  # Get the stock ID
                
                # Create stock request
                stock_request = StockRequest(
                    from_id=farmer.id,
                    to_id=warehouse_id,
                    stock_id=stock.id,
                    status='pending'
                )
                db.session.add(stock_request)
                
                # Create notification for warehouse manager
                notification = Notification(
                    user_id=warehouse.user.id,
                    title='New Stock Request',
                    message=f'New request for {quantity} tons of {stock_type} from {farmer.name}',
                    type='new_request'
                )
                db.session.add(notification)
                
                db.session.commit()
                return jsonify({'success': True})
                
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': str(e)})
    
    # Handle GET request
    warehouses = Warehouse.query.all()
    # Calculate actual available space for each warehouse
    for warehouse in warehouses:
        total_allocated = db.session.query(db.func.sum(Stock.quantity))\
            .filter(Stock.warehouse_id == warehouse.id)\
            .filter(Stock.status == 'stored')\
            .scalar() or 0
        warehouse.available_space = warehouse.capacity - total_allocated
    
    return render_template('create_request.html', warehouses=warehouses)

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
        
        flash('Stock request submitted successfully', 'success')
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
    
    # Try to get request using new schema
    try:
        stock_request = StockRequest.query.filter_by(id=request_id, farmer_id=farmer.id, status='pending').first()
        if stock_request:
            stock_request.status = 'canceled'
            db.session.commit()
            return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        # If new schema fails, try old schema
        try:
            stock_request = StockRequest.query.filter_by(id=request_id, to_id=farmer.id, status='pending').first()
            if stock_request:
                stock_request.status = 'canceled'
                db.session.commit()
                return jsonify({'success': True})
        except Exception as inner_e:
            db.session.rollback()
    
    return jsonify({'success': False, 'message': 'Request not found or cannot be canceled'})

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
        flash('Access denied. Farmers only.', 'error')
        return redirect(url_for('main.dashboard'))
    
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    if not farmer:
        flash('Farmer profile not found.', 'error')
        return redirect(url_for('main.dashboard'))
    
    requests = StockRequest.query.filter_by(
        from_id=farmer.id,
        status='approved'
    ).join(Stock).filter(
        Stock.quantity < Stock.requested_quantity
    ).order_by(StockRequest.updated_at.desc()).all()
    
    warehouses = Warehouse.query.all()
    
    return render_template('partial_acceptances.html', requests=requests, warehouses=warehouses)

# Warehouse Dashboard Routes
@warehouse_dashboard.route('/')
@login_required
def warehouse_home():
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        flash('You need to be logged in as a warehouse manager to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the warehouse data
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    if not warehouse:
        flash('Warehouse not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get all stock requests for this warehouse
    pending_requests = StockRequest.query.filter_by(to_id=warehouse.id, status='pending').all()
    approved_requests = StockRequest.query.filter_by(to_id=warehouse.id, status='approved').all()
    
    # Get all ration shop stock requests for this warehouse
    ration_pending_requests = RationStockRequest.query.filter_by(warehouse_id=warehouse.id, status='pending').all()
    ration_approved_requests = RationStockRequest.query.filter_by(warehouse_id=warehouse.id, status='approved').all()
    
    # Calculate total allocated space
    total_allocated_space = sum(stock.quantity for stock in warehouse.stocks if stock.status == 'stored')
    
    # Get notifications
    notifications = Notification.query.filter_by(user_id=current_user.id, read=False).all()
    
    return render_template('warehouse_dashboard.html',
                         warehouse=warehouse,
                         pending_requests=pending_requests,
                          approved_requests=approved_requests,
                          ration_pending_requests=ration_pending_requests,
                          ration_approved_requests=ration_approved_requests,
                          total_allocated_space=total_allocated_space,
                          notifications=notifications)

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
            user_id=RationShop.query.get(stock_request.ration_shop_id).user_id,
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
            user_id=RationShop.query.get(stock_request.ration_shop_id).user_id,
            title='Stock Request Rejected',
            message=f'Your request for {stock_request.quantity} tons of {stock_request.stock_type} has been rejected by {warehouse.name}.',
            type='ration_stock_request_rejected'
        )
        db.session.add(notification)
    else:
        return jsonify({'success': False, 'message': 'Invalid action'}), 400
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': f'Request {action}d successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error processing request: {str(e)}'}), 500

@warehouse_dashboard.route('/respond_to_request', methods=['POST'])
@login_required
def respond_to_request():
    # Check if user is a warehouse manager
    if not current_user.is_authenticated or current_user.role != 'warehouse_manager':
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    
    # Get the warehouse data
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    if not warehouse:
        return jsonify({'success': False, 'message': 'Warehouse not found'}), 404
    
    # Handle both form data and JSON data
    data = request.json if request.is_json else request.form
    request_id = data.get('request_id')
    approved_quantity = float(data.get('approved_quantity', 0))
    notes = data.get('notes', '')
    action = data.get('action')
    
    if not request_id:
        return jsonify({'success': False, 'message': 'Request ID is required'}), 400
    
    try:
        stock_request = StockRequest.query.get(request_id)
        if not stock_request or stock_request.to_id != warehouse.id:
            return jsonify({'success': False, 'message': 'Request not found'}), 404
        
        if stock_request.status != 'pending':
            return jsonify({'success': False, 'message': 'Request cannot be modified'}), 400
        
        if action == 'approve':
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
            
            # Update the stock with approved quantity
            stock_request.stock.quantity = approved_quantity
            
            # Update request status and stock status
            stock_request.status = 'approved'
            stock_request.stock.status = 'stored'
            
            # Create notification for the farmer
            notification = Notification(
                user_id=stock_request.stock.farmer.user_id,
                title='Stock Request Approved',
                message=f'Your stock request has been approved for {approved_quantity} tons of {stock_request.stock.type}.',
                type='approved'
            )
            db.session.add(notification)
            
        elif action == 'reject':
            # Update request status and stock status
            stock_request.status = 'rejected'
            stock_request.stock.status = 'rejected'
            
            # Create notification for the farmer
            notification = Notification(
                user_id=stock_request.stock.farmer.user_id,
                title='Stock Request Rejected',
                message=f'Your stock request for {stock_request.stock.requested_quantity} tons of {stock_request.stock.type} has been rejected.',
                type='rejected'
            )
            db.session.add(notification)
        else:
            return jsonify({'success': False, 'message': 'Invalid action'}), 400
        
        # Update notes
        stock_request.admin_notes = notes
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'Request {action}d successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

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
    return render_template('admin/requests.html', requests=stock_requests)

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
        
        # Update the ration shop
        shop.status = 'approved'
        shop.unique_id = unique_id
        shop.temp_password = password  # Store the temporary password
        shop.user_id = user.id
        shop.approved_at = datetime.utcnow()
        
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
    pending_requests = RationStockRequest.query.filter_by(ration_shop_id=shop.id, status='pending').count()
    approved_requests = RationStockRequest.query.filter_by(ration_shop_id=shop.id, status='approved').count()
    rejected_requests = RationStockRequest.query.filter_by(ration_shop_id=shop.id, status='rejected').count()
    total_requests = RationStockRequest.query.filter_by(ration_shop_id=shop.id).count()
    
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
    
    # Get warehouse stock data for the first warehouse (default selection)
    default_warehouse = warehouses[0] if warehouses else None
    warehouse_stock = []
    
    if default_warehouse:
        warehouse_stock = Stock.query.filter_by(
            warehouse_id=default_warehouse.id,
            status='stored'
        ).all()
    
    return render_template('ration/dashboard.html', 
                          shop=shop, 
                          stats=stats, 
                          notifications=notifications,
                          warehouses=warehouses,
                          stock_requests=stock_requests,
                          pending_count=pending_requests,
                          approved_count=approved_requests,
                          rejected_count=rejected_requests,
                          total_count=total_requests,
                          default_warehouse=default_warehouse,
                          warehouse_stock=warehouse_stock)

@main.route('/ration/available_stock')
@login_required
def ration_available_stock():
    # Check if user is a ration shop manager
    if not current_user.is_authenticated or current_user.role != 'ration_shop':
        flash('You need to be logged in as a ration shop manager to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the ration shop data
    shop = RationShop.query.filter_by(user_id=current_user.id).first()
    if not shop:
        flash('Ration shop not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get all warehouses for viewing stock
    warehouses = Warehouse.query.all()
    
    # Get default warehouse (first one or None if no warehouses)
    default_warehouse = warehouses[0] if warehouses else None
    warehouse_stock = []
    
    if default_warehouse:
        warehouse_stock = Stock.query.filter_by(
            warehouse_id=default_warehouse.id,
            status='stored'
        ).all()
    
    return render_template('ration/available_stock.html', 
                          shop=shop,
                          warehouses=warehouses,
                          default_warehouse=default_warehouse,
                          warehouse_stock=warehouse_stock)

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
        
        return jsonify({'success': True, 'message': 'Stock request submitted successfully'}), 200
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
        
        return jsonify({'success': True, 'message': 'Request canceled successfully'}), 200
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
