from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

db = SQLAlchemy()

class UserRole(str, Enum):
    CLIENT = 'client'      
    MASTER = 'master'      
    ADMIN = 'admin'        

class RequestStatus(str, Enum):
    """Статусы заявок"""
    NEW = 'new'                    
    ACCEPTED = 'accepted'          
    DIAGNOSTICS = 'diagnostics'   
    REPAIR = 'repair'              
    READY = 'ready'                
    COMPLETED = 'completed'        
    CANCELLED = 'cancelled'        

class DeviceType(str, Enum):
    """Типы устройств"""
    PC = 'pc'                      
    NOTEBOOK = 'notebook'          
    MONOBLOCK = 'monoblock'        

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default=UserRole.CLIENT, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    requests_as_client = db.relationship(
        'RepairRequest', 
        foreign_keys='RepairRequest.client_id',
        backref='client', 
        lazy='dynamic'
    )
    requests_as_master = db.relationship(
        'RepairRequest',
        foreign_keys='RepairRequest.master_id',
        backref='assigned_master',
        lazy='dynamic'
    )
    comments = db.relationship('RequestComment', backref='author', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role):
        return self.role == role or self.role == UserRole.ADMIN
    
    def to_dict(self, include_email=True):
        data = {
            'id': self.id,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_email:
            data['email'] = self.email
        return data
    
    def __repr__(self):
        return f'<User {self.email}>'

class RepairCategory(db.Model):
    __tablename__ = 'repair_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    estimated_days = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    
    requests = db.relationship('RepairRequest', backref='category', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else 0,
            'estimated_days': self.estimated_days,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<RepairCategory {self.name}>'