import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import inspect, text
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'  # FIXED

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from . import routes
    app.register_blueprint(routes.main)  # FIXED

    with app.app_context():
        db.create_all()
        ensure_schema()
        ensure_hardcoded_admin()

    return app


def ensure_schema():
    """Add small SQLite columns used by the class project use cases."""
    inspector = inspect(db.engine)

    if 'users' in inspector.get_table_names():
        user_columns = {column['name'] for column in inspector.get_columns('user')}
        additions = {
            'is_blocked': 'BOOLEAN DEFAULT 0',
        }
        for name, definition in additions.items():
            if name not in user_columns:
                db.session.execute(text(f'ALTER TABLE user ADD COLUMN {name} {definition}'))

    if 'posts' in inspector.get_table_names():
        post_columns = {column['name'] for column in inspector.get_columns('post')}
        additions = {
            'category': "VARCHAR(80) DEFAULT 'General'",
            'price': 'NUMERIC(10, 2)',
            'condition': "VARCHAR(80) DEFAULT 'Good'",
            'status': "VARCHAR(80) DEFAULT 'Available'",
            'is_active': 'BOOLEAN DEFAULT 1',
        }
        for name, definition in additions.items():
            if name not in post_columns:
                db.session.execute(text(f'ALTER TABLE post ADD COLUMN {name} {definition}'))

    db.session.commit()


def ensure_hardcoded_admin():
    from .models import User

    admin = User.query.filter_by(email='admin@southernct.edu').first()
    if admin and (not admin.is_admin or admin.is_blocked):
        admin.is_admin = True
        admin.is_blocked = False
        db.session.commit()
