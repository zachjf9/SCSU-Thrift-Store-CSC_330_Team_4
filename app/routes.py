from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from . import db
from .models import User
from .forms import LoginForm, RegisterForm

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

# Routes for all of the app functionalities