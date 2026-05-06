from functools import wraps
from datetime import datetime, timedelta
import os 
from uuid import uuid4

from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from . import db
from .forms import LoginForm, MessageForm, PostForm, ProfileForm, RegisterForm, ReviewForm, UserAdminForm
from .models import Favorite, Message, Notification, Post, Review, User

main = Blueprint('main', __name__)
ADMIN_EMAIL = 'admin@southernct.edu'


def is_hardcoded_admin(email):
    return email and email.strip().lower() == ADMIN_EMAIL


def sync_admin_status(user):
    if user and is_hardcoded_admin(user.email) and (not user.is_admin or user.is_blocked):
        user.is_admin = True
        user.is_blocked = False
        db.session.commit()

def allowed_image(filename):
    allowed_extensions = current_app.config.get('ALLOWED_IMAGE_EXTENSIONS', set())
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_listing_image(image_file):
    if not image_file or not image_file.filename:
        return None, None

    if not allowed_image(image_file.filename):
        return None, 'Please upload a PNG, JPG, JPEG, GIF, or WEBP image.'

    original_name = secure_filename(image_file.filename)
    extension = original_name.rsplit('.', 1)[1].lower()
    filename = f'{uuid4().hex}.{extension}'
    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    image_file.save(image_path)
    return filename, None


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.')
            return redirect(url_for('main.home'))
        return view(*args, **kwargs)

    return wrapped


@main.route('/')
def home():
    query = Post.query.filter_by(is_active=True)
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    date_filter = request.args.get('date_filter', '').strip()

    if search:
        pattern = f'%{search}%'
        query = query.filter((Post.title.ilike(pattern)) | (Post.description.ilike(pattern)))
    if category:
        query = query.filter_by(category=category)
    if date_filter == '7':
        query = query.filter(Post.timestamp >= datetime.utcnow() - timedelta(days=7))
    elif date_filter == '30':
        query = query.filter(Post.timestamp >= datetime.utcnow() - timedelta(days=30))

    posts = query.order_by(Post.timestamp.desc()).all()
    categories = [row[0] for row in db.session.query(Post.category).distinct().order_by(Post.category).all() if row[0]]
    favorite_post_ids = set()
    if current_user.is_authenticated:
        favorite_post_ids = {favorite.post_id for favorite in Favorite.query.filter_by(user_id=current_user.id).all()}

    return render_template(
        'index.html',
        posts=posts,
        categories=categories,
        search=search,
        selected_category=category,
        selected_date_filter=date_filter,
        favorite_post_ids=favorite_post_ids,
    )


