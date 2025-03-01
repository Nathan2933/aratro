from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, session
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Farmer, Warehouse, Stock, StockRequest, WarehouseRequest
import re

auth = Blueprint('auth', __name__)
main = Blueprint('main', __name__)
farmer_dashboard = Blueprint('farmer_dashboard', __name__, url_prefix='/farmer')
warehouse_dashboard = Blueprint('warehouse_dashboard', __name__, url_prefix='/warehouse')

@auth.before_request
def before_request():
    if current_user.is_authenticated:
        # Refresh the user session on each request
        session.modified = True

@auth.route('/register')
def register():
    # If user is logged in, log them out before showing registration options
    if current_user.is_authenticated:
        logout_user()
        session.clear()
    return render_template('register.html')

@auth.route('/farmer/register', methods=['GET', 'POST'])
def farmer_register():
    # If user is logged in, log them out before registration
    if current_user.is_authenticated:
        logout_user()
        session.clear()

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
    # If user is logged in, log them out before registration
    if current_user.is_authenticated:
        logout_user()
        session.clear()

    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

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
            'warehouse': 'warehouse_manager'
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
            
            # Redirect to dashboard
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
        return redirect(url_for('main.dashboard'))
    
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    
    # Try to get requests using new schema
    try:
        requests = StockRequest.query.filter_by(farmer_id=farmer.id).all()
    except Exception as e:
        # If new schema fails, fall back to old schema
        try:
            requests = StockRequest.query.filter_by(to_id=farmer.id).all()
        except:
            # If both fail, just use an empty list
            requests = []
    
    warehouses = Warehouse.query.all()
    
    return render_template('farmer_dashboard_new.html', farmer=farmer, requests=requests, warehouses=warehouses)

@farmer_dashboard.route('/create_request')
@login_required
def create_request_page():
    if current_user.role != 'farmer':
        flash('Access denied: You must be a farmer to access this page', 'error')
        return redirect(url_for('main.dashboard'))
    
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    warehouses = Warehouse.query.all()
    
    # Check if we're responding to a warehouse request
    warehouse_request_id = request.args.get('warehouse_request_id')
    warehouse_request = None
    
    if warehouse_request_id:
        try:
            warehouse_request = WarehouseRequest.query.get(int(warehouse_request_id))
        except:
            pass
    
    # Check if a specific warehouse was selected
    warehouse_id = request.args.get('warehouse_id')
    selected_warehouse = None
    
    if warehouse_id:
        try:
            selected_warehouse = Warehouse.query.get(int(warehouse_id))
        except:
            pass
    
    # Get Google Maps API key from config
    maps_api_key = current_app.config.get('GOOGLE_MAPS_API_KEY', '')
    
    return render_template('create_request.html', 
                          farmer=farmer, 
                          warehouses=warehouses, 
                          maps_api_key=maps_api_key, 
                          warehouse_request=warehouse_request,
                          selected_warehouse=selected_warehouse)

@farmer_dashboard.route('/view_requests')
@login_required
def view_requests_page():
    if current_user.role != 'farmer':
        flash('Access denied: You must be a farmer to view this page', 'error')
        return redirect(url_for('main.dashboard'))
    
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    
    # Get farmer's stock requests
    try:
        # Try new schema
        requests = StockRequest.query.filter_by(farmer_id=farmer.id).order_by(StockRequest.date_requested.desc()).all()
    except Exception as e:
        # If new schema fails, try old schema
        try:
            requests = StockRequest.query.filter_by(to_id=farmer.id).order_by(StockRequest.request_date.desc()).all()
        except Exception as inner_e:
            requests = []
    
    # Get open warehouse requests
    try:
        warehouse_requests = WarehouseRequest.query.filter_by(status='open').order_by(WarehouseRequest.date_posted.desc()).all()
    except Exception as e:
        # WarehouseRequest model might not exist yet
        warehouse_requests = []
    
    return render_template('view_requests.html', requests=requests, warehouse_requests=warehouse_requests)

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
    notes = request.form.get('notes', '')
    
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
        
        if quantity > warehouse.available_space:
            flash(f'Requested quantity exceeds available space in the warehouse ({warehouse.available_space} tons)', 'error')
            return redirect(url_for('farmer_dashboard.create_request_page'))
        
        farmer = Farmer.query.filter_by(user_id=current_user.id).first()
        
        # Try to create a request using the new schema
        try:
            new_request = StockRequest(
                farmer_id=farmer.id,
                warehouse_id=warehouse.id,
                stock_type=stock_type,
                quantity=quantity,
                notes=notes,
                status='pending'
            )
            db.session.add(new_request)
            db.session.commit()
        except Exception as e:
            # If new schema fails, try old schema
            db.session.rollback()
            try:
                new_request = StockRequest(
                    from_id=farmer.id,
                    to_id=warehouse.id,
                    stock_type=stock_type,
                    quantity=quantity,
                    status='pending'
                )
                db.session.add(new_request)
                db.session.commit()
            except Exception as inner_e:
                db.session.rollback()
                flash(f'Error submitting request: {str(inner_e)}', 'error')
                return redirect(url_for('farmer_dashboard.create_request_page'))
        
        flash('Stock request submitted successfully', 'success')
        return redirect(url_for('farmer_dashboard.view_requests_page'))
        
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

# Warehouse Dashboard Routes
@warehouse_dashboard.route('/dashboard')
@login_required
def warehouse_home():
    if current_user.role != 'warehouse_manager':
        flash('Access denied. You must be a warehouse manager to view this page.', 'error')
        return redirect(url_for('main.index'))
    
    warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
    stocks = Stock.query.filter_by(warehouse_id=warehouse.id).all()
    return render_template('warehouse_dashboard.html', stocks=stocks, warehouse=warehouse)

@warehouse_dashboard.route('/update_stock', methods=['POST'])
@login_required
def update_stock():
    if current_user.role != 'warehouse_manager':
        return jsonify({'error': 'Unauthorized access'}), 403
    
    crop_type = request.form.get('crop_type')
    quantity = request.form.get('quantity')
    action = request.form.get('action')
    
    if not all([crop_type, quantity, action]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        warehouse = Warehouse.query.filter_by(user_id=current_user.id).first()
        stock = Stock.query.filter_by(warehouse_id=warehouse.id, crop_type=crop_type).first()
        
        if action == 'add':
            if not stock:
                stock = Stock(warehouse_id=warehouse.id, crop_type=crop_type, quantity=0)
                db.session.add(stock)
            stock.quantity += float(quantity)
        elif action == 'remove':
            if not stock or stock.quantity < float(quantity):
                return jsonify({'error': 'Insufficient stock'}), 400
            stock.quantity -= float(quantity)
        
        db.session.commit()
        return jsonify({'message': 'Stock updated successfully', 'new_quantity': stock.quantity})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Main Routes
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
        if current_user.role == 'warehouse_manager':
            data['user_warehouse'] = Warehouse.query.filter_by(user_id=current_user.id).first()
        elif current_user.role == 'farmer':
            data['user_farmer'] = Farmer.query.filter_by(user_id=current_user.id).first()
    return data
