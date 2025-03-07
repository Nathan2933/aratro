from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone_number = db.Column(db.String(10), unique=True, nullable=False)  # Exactly 10 digits
    password_hash = db.Column(db.String(256), nullable=False)  # Increased length for secure hash
    role = db.Column(db.String(20), nullable=False)  # 'farmer', 'warehouse_manager', or 'ration_manager'
    farmer = db.relationship('Farmer', backref='user', lazy=True, uselist=False)
    warehouse = db.relationship('Warehouse', backref='user', lazy=True, uselist=False)

class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    aadhar_number = db.Column(db.String(12), unique=True, nullable=False)  # Exactly 12 digits
    phone_number = db.Column(db.String(10), nullable=False)  # Exactly 10 digits
    stocks = db.relationship('Stock', backref='farmer', lazy=True)

class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manager_name = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    phone_number = db.Column(db.String(20))
    warehouse_type = db.Column(db.String(20))  # 'private' or 'government'
    capacity = db.Column(db.Float)  # in tons
    available_space = db.Column(db.Float)  # in tons
    stocks = db.relationship('Stock', backref='warehouse', lazy=True)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    requested_quantity = db.Column(db.Float, nullable=False)  # Original requested quantity
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, stored, rejected
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Stock {self.type} - {self.quantity} tons>'

class StockRequest(db.Model):
    __tablename__ = 'stock_request'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    from_id = db.Column(db.Integer, db.ForeignKey('farmer.id'), nullable=False)  # Farmer's ID
    to_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)    # Warehouse's ID
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add relationships
    farmer = db.relationship('Farmer', foreign_keys=[from_id], backref='stock_requests')
    warehouse = db.relationship('Warehouse', foreign_keys=[to_id], backref='received_requests')
    stock = db.relationship('Stock', backref='request')
    
    def __repr__(self):
        return f'<StockRequest {self.id}: from {self.from_id} to {self.to_id}>'

class WarehouseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    stock_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price_per_ton = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, nullable=False)
    
    # Relationships
    warehouse = db.relationship('Warehouse', backref='warehouse_requests')
    
    def __repr__(self):
        return f'<WarehouseRequest {self.id}: {self.warehouse.name} requesting {self.quantity} tons of {self.stock_type}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))  # e.g., 'stock_return', 'request_update', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    
    # Relationship with User
    user = db.relationship('User', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    role = 'admin'  # Add a static role attribute
    
    def get_id(self):
        return f"admin_{self.id}"
    
    def __repr__(self):
        return f'<Admin {self.email}>'

class RationShop(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shop_id = db.Column(db.String(50), unique=True, nullable=True)  # Added to match database schema
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Will be set after approval
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=True)  # Latitude for map location
    longitude = db.Column(db.Float, nullable=True)  # Longitude for map location
    aadhar_number = db.Column(db.String(12), unique=True, nullable=False)  # Exactly 12 digits
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    unique_id = db.Column(db.String(20), unique=True, nullable=True)  # Will be set by admin after approval
    temp_password = db.Column(db.String(100), nullable=True)  # Temporary password set by admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Relationship with User
    user = db.relationship('User', backref='ration_shop', lazy=True, uselist=False)
    
    def __repr__(self):
        return f'<RationShop {self.name}>'

class RationStockRequest(db.Model):
    __tablename__ = 'ration_stock_request'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ration_shop_id = db.Column(db.Integer, db.ForeignKey('ration_shop.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    stock_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed_date = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ration_shop = db.relationship('RationShop', backref='stock_requests')
    warehouse = db.relationship('Warehouse', backref='ration_requests')
    
    def __repr__(self):
        return f'<RationStockRequest {self.id}: from {self.ration_shop_id} to {self.warehouse_id}>'
