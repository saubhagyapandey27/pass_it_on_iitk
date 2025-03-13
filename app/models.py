from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    batch = db.Column(db.String(32), nullable=False)
    department = db.Column(db.String(64), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    iitk_address = db.Column(db.String(20), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    items = db.relationship('Item', backref='seller', lazy='dynamic')
    sent_requests = db.relationship('BuyRequest', 
                                  foreign_keys='BuyRequest.buyer_id',
                                  backref='buyer', lazy='dynamic')
    received_requests = db.relationship('BuyRequest',
                                      foreign_keys='BuyRequest.seller_id',
                                      backref='seller', lazy='dynamic')
    wishlisted_items = db.relationship('Wishlist', backref='user', lazy='dynamic')

    # app/models.py - Update password hashing
    def set_password(self, password):
        # Use stronger hashing algorithm with more iterations
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256:150000')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Other')
    condition = db.Column(db.String(20), nullable=False)
    defect_description = db.Column(db.Text)
    specifications = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_donation = db.Column(db.Boolean, default=False)
    is_bargainable = db.Column(db.Boolean, default=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    is_available = db.Column(db.Boolean, default=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    images = db.relationship('ItemImage', backref='item', lazy=True)
    requests = db.relationship('BuyRequest', backref='item', lazy='dynamic')
    wishlisted_by = db.relationship('Wishlist', backref='item', lazy='dynamic')

class ItemImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(512), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)

class BuyRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined
    date_requested = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add a unique constraint to prevent duplicate wishlist entries
    __table_args__ = (db.UniqueConstraint('user_id', 'item_id', name='_user_item_wishlist_uc'),) 