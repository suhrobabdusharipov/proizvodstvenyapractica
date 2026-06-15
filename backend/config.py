import os

class Config:
    DB_HOST = 'localhost'
    DB_PORT = '5432'
    DB_NAME = 'remont24_db'
    DB_USER = 'postgres'
    DB_PASSWORD = 'postgres123'
    
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SECRET_KEY = 'remont24-secret-key-2025'
    JWT_SECRET_KEY = 'remont24-jwt-secret-key-2025'
    
    JWT_ACCESS_TOKEN_EXPIRES = 86400

    DEBUG = True
    
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5000']