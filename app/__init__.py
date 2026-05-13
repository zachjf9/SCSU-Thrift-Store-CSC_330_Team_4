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

    return app


def ensure_schema():
    """Add missing columns used by the class project use cases."""
    inspector = inspect(db.engine)

    if 'users' in inspector.get_table_names():
        user_columns = {column['name'] for column in inspector.get_columns('user')}
        additions = {
            'is_blocked': 'BOOLEAN DEFAULT FALSE',
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
            'is_active': 'BOOLEAN DEFAULT TRUE',
        }
        for name, definition in additions.items():
            if name not in post_columns:
                db.session.execute(text(f'ALTER TABLE post ADD COLUMN {name} {definition}'))

    db.session.commit()
