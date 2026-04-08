from flask import Blueprint, render_template, redirect, url_for, flash, request
from .models import User, Post, Message, Review
from .forms import RegisterForm, LoginForm, PostForm, MessageForm, ProfileForm, ReviewForm
from . import db
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

main = Blueprint('main', __name__)

# Home
@main.route('/')
def home():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts)


# Register
@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)

        new_user = User(
            email=form.email.data,
            username=form.username.data,
            password=hashed_pw
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully!')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)


# Login
@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid email or password.')

    return render_template('login.html', form=form)

# Logout
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.')
    return redirect(url_for('main.login'))


# Profile
@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()

    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.major = form.major.data
        current_user.interests = form.interests.data

        db.session.commit()
        flash('Profile updated!')

    return render_template('profile.html', form=form)


# Create a post
@main.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()

    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            description=form.description.data,
            owner_id=current_user.id
        )

        db.session.add(post)
        db.session.commit()

        flash('Post created!')
        return redirect(url_for('main.home'))

    return render_template('create_post.html', form=form)


# View a post and message
@main.route('/post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = MessageForm()

    if form.validate_on_submit():
        message = Message(
            sender_id=current_user.id,
            receiver_id=post.owner_id,
            content=form.message.data
        )

        db.session.add(message)
        db.session.commit()

        flash('Message sent!')

    return render_template('post.html', post=post, form=form)


# Inbox message
@main.route('/messages')
@login_required
def messages():
    inbox = Message.query.filter_by(receiver_id=current_user.id).all()
    return render_template('messages.html', messages=inbox)


# Leave a review
@main.route('/review/<int:user_id>', methods=['GET', 'POST'])
@login_required
def review(user_id):
    form = ReviewForm()
    user = User.query.get_or_404(user_id)

    if form.validate_on_submit():
        review = Review(
            reviewer_id=current_user.id,
            reviewed_id=user.id,
            rating=form.rating.data,
            comment=form.comment.data
        )

        db.session.add(review)
        db.session.commit()

        flash('Review submitted!')
        return redirect(url_for('main.home'))

    return render_template('review.html', form=form, user=user)