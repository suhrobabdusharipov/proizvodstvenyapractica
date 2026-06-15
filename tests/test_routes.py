import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from backend.main import app, db
from models import User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        
            client_user = User(email='client@test.ru', full_name='Клиент', role='client')
            client_user.set_password('client123')
            
            master_user = User(email='master@test.ru', full_name='Мастер', role='master')
            master_user.set_password('master123')
            
            admin_user = User(email='admin@test.ru', full_name='Админ', role='admin')
            admin_user.set_password('admin123')
            
            db.session.add_all([client_user, master_user, admin_user])
            db.session.commit()
            
            yield client
            
            db.drop_all()


def test_user_page_requires_login(client):
    response = client.get('/user', follow_redirects=True)
    assert response.status_code == 200


def test_master_page_requires_master_role(client):
    client.post('/login', data={'email': 'client@test.ru', 'password': 'client123'})
    response = client.get('/master')
    assert response.status_code == 403


def test_admin_page_requires_admin_role(client):
    client.post('/login', data={'email': 'client@test.ru', 'password': 'client123'})
    response = client.get('/admin')
    assert response.status_code == 403


def test_master_page_access_for_master(client):
    client.post('/login', data={'email': 'master@test.ru', 'password': 'master123'})
    response = client.get('/master')
    assert response.status_code == 200


def test_admin_page_access_for_admin(client):
    client.post('/login', data={'email': 'admin@test.ru', 'password': 'admin123'})
    response = client.get('/admin')
    assert response.status_code == 200