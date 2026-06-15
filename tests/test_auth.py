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
            
            test_user = User(
                email='test@test.ru',
                full_name='Тест Тестович',
                phone='+79001234567',
                role='client'
            )
            test_user.set_password('test12345')
            db.session.add(test_user)
            db.session.commit()
            
            yield client
            
            db.drop_all()


def test_register_page_loads(client):
    response = client.get('/')
    assert response.status_code == 200


def test_register_success(client):
    data = {
        'full_name': 'Новый Пользователь',
        'email': 'new@test.ru',
        'phone': '+79998887766',
        'password': 'password123',
        'confirm': 'password123'
    }
    response = client.post('/register', data=data)
    assert response.status_code == 200
    
    user = User.query.filter_by(email='new@test.ru').first()
    assert user is not None
    assert user.full_name == 'Новый Пользователь'


def test_register_short_password(client):
    data = {
        'full_name': 'Новый Пользователь',
        'email': 'new2@test.ru',
        'phone': '+79998887766',
        'password': '123',
        'confirm': '123'
    }
    response = client.post('/register', data=data)
    assert response.status_code == 200
    assert 'Пароль должен содержать минимум 8 символов' in response.get_data(as_text=True)


def test_register_password_mismatch(client):
    data = {
        'full_name': 'Новый Пользователь',
        'email': 'new3@test.ru',
        'phone': '+79998887766',
        'password': 'password123',
        'confirm': 'password456'
    }
    response = client.post('/register', data=data)
    assert response.status_code == 200
    assert 'Пароли не совпадают' in response.get_data(as_text=True)


def test_register_duplicate_email(client):
    data = {
        'full_name': 'Дубликат',
        'email': 'test@test.ru',
        'phone': '+79998887766',
        'password': 'password123',
        'confirm': 'password123'
    }
    response = client.post('/register', data=data)
    assert response.status_code == 200
    assert 'Пользователь с таким email уже существует' in response.get_data(as_text=True)


def test_login_success(client):
    data = {'email': 'test@test.ru', 'password': 'test12345'}
    response = client.post('/login', data=data, follow_redirects=True)
    assert response.status_code == 200


def test_login_wrong_password(client):
    data = {'email': 'test@test.ru', 'password': 'wrongpassword'}
    response = client.post('/login', data=data)
    assert response.status_code == 200
    assert 'Неверный email или пароль' in response.get_data(as_text=True)


def test_login_nonexistent_user(client):
    data = {'email': 'nonexistent@test.ru', 'password': 'password123'}
    response = client.post('/login', data=data)
    assert response.status_code == 200
    assert 'Неверный email или пароль' in response.get_data(as_text=True)


def test_logout(client):
    client.post('/login', data={'email': 'test@test.ru', 'password': 'test12345'})
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200