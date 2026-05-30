from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from config import Config
from app.models import db, User, RepairCategory, RepairRequest, RequestComment, SparePart, RequestSparePart

app = Flask(__name__)
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
            print(f" База данных '{db_name}' успешно создана!")
        else:
            print(f" База данных '{db_name}' уже существует")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f" Ошибка при проверке/создании БД: {e}")
        print("   Убедитесь, что PostgreSQL запущен и параметры подключения верны")

@app.route('/')
def index_page():
    return render_template('index.html')

@app.route('/health')
def health():
    from flask import jsonify
    return jsonify({'status': 'ok', 'service': 'Ремонт24'}), 200

with app.app_context():
    print("\n" + "=" * 50)
    print(" Ремонт24 - Создание базы данных")
    print("=" * 50)
    
    create_database_if_not_exists()
    try:
        db.create_all()
        print(" Таблицы базы данных созданы/проверены")
        
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\n Созданные таблицы ({len(tables)}):")
        for table in tables:
            print(f"   - {table}")
            
    except Exception as e:
        print(f" Ошибка создания таблиц: {e}")
    
    print("\n" + "=" * 50)
    print("Готово! База данных и таблицы созданы")
    print("=" * 50)

if __name__ == '__main__':
    app.run()