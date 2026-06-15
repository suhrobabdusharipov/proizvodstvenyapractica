from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from functools import wraps
from datetime import timedelta

from backend.config import Config
from models import db, User, RepairCategory, RepairRequest, RequestComment, RequestStatus, UserRole

app = Flask(__name__,
    template_folder='templates',
    static_folder='static'
)
app.config.from_object(Config)

CORS(app)
jwt = JWTManager(app)
db.init_app(app)

def create_database_if_not_exists():
    db_name = app.config['DB_NAME']
    db_user = app.config['DB_USER']
    db_password = app.config['DB_PASSWORD']
    db_host = app.config['DB_HOST']
    db_port = app.config['DB_PORT']
    
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database='postgres',
            user=db_user,
            password=db_password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"База данных '{db_name}' успешно создана!")
        else:
            print(f"База данных '{db_name}' уже существует")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Ошибка при проверке/создании БД: {e}")

def get_status_text(status):
    statuses = {
        'new': 'Новая',
        'accepted': 'Принята',
        'diagnostics': 'Диагностика',
        'repair': 'Ремонт',
        'ready': 'Готова к выдаче',
        'completed': 'Выдана',
        'cancelled': 'Отменена'
    }
    return statuses.get(status, status)

def get_device_type_text(device_type):
    types = {
        'pc': 'Компьютер',
        'notebook': 'Ноутбук',
        'monoblock': 'Моноблок'
    }
    return types.get(device_type, device_type)

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index_page') + '#auth-section')
        return f(*args, **kwargs)
    return decorated_function

def master_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index_page') + '#auth-section')
        
        user = User.query.get(session['user_id'])
        if not user or user.role not in ['master', 'admin']:
            return "Доступ запрещён. Требуются права мастера или администратора", 403
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index_page') + '#auth-section')
        
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return "Доступ запрещён. Требуются права администратора", 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index_page():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login_action():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    
    if not email:
        return render_template('index.html', error='Введите email', active_tab='login')
    
    if not password:
        return render_template('index.html', error='Введите пароль', active_tab='login')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['user_name'] = user.full_name
        session['user_role'] = user.role
        
        if user.role == 'admin':
            return redirect(url_for('admin_page'))
        elif user.role == 'master':
            return redirect(url_for('master_page'))
        else:
            return redirect(url_for('user_page'))
    else:
        return render_template('index.html', error='Неверный email или пароль', active_tab='login')


@app.route('/register', methods=['POST'])
def register_action():
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm', '')
    
    if not full_name:
        return render_template('index.html', register_error='Введите ФИО', active_tab='register')
    
    if not email:
        return render_template('index.html', register_error='Введите email', active_tab='register')
    
    if not password:
        return render_template('index.html', register_error='Введите пароль', active_tab='register')
    
    if len(password) < 8:
        return render_template('index.html', register_error='Пароль должен содержать минимум 8 символов', active_tab='register')
    
    if password != confirm:
        return render_template('index.html', register_error='Пароли не совпадают', active_tab='register')
    
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return render_template('index.html', register_error='Пользователь с таким email уже существует', active_tab='register')
    
    user = User(
        email=email,
        full_name=full_name,
        phone=phone,
        role='client'
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return render_template('index.html', register_success='Регистрация прошла успешно! Теперь войдите в систему', active_tab='login')

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()
    return redirect(url_for('index_page'))


@app.route('/user')
@login_required
def user_page():
    """Личный кабинет пользователя (клиент)"""
    user = get_current_user()
    
    requests = RepairRequest.query.filter_by(client_id=user.id).order_by(RepairRequest.created_at.desc()).all()
    
    requests_data = []
    for req in requests:
        requests_data.append({
            'id': req.id,
            'device_type': req.device_type,
            'device_type_text': get_device_type_text(req.device_type),
            'device_model': req.device_model,
            'issue_description': req.issue_description,
            'status': req.status,
            'status_text': get_status_text(req.status),
            'total_price': float(req.total_price) if req.total_price else 0,
            'created_at': req.created_at.strftime('%d.%m.%Y %H:%M') if req.created_at else '',
            'category_name': req.category.name if req.category else '',
            'master_name': req.assigned_master.full_name if req.assigned_master else None
        })
    
    return render_template('user.html', current_user=user, requests=requests_data)


@app.route('/master')
@master_or_admin_required
def master_page():
    """Панель мастера"""
    user = get_current_user()
    
    requests = RepairRequest.query.filter_by(master_id=user.id).order_by(RepairRequest.created_at.desc()).all()
    
    requests_data = []
    for req in requests:
        requests_data.append({
            'id': req.id,
            'device_type': req.device_type,
            'device_type_text': get_device_type_text(req.device_type),
            'device_model': req.device_model,
            'status': req.status,
            'status_text': get_status_text(req.status),
            'created_at': req.created_at.strftime('%d.%m.%Y %H:%M') if req.created_at else '',
            'client_name': req.client.full_name if req.client else ''
        })
    
    return render_template('master.html', current_user=user, requests=requests_data)

@app.route('/admin')
@admin_required
def admin_page():
    user = get_current_user()
    users = User.query.all()
    masters = User.query.filter_by(role='master').all()
    requests = RepairRequest.query.order_by(RepairRequest.created_at.desc()).all()
    
    requests_data = []
    for req in requests:
        requests_data.append({
            'id': req.id,
            'device_type': req.device_type,
            'device_type_text': get_device_type_text(req.device_type),
            'device_model': req.device_model,
            'status': req.status,
            'created_at': req.created_at.strftime('%d.%m.%Y %H:%M') if req.created_at else '',
            'client_name': req.client.full_name if req.client else '',
            'master_id': req.master_id
        })
    
    return render_template('admin.html', current_user=user, users=users, masters=masters, requests=requests_data)


@app.route('/admin/change-role/<int:user_id>', methods=['POST'])
@admin_required
def change_role(user_id):
    """Изменение роли пользователя"""
    user = User.query.get(user_id)
    if user and user.role != 'admin':
        new_role = request.form.get('new_role')
        user.role = new_role
        db.session.commit()
    return redirect(url_for('admin_page'))


@app.route('/admin/assign-master/<int:request_id>', methods=['POST'])
@admin_required
def assign_master(request_id):
    """Назначение мастера на заявку"""
    repair_request = RepairRequest.query.get(request_id)
    if repair_request:
        master_id = request.form.get('master_id')
        repair_request.master_id = master_id if master_id else None
        db.session.commit()
    return redirect(url_for('admin_page'))


@app.route('/admin/change-status/<int:request_id>', methods=['POST'])
@admin_required
def change_status(request_id):
    """Изменение статуса заявки"""
    repair_request = RepairRequest.query.get(request_id)
    if repair_request:
        new_status = request.form.get('new_status')
        repair_request.status = new_status
        db.session.commit()
    return redirect(url_for('admin_page'))


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'Ремонт24'}), 200
    
