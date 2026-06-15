import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from backend.main import app, db
from models import User, RepairCategory, RepairRequest

@pytest.fixture
def app_context():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def test_create_user(app_context):
    user = User(
        email='model@test.ru',
        full_name='Модельный Пользователь',
        phone='+79001234567',
        role='client'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    saved_user = User.query.filter_by(email='model@test.ru').first()
    assert saved_user is not None
    assert saved_user.full_name == 'Модельный Пользователь'
    assert saved_user.check_password('password123') == True


def test_user_to_dict(app_context):
    user = User(
        email='dict@test.ru',
        full_name='Словарный Пользователь',
        phone='+79001234567',
        role='client'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    user_dict = user.to_dict()
    assert user_dict['email'] == 'dict@test.ru'
    assert user_dict['full_name'] == 'Словарный Пользователь'
    assert 'password_hash' not in user_dict


def test_create_category(app_context):
    category = RepairCategory(
        name='Диагностика',
        description='Полная диагностика',
        price=500,
        estimated_days=1
    )
    db.session.add(category)
    db.session.commit()
    
    saved = RepairCategory.query.filter_by(name='Диагностика').first()
    assert saved is not None
    assert saved.price == 500


def test_create_request(app_context):
    user = User(email='request@test.ru', full_name='Тестовый Клиент', role='client')
    user.set_password('password123')
    db.session.add(user)
    
    category = RepairCategory(name='Ремонт', price=1000)
    db.session.add(category)
    db.session.commit()
    
    request = RepairRequest(
        client_id=user.id,
        category_id=category.id,
        device_type='notebook',
        device_model='Lenovo T480',
        issue_description='Не включается',
        status='new',
        total_price=1000
    )
    db.session.add(request)
    db.session.commit()
    
    saved = RepairRequest.query.first()
    assert saved is not None
    assert saved.device_model == 'Lenovo T480'
    assert saved.client_id == user.id


def test_user_has_role_method(app_context):
    admin = User(email='admin@test.ru', full_name='Админ', role='admin')
    master = User(email='master@test.ru', full_name='Мастер', role='master')
    client = User(email='client@test.ru', full_name='Клиент', role='client')
    
    db.session.add_all([admin, master, client])
    db.session.commit()
    
    assert admin.has_role('admin') == True
    assert master.has_role('master') == True
    assert client.has_role('client') == True
    assert client.has_role('admin') == False