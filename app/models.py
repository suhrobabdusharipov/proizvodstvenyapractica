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
    
class RepairRequest(db.Model):
    __tablename__ = 'repair_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    master_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('repair_categories.id'), nullable=False)
    
    device_type = db.Column(db.String(20), nullable=False)
    device_model = db.Column(db.String(100), nullable=True)
    issue_description = db.Column(db.Text, nullable=False)
    
    status = db.Column(db.String(20), default=RequestStatus.NEW, nullable=False, index=True)
    total_price = db.Column(db.Numeric(10, 2), default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    comments = db.relationship(
        'RequestComment',
        backref='request',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    used_parts = db.relationship(
        'RequestSparePart',
        backref='request',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def can_edit(self, user):
        if not user:
            return False
        if user.role == UserRole.ADMIN:
            return True
        if user.role == UserRole.MASTER:
            return True
        if user.id == self.client_id and self.status == RequestStatus.NEW:
            return True
        return False
    
    def can_change_status(self, user):
        if not user:
            return False
        return user.role in [UserRole.ADMIN, UserRole.MASTER]
    
    def to_dict(self, include_comments=False, include_parts=False):
        data = {
            'id': self.id,
            'client': self.client.to_dict() if self.client else None,
            'master': self.assigned_master.to_dict() if self.assigned_master else None,
            'category': self.category.to_dict() if self.category else None,
            'device_type': self.device_type,
            'device_model': self.device_model,
            'issue_description': self.issue_description,
            'status': self.status,
            'total_price': float(self.total_price) if self.total_price else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
        
        if include_comments:
            data['comments'] = [c.to_dict() for c in self.comments.order_by(RequestComment.created_at.asc())]
        
        if include_parts:
            data['used_parts'] = [p.to_dict() for p in self.used_parts]
        
        return data
    
    def __repr__(self):
        return f'<RepairRequest {self.id}: {self.status}>'
    
class RequestComment(db.Model):
    __tablename__ = 'request_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('repair_requests.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    comment_text = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False) 
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def can_view(self, user):
        if not user:
            return not self.is_internal
        if user.role in [UserRole.ADMIN, UserRole.MASTER]:
            return True
        return not self.is_internal
    
    def to_dict(self, user=None):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'user_name': self.author.full_name if self.author else None,
            'user_role': self.author.role if self.author else None,
            'comment_text': self.comment_text,
            'is_internal': self.is_internal,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<RequestComment {self.id} for request {self.request_id}>'

class SparePart(db.Model):
    __tablename__ = 'spare_parts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    quantity = db.Column(db.Integer, default=0)
    reserved_quantity = db.Column(db.Integer, default=0)  
    price = db.Column(db.Numeric(10, 2), nullable=False)
    compatible_models = db.Column(db.Text, nullable=True)  
    is_active = db.Column(db.Boolean, default=True)
    
    used_in_requests = db.relationship('RequestSparePart', backref='spare_part', lazy='dynamic')
    
    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'quantity': self.quantity,
            'reserved_quantity': self.reserved_quantity,
            'available_quantity': self.available_quantity,
            'price': float(self.price) if self.price else 0,
            'compatible_models': self.compatible_models,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<SparePart {self.name}>'

class RequestSparePart(db.Model):
    __tablename__ = 'request_spare_parts'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('repair_requests.id'), nullable=False)
    part_id = db.Column(db.Integer, db.ForeignKey('spare_parts.id'), nullable=False)
    quantity_used = db.Column(db.Integer, default=1)
    price_at_moment = db.Column(db.Numeric(10, 2), nullable=True)  
    
    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'part_id': self.part_id,
            'part_name': self.spare_part.name if self.spare_part else None,
            'quantity_used': self.quantity_used,
            'price_at_moment': float(self.price_at_moment) if self.price_at_moment else None
        }
    
    def __repr__(self):
        return f'<RequestSparePart request={self.request_id} part={self.part_id}>'