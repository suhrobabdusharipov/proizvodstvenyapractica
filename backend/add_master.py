from backend.main import app, db
from models import User

with app.app_context():
    masters = [
        {
            'email': 'master1@remont24.ru',
            'full_name': 'Алексей Мастеров',
            'phone': '+79001112233',
            'password': 'master123'
        },
        {
            'email': 'master2@remont24.ru',
            'full_name': 'Дмитрий Техник',
            'phone': '+79004445566',
            'password': 'master456'
        }
    ]
    
    for m in masters:
        existing = User.query.filter_by(email=m['email']).first()
        
        if existing:
            print(f"❌ Мастер {m['email']} уже существует")
        else:
            master = User(
                email=m['email'],
                full_name=m['full_name'],
                phone=m['phone'],
                role='master',
                is_active=True
            )
            master.set_password(m['password'])
            db.session.add(master)
            print(f"✅ Добавлен мастер: {m['email']} / {m['password']}")
    
    db.session.commit()
    
    print("\n=== СПИСОК МАСТЕРОВ ===")
    masters_list = User.query.filter_by(role='master').all()
    for m in masters_list:
        print(f"ID: {m.id}, Email: {m.email}, Имя: {m.full_name}")