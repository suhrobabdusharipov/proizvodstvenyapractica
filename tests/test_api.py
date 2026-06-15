import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
from backend.main import app, db
from backend.app.models import User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            user = User(
                email='apiuser@test.ru',
                full_name='API Пользователь',
                role='client'
            )
            user.set_password('api12345')
            db.session.add(user)
            db.session.commit()
            
            yield client
            
            db.drop_all()


def test_api_register(client):
    data = {
        'email': 'apinew@test.ru',
        'password': 'password123',
        'full_name': 'API Новый'
    }
    response = client.post('/api/auth/register', json=data)
    assert response.status_code == 201
    assert 'Регистрация успешна' in response.get_data(as_text=True)


def test_api_login(client):
    data = {'email': 'apiuser@test.ru', 'password': 'api12345'}
    response = client.post('/api/auth/login', json=data)
    assert response.status_code == 200
    assert 'access_token' in response.get_json()


def test_api_login_wrong(client):
    data = {'email': 'apiuser@test.ru', 'password': 'wrongpassword'}
    response = client.post('/api/auth/login', json=data)
    assert response.status_code == 401
    assert 'Неверный email или пароль' in response.get_data(as_text=True)


def test_api_categories(client):
    response = client.get('/api/categories')
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['service'] == 'Ремонт24'