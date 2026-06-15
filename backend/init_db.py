import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from app.models import db, User, RepairCategory, RepairRequest
from flask import Flask
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///remont24.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    
    print("✅ Таблицы созданы")
    
    # Проверяем, есть ли пользователи
    if User.query.count() == 0:
        # Создаём админа
        admin = User(
            email='admin@remont24.ru',
            full_name='Администратор',
            phone='+79998887766',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("✅ Админ создан: admin@remont24.ru / admin123")
        
        # Создаём мастеров
        master1 = User(
            email='master1@remont24.ru',
            full_name='Алексей Мастеров',
            phone='+79001112233',
            role='master'
        )
        master1.set_password('master123')
        db.session.add(master1)
        print("✅ Мастер 1: master1@remont24.ru / master123")
        
        master2 = User(
            email='master2@remont24.ru',
            full_name='Дмитрий Техник',
            phone='+79004445566',
            role='master'
        )
        master2.set_password('master456')
        db.session.add(master2)
        print("✅ Мастер 2: master2@remont24.ru / master456")
        
        # Создаём клиентов
        client1 = User(
            email='client@remont24.ru',
            full_name='Иван Петров',
            phone='+79001234567',
            role='client'
        )
        client1.set_password('client123')
        db.session.add(client1)
        print("✅ Клиент: client@remont24.ru / client123")
        
        client2 = User(
            email='client2@remont24.ru',
            full_name='Мария Сидорова',
            phone='+79007654321',
            role='client'
        )
        client2.set_password('client456')
        db.session.add(client2)
        print("✅ Клиент 2: client2@remont24.ru / client456")
        
        # Создаём категории
        categories = [
            RepairCategory(name='Диагностика', price=500),
            RepairCategory(name='Замена клавиатуры', price=1500),
            RepairCategory(name='Чистка от пыли', price=1000),
            RepairCategory(name='Установка Windows', price=800),
            RepairCategory(name='Замена матрицы', price=3000),
            RepairCategory(name='Ремонт материнской платы', price=2500),
            RepairCategory(name='Замена аккумулятора', price=1200),
            RepairCategory(name='Установка SSD', price=2000),
        ]
        for cat in categories:
            db.session.add(cat)
        
        db.session.commit()
        print("✅ Добавлены категории ремонта")
        
        print("\n" + "=" * 50)
        print("📋 Тестовые учётные данные:")
        print("=" * 50)
        print("  👑 Админ:    admin@remont24.ru / admin123")
        print("  🔧 Мастер 1: master1@remont24.ru / master123")
        print("  🔧 Мастер 2: master2@remont24.ru / master456")
        print("  👤 Клиент:   client@remont24.ru / client123")
        print("=" * 50)
    else:
        print("⚠️ Пользователи уже существуют")
    
    print(f"\n📊 Статистика:")
    print(f"   Пользователей: {User.query.count()}")
    print(f"   Категорий: {RepairCategory.query.count()}")
    print(f"   Заявок: {RepairRequest.query.count()}")