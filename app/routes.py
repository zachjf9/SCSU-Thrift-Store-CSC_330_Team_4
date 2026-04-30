from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from . import db
from .forms import LoginForm, MessageForm, PostForm, ProfileForm, RegisterForm, ReviewForm, UserAdminForm
from .models import Message, Notification, Post, Review, User

main = Blueprint('main', __name__)


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

    if search:
        pattern = f'%{search}%'
        query = query.filter((Post.title.ilike(pattern)) | (Post.description.ilike(pattern)))
    if category:
        query = query.filter_by(category=category)

    posts = query.order_by(Post.timestamp.desc()).all()
    categories = [row[0] for row in db.session.query(Post.category).distinct().order_by(Post.category).all() if row[0]]
    return render_template('index.html', posts=posts, categories=categories, search=search, selected_category=category)


@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        new_user = User(
            email=form.email.data.strip().lower(),
            username=form.username.data.strip(),
            password=generate_password_hash(form.password.data),
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
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()

        if user and user.is_blocked:
            flash('Your user account is blocked.')
            return redirect(url_for('main.home'))

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!')
            return redirect(url_for('main.home'))

        flash('Invalid email or password.')

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


@main.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()

    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
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
    return render_template('post.html', post=post, form=form, reviews=reviews)


@main.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.owner_id != current_user.id and not current_user.is_admin:
        flash('You can only edit your own listings.')
        return redirect(url_for('main.view_post', post_id=post.id))

    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data
        post.description = form.description.data
        post.category = form.category.data
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
    inbox = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.timestamp.desc()).all()
    return render_template('messages.html', messages=inbox)


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
    form = UserAdminForm(obj=user)

    if form.validate_on_submit():
        user.email = form.email.data.strip().lower()
        user.username = form.username.data.strip()
        user.name = form.name.data
        user.major = form.major.data
        user.is_admin = form.is_admin.data
        user.is_blocked = form.is_blocked.data
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

    Message.query.filter((Message.sender_id == user.id) | (Message.receiver_id == user.id)).delete(synchronize_session=False)
    Review.query.filter((Review.reviewer_id == user.id) | (Review.reviewed_id == user.id)).delete(synchronize_session=False)
    Notification.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    Post.query.filter_by(owner_id=user.id).delete(synchronize_session=False)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.')
    return redirect(url_for('main.admin_users'))
