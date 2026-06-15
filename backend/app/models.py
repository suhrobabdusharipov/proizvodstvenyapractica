from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class UserRole:
    CLIENT = 'client'
    MASTER = 'master'
    ADMIN = 'admin'

class RequestStatus:
    NEW = 'new'
    ACCEPTED = 'accepted'
    DIAGNOSTICS = 'diagnostics'
    REPAIR = 'repair'
    READY = 'ready'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default=UserRole.CLIENT, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role
        }

class RepairCategory(db.Model):
    __tablename__ = 'repair_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': float(self.price)
        }

class RepairRequest(db.Model):
    __tablename__ = 'repair_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    master_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('repair_categories.id'), nullable=False)
    
    device_type = db.Column(db.String(20), nullable=False)
    device_model = db.Column(db.String(100), nullable=True)
    issue_description = db.Column(db.Text, nullable=False)
    
    status = db.Column(db.String(20), default=RequestStatus.NEW, nullable=False)
    total_price = db.Column(db.Numeric(10, 2), default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    client = db.relationship('User', foreign_keys=[client_id], backref='user_requests')
    assigned_master = db.relationship('User', foreign_keys=[master_id], backref='master_requests')
    category = db.relationship('RepairCategory', backref='category_requests')

class RequestComment(db.Model):
    __tablename__ = 'request_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('repair_requests.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    request = db.relationship('RepairRequest', backref='comments')
    author = db.relationship('User', backref='user_comments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'user_id': self.user_id,
            'comment_text': self.comment_text,
            'is_internal': self.is_internal,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }