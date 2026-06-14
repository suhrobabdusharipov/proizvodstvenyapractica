from main import app, db
from models import User

with app.app_context():
    admin = User.query.filter_by(email='admin@remont24.ru').first()
    
    if admin:
        print(f"Админ уже существует: {admin.email}")
    else:
        admin = User(
            email='admin@remont24.ru',
            full_name='Администратор',
            phone='+79998887766',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Админ создан: admin@remont24.ru / admin123")
    
    users = User.query.all()
    print("\n=== ВСЕ ПОЛЬЗОВАТЕЛИ ===")
    for u in users:
        print(f"ID: {u.id}, Email: {u.email}, Роль: {u.role}")