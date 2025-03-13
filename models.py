from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone_number = db.Column(db.String(10), unique=True, nullable=False)  # Exactly 10 digits
    password_hash = db.Column(db.String(256), nullable=False)  # Increased length for secure hash
    role = db.Column(db.String(20), nullable=False)  # 'farmer', 'warehouse_manager', or 'ration_manager'
    eth_address = db.Column(db.String(42), unique=True, nullable=True)  # Ethereum address for blockchain
    farmer = db.relationship('Farmer', backref='user', lazy=True, uselist=False)
    warehouse = db.relationship('Warehouse', backref='user', lazy=True, uselist=False)

class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    aadhar_number = db.Column(db.String(12), unique=True, nullable=False)  # Exactly 12 digits
    phone_number = db.Column(db.String(10), nullable=False)  # Exactly 10 digits
    eth_address = db.Column(db.String(42), unique=True, nullable=True)  # Ethereum address for blockchain
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
    eth_address = db.Column(db.String(42), unique=True, nullable=True)  # Ethereum address for blockchain
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
    blockchain_id = db.Column(db.Integer, nullable=True)  # ID on the blockchain
    blockchain_tx_hash = db.Column(db.String(66), nullable=True)  # Transaction hash on the blockchain
    
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
    blockchain_id = db.Column(db.Integer, nullable=True)  # ID on the blockchain
    blockchain_tx_hash = db.Column(db.String(66), nullable=True)  # Transaction hash on the blockchain
    
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
    blockchain_id = db.Column(db.Integer, nullable=True)  # ID on the blockchain
    blockchain_tx_hash = db.Column(db.String(66), nullable=True)  # Transaction hash on the blockchain
    
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
    eth_address = db.Column(db.String(42), unique=True, nullable=True)  # Ethereum address for blockchain
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
    eth_address = db.Column(db.String(42), unique=True, nullable=True)  # Ethereum address for blockchain
    
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
    blockchain_id = db.Column(db.Integer, nullable=True)  # ID on the blockchain
    blockchain_tx_hash = db.Column(db.String(66), nullable=True)  # Transaction hash on the blockchain
    
    # Relationships
    ration_shop = db.relationship('RationShop', backref='stock_requests')
    warehouse = db.relationship('Warehouse', backref='ration_requests')
    
    def __repr__(self):
        return f'<RationStockRequest {self.id}: from {self.ration_shop_id} to {self.warehouse_id}>'

class OTP(db.Model):
    """Model for storing OTP codes for password reset"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone_number = db.Column(db.String(10), nullable=False)  # Phone number to which OTP is sent
    otp_code = db.Column(db.String(6), nullable=False)  # 6-digit OTP code
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)  # OTP expiration time
    is_used = db.Column(db.Boolean, default=False)  # Whether the OTP has been used
    
    def __repr__(self):
        return f'<OTP {self.id}: {self.phone_number}>'

# New model for blockchain transactions
class BlockchainTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tx_hash = db.Column(db.String(66), unique=True, nullable=False)  # Transaction hash
    tx_type = db.Column(db.String(50), nullable=False)  # Type of transaction (e.g., 'create_stock', 'update_status')
    entity_type = db.Column(db.String(50), nullable=False)  # Type of entity (e.g., 'stock', 'stock_request')
    entity_id = db.Column(db.Integer, nullable=False)  # ID of the entity in the database
    blockchain_id = db.Column(db.Integer, nullable=True)  # ID on the blockchain
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, failed
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime, nullable=True)  # When the transaction was confirmed
    data = db.Column(db.Text, nullable=True)  # Additional data in JSON format
    
    def __repr__(self):
        return f'<BlockchainTransaction {self.id}: {self.tx_type} for {self.entity_type} {self.entity_id}>'

class CropPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    crop_type = db.Column(db.String(100), unique=True, nullable=False)  # Type of crop (e.g., 'Rice', 'Wheat')
    price_per_kg = db.Column(db.Float, nullable=False)  # Price per kg in currency
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CropPrice {self.crop_type}: {self.price_per_kg} per kg>'

class StockQualityRating(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    stock_type = db.Column(db.String(50), nullable=False)  # 'perishable' or 'non_perishable'
    
    # Common parameters
    hygiene_rating = db.Column(db.Integer, nullable=False)  # Scale of 1-10
    damaged_goods_rating = db.Column(db.Integer, nullable=False)  # Scale of 1-10
    
    # Perishable specific parameters
    perishability_level = db.Column(db.Integer, nullable=True)  # Scale of 1-10
    preservation_rating = db.Column(db.Integer, nullable=True)  # Scale of 1-10
    
    # Non-perishable specific parameters
    water_content_rating = db.Column(db.Integer, nullable=True)  # Scale of 1-10
    grain_grade_rating = db.Column(db.Integer, nullable=True)  # Scale of 1-10
    
    overall_rating = db.Column(db.Float, nullable=False)  # Average of all applicable ratings
    rated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Warehouse manager who rated
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    stock = db.relationship('Stock', backref='quality_rating', uselist=False)
    rater = db.relationship('User', backref='ratings_given')
    
    def __repr__(self):
        return f'<StockQualityRating {self.id}: {self.overall_rating}/10 for Stock {self.stock_id}>'
