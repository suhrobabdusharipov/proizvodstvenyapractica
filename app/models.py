from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
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
