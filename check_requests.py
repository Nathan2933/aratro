from flask import Flask
from models import db, RationStockRequest
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aratro.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    print('Requests by status:')
    for status in ['pending', 'approved', 'rejected']:
        count = db.session.query(func.count(RationStockRequest.id)).filter(RationStockRequest.status == status).scalar()
        print(f'{status}: {count}')