@app.route('/create-request', methods=['POST'])
@login_required
def create_request():
    """Создание новой заявки"""
    user = get_current_user()
    
    device_type = request.form.get('device_type')
    device_model = request.form.get('device_model')
    category_id = request.form.get('category_id')
    preferred_date = request.form.get('preferred_date')
    preferred_time = request.form.get('preferred_time')
    address = request.form.get('address')
    issue_description = request.form.get('issue_description')
    
    if not device_type or not category_id or not issue_description:
        return redirect(url_for('user_page') + '#create-request-form')
    
    category = RepairCategory.query.get(category_id)
    if not category:
        return redirect(url_for('user_page') + '#create-request-form')
    
    repair_request = RepairRequest(
        client_id=user.id,
        category_id=int(category_id),
        device_type=device_type,
        device_model=device_model,
        issue_description=issue_description,
        status='new',
        total_price=category.price
    )
    
    if preferred_date:
        repair_request.preferred_date = preferred_date
    if preferred_time:
        repair_request.preferred_time = preferred_time
    if address:
        repair_request.address = address
    
    db.session.add(repair_request)
    db.session.commit()
    
    return redirect(url_for('user_page') + '#requests-section')

@app.route('/request/<int:request_id>')
@login_required
def request_detail_page(request_id):
    user = get_current_user()
    
    repair_request = RepairRequest.query.get(request_id)
    if not repair_request:
        return "Заявка не найдена", 404
    
    if user.role == 'client' and repair_request.client_id != user.id:
        return "У вас нет доступа к этой заявке", 403
    
    if user.role == 'admin':
        back_url = '/admin'
    elif user.role == 'master':
        back_url = '/master'
    else:
        back_url = '/user'
    
    return render_template('request_detail.html', 
                         request=repair_request, 
                         back_url=back_url,
                         current_user=user)

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Пользователь уже существует'}), 409
    
    user = User(
        email=data['email'],
        full_name=data['full_name'],
        phone=data.get('phone'),
        role='client'
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'Регистрация успешна'}), 201


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    
    user = User.query.filter_by(email=data.get('email')).first()
    
    if not user or not user.check_password(data.get('password')):
        return jsonify({'error': 'Неверный email или пароль'}), 401
    
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = RepairCategory.query.filter_by(is_active=True).all()
    return jsonify([c.to_dict() for c in categories]), 200


@app.route('/api/requests', methods=['GET'])
@jwt_required()
def api_get_requests():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role == 'client':
        requests = RepairRequest.query.filter_by(client_id=user_id).order_by(RepairRequest.created_at.desc()).all()
    else:
        requests = RepairRequest.query.order_by(RepairRequest.created_at.desc()).all()
    
    return jsonify([r.to_dict() for r in requests]), 200


@app.route('/api/requests', methods=['POST'])
@jwt_required()
def api_create_request():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    category = RepairCategory.query.get(data['category_id'])
    if not category:
        return jsonify({'error': 'Категория не найдена'}), 404
    
    repair_request = RepairRequest(
        client_id=user_id,
        category_id=data['category_id'],
        device_type=data['device_type'],
        device_model=data.get('device_model'),
        issue_description=data['issue_description'],
        status='new',
        total_price=category.price
    )
    
    db.session.add(repair_request)
    db.session.commit()
    
    return jsonify(repair_request.to_dict()), 201

with app.app_context():
    print("\n" + "=" * 50)
    print("Ремонт24 - Запуск приложения")
    print("=" * 50)
    
    create_database_if_not_exists()
    
    try:
        db.create_all()
        print("Таблицы базы данных созданы/проверены")
    except Exception as e:
        print(f"Ошибка создания таблиц: {e}")
    
    print("\n" + "=" * 50)

if __name__ == '__main__':
    print("\nРемонт24 запущен!")
    print("http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)