@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        new_user = User(
            email=email,
            username=form.username.data.strip(),
            password=generate_password_hash(form.password.data),
            is_admin=is_hardcoded_admin(email),
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        sync_admin_status(user)

        if user and user.is_blocked:
            flash('Your user account is blocked.')
            return redirect(url_for('main.home'))

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!')
            return redirect(url_for('main.home'))

        flash('Invalid username or password.')

    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.')
    return redirect(url_for('main.login'))


@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    sync_admin_status(current_user)
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.major = form.major.data
        current_user.interests = form.interests.data
        db.session.commit()
        flash('Profile updated!')
        return redirect(url_for('main.profile'))

    received_reviews = Review.query.filter_by(reviewed_id=current_user.id).order_by(Review.timestamp.desc()).all()
    authored_reviews = Review.query.filter_by(reviewer_id=current_user.id).order_by(Review.timestamp.desc()).all()
    return render_template('profile.html', form=form, received_reviews=received_reviews, authored_reviews=authored_reviews)


@main.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return redirect(url_for('main.profile'))

    listings = (
        Post.query
        .filter_by(owner_id=user.id, is_active=True)
        .order_by(Post.timestamp.desc())
        .all()
    )
    reviews = Review.query.filter_by(reviewed_id=user.id).order_by(Review.timestamp.desc()).all()
    return render_template('view_profile.html', user=user, listings=listings, reviews=reviews)


@main.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()

    if form.validate_on_submit():
        image_filename, image_error = save_listing_image(form.image.data)
        if image_error:
            flash(image_error)
            return render_template('post_form.html', form=form, title='Create Listing')

        post = Post(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            price=form.price.data,
            condition=form.condition.data,
            status=form.status.data,
            image=image_filename,
            owner_id=current_user.id,
        )
        db.session.add(post)
        db.session.commit()
        flash('Listing created!')
        return redirect(url_for('main.view_post', post_id=post.id))

    return render_template('post_form.html', form=form, title='Create Listing')


@main.route('/post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = MessageForm()

    if form.validate_on_submit():
        message = Message(sender_id=current_user.id, receiver_id=post.owner_id, content=form.message.data)
        db.session.add(message)
        db.session.commit()
        flash('Message sent!')
        return redirect(url_for('main.view_post', post_id=post.id))

    reviews = Review.query.filter_by(reviewed_id=post.owner_id).order_by(Review.timestamp.desc()).all()
    is_favorite = Favorite.query.filter_by(user_id=current_user.id, post_id=post.id).first() is not None
    return render_template('post.html', post=post, form=form, reviews=reviews, is_favorite=is_favorite)


@main.route('/favorites')
@login_required
def favorites():
    saved_posts = (
        Post.query
        .join(Favorite, Favorite.post_id == Post.id)
        .filter(Favorite.user_id == current_user.id, Post.is_active == True)
        .order_by(Favorite.timestamp.desc())
        .all()
    )
    return render_template('favorites.html', posts=saved_posts)


@main.route('/post/<int:post_id>/favorite', methods=['POST'])
@login_required
def favorite_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.owner_id == current_user.id:
        flash('You cannot favorite your own listing.')
        return redirect(url_for('main.view_post', post_id=post.id))

    existing_favorite = Favorite.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if not existing_favorite:
        db.session.add(Favorite(user_id=current_user.id, post_id=post.id))
        db.session.commit()
        flash('Listing added to favorites.')

    return redirect(request.referrer or url_for('main.view_post', post_id=post.id))


@main.route('/post/<int:post_id>/unfavorite', methods=['POST'])
@login_required
def unfavorite_post(post_id):
    favorite = Favorite.query.filter_by(user_id=current_user.id, post_id=post_id).first_or_404()
    db.session.delete(favorite)
    db.session.commit()
    flash('Listing removed from favorites.')
    return redirect(request.referrer or url_for('main.favorites'))


@main.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.owner_id != current_user.id and not current_user.is_admin:
        flash('You can only edit your own listings.')
        return redirect(url_for('main.view_post', post_id=post.id))

    form = PostForm(obj=post)
    if form.validate_on_submit():
        image_filename, image_error = save_listing_image(form.image.data)
        if image_error:
            flash(image_error)
            return render_template('post_form.html', form=form, title='Edit Listing')

        post.title = form.title.data
        post.description = form.description.data
        post.category = form.category.data
        post.price = form.price.data
        post.condition = form.condition.data
        post.status = form.status.data
        if image_filename:
            post.image = image_filename
        db.session.commit()
        flash('Listing updated!')
        return redirect(url_for('main.view_post', post_id=post.id))

    return render_template('post_form.html', form=form, title='Edit Listing')


@main.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.owner_id != current_user.id and not current_user.is_admin:
        flash('You can only delete your own listings.')
        return redirect(url_for('main.view_post', post_id=post.id))

    post.is_active = False
    db.session.commit()
    flash('Listing deleted.')
    return redirect(url_for('main.home'))


@main.route('/messages')
@login_required
def messages():
    all_messages = (
        Message.query
        .filter(or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id))
        .order_by(Message.timestamp.asc())
        .all()
    )

    conversations_by_user = {}
    for message in all_messages:
        other_user = message.receiver if message.sender_id == current_user.id else message.sender
        conversations_by_user.setdefault(other_user.id, {
            'user': other_user,
            'messages': [],
            'last_message': None,
        })
        conversations_by_user[other_user.id]['messages'].append(message)
        conversations_by_user[other_user.id]['last_message'] = message

    conversations = sorted(
        conversations_by_user.values(),
        key=lambda conversation: conversation['last_message'].timestamp,
        reverse=True,
    )

    form = MessageForm()
    return render_template('messages.html', conversations=conversations, form=form)


@main.route('/messages/<int:message_id>/reply', methods=['POST'])
@login_required
def reply_message(message_id):
    original_message = Message.query.get_or_404(message_id)
    if original_message.receiver_id != current_user.id:
        flash('You can only reply to messages sent to you.')
        return redirect(url_for('main.messages'))

    form = MessageForm()
    if form.validate_on_submit():
        reply = Message(
            sender_id=current_user.id,
            receiver_id=original_message.sender_id,
            content=form.message.data,
        )
        db.session.add(reply)
        db.session.commit()
        flash('Reply sent!')
    else:
        flash('Reply cannot be empty.')

    return redirect(url_for('main.messages'))


@main.route('/messages/user/<int:user_id>/reply', methods=['POST'])
@login_required
def reply_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot message yourself.')
        return redirect(url_for('main.messages'))

    form = MessageForm()
    if form.validate_on_submit():
        reply = Message(
            sender_id=current_user.id,
            receiver_id=user.id,
            content=form.message.data,
        )
        db.session.add(reply)
        db.session.commit()
        flash('Reply sent!')
    else:
        flash('Reply cannot be empty.')

    return redirect(url_for('main.messages'))


@main.route('/review/<int:user_id>', methods=['GET', 'POST'])
@login_required
def review(user_id):
    form = ReviewForm()
    user = User.query.get_or_404(user_id)

    if form.validate_on_submit():
        new_review = Review(
            reviewer_id=current_user.id,
            reviewed_id=user.id,
            rating=form.rating.data,
            comment=form.comment.data,
        )
        db.session.add(new_review)
        db.session.commit()
        flash('Review submitted!')
        return redirect(url_for('main.home'))

    return render_template('review.html', form=form, user=user, title='Create Review')


@main.route('/review/<int:review_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    existing_review = Review.query.get_or_404(review_id)
    if existing_review.reviewer_id != current_user.id and not current_user.is_admin:
        flash('You can only edit your own reviews.')
        return redirect(url_for('main.home'))

    form = ReviewForm(obj=existing_review)
    if form.validate_on_submit():
        existing_review.rating = form.rating.data
        existing_review.comment = form.comment.data
        db.session.commit()
        flash('Review updated!')
        return redirect(url_for('main.profile'))

    return render_template('review.html', form=form, user=existing_review.reviewed, title='Edit Review')


@main.route('/review/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    existing_review = Review.query.get_or_404(review_id)
    if existing_review.reviewer_id != current_user.id and not current_user.is_admin:
        flash('You can only delete your own reviews.')
        return redirect(url_for('main.home'))

    db.session.delete(existing_review)
    db.session.commit()
    flash('Review deleted.')
    return redirect(url_for('main.profile'))


@main.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.order_by(User.username).all()
    return render_template('admin_users.html', users=users)


@main.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    sync_admin_status(user)
    form = UserAdminForm(obj=user)

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user.email = email
        user.username = form.username.data.strip()
        user.name = form.name.data
        user.major = form.major.data
        user.is_admin = form.is_admin.data or is_hardcoded_admin(email)
        user.is_blocked = False if is_hardcoded_admin(email) else form.is_blocked.data
        db.session.commit()
        flash('User updated.')
        return redirect(url_for('main.admin_users'))

    return render_template('admin_user_form.html', form=form, user=user)


@main.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account while logged in.')
        return redirect(url_for('main.admin_users'))

    user_post_ids = [post.id for post in Post.query.filter_by(owner_id=user.id).all()]
    Favorite.query.filter(Favorite.user_id == user.id).delete(synchronize_session=False)
    if user_post_ids:
        Favorite.query.filter(Favorite.post_id.in_(user_post_ids)).delete(synchronize_session=False)
    Message.query.filter((Message.sender_id == user.id) | (Message.receiver_id == user.id)).delete(synchronize_session=False)
    Review.query.filter((Review.reviewer_id == user.id) | (Review.reviewed_id == user.id)).delete(synchronize_session=False)
    Notification.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    Post.query.filter_by(owner_id=user.id).delete(synchronize_session=False)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.')
    return redirect(url_for('main.admin_users'))
