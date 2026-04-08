from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length

"""
The kind of forms that we will have
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from .models import User

# Registration
class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=150)
    ])
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=150)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password')
    ])
    submit = SubmitField('Register')

    # Restrict to @southernct.edu
    def validate_email(self, email):
        if not email.data.endswith("@southernct.edu"):
            raise ValidationError("Must use a Southern Connecticut State University email.")

        existing_user = User.query.filter_by(email=email.data).first()
        if existing_user:
            raise ValidationError("Email already registered.")
    
    def validate_username(self, username):
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user:
            raise ValidationError("Username already exists.")
# Login
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])
    submit = SubmitField('Login')

# Profile
class ProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[Length(max=150)])
    major = StringField('Major', validators=[Length(max=150)])
    interests = TextAreaField('Interests', validators=[Length(max=300)])
    image = FileField('Profile Image')  # optional
    submit = SubmitField('Update Profile')


# Post
class PostForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(),
        Length(max=150)
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(max=300)
    ])
    image = FileField('Image')  # optional
    submit = SubmitField('Create Post')
    
# User Messaging
class MessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[
        DataRequired(),
        Length(max=500)
    ])
    submit = SubmitField('Send')

# Reviews
class ReviewForm(FlaskForm):
    rating = StringField('Rating (1-5)', validators=[
        DataRequired()
    ])
    comment = TextAreaField('Comment', validators=[
        Length(max=300)
    ])
    submit = SubmitField('Submit Review')