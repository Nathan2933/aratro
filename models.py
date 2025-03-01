from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(10), unique=True, nullable=False)  # Exactly 10 digits
    password_hash = db.Column(db.String(256), nullable=False)  # Increased length for secure hash
    role = db.Column(db.String(20), nullable=False)  # 'farmer', 'warehouse_manager', or 'ration_manager'
    farmer = db.relationship('Farmer', backref='user', lazy=True, uselist=False)
    warehouse = db.relationship('Warehouse', backref='user', lazy=True, uselist=False)

class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    aadhar_number = db.Column(db.String(12), unique=True, nullable=False)  # Exactly 12 digits
    phone_number = db.Column(db.String(10), nullable=False)  # Exactly 10 digits
    stocks = db.relationship('Stock', backref='farmer', lazy=True)

class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # type of crop/product
    quantity = db.Column(db.Float, nullable=False)  # in tons
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer.id'))
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20))  # 'available', 'in_transit', 'stored'

class StockRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    stock_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # in tons
    notes = db.Column(db.Text)
    admin_notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    date_requested = db.Column(db.DateTime, default=datetime.utcnow)
    date_processed = db.Column(db.DateTime)
    
    # For compatibility with old schema
    from_id = db.Column(db.Integer)
    to_id = db.Column(db.Integer)
    request_date = db.Column(db.DateTime)
    crop_type = db.Column(db.String(50))
    
    # Relationships
    farmer = db.relationship('Farmer', backref='stock_requests')
    warehouse = db.relationship('Warehouse', backref='stock_requests')

class WarehouseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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
