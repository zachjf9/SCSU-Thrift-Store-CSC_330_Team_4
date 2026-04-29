from . import db, login_manager
from flask_login import UserMixin
from datetime import datetime

# User
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)

    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    # Profile fields
    name = db.Column(db.String(150))
    major = db.Column(db.String(150))
    interests = db.Column(db.String(300))
    image = db.Column(db.String(200))  # store filename/path

    # Relationships
    posts = db.relationship('Post', backref='owner', lazy=True)
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)

    reviews_given = db.relationship('Review', foreign_keys='Review.reviewer_id', backref='reviewer', lazy=True)
    reviews_received = db.relationship('Review', foreign_keys='Review.reviewed_id', backref='reviewed', lazy=True)

# Posts
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    category = db.Column(db.String(80), default='General')
    image = db.Column(db.String(200))  # optional image path
    is_active = db.Column(db.Boolean, default=True)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign key
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Messages
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Reviews
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    rating = db.Column(db.Integer, nullable=False)  # 1–5
    comment = db.Column(db.String(300))

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Notifications
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(300), nullable=False)

    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Logging in
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
