from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=4, max=20, message='Username must be between 4 and 20 characters')
    ])
    user_id = StringField('User ID', validators=[
        DataRequired(message='User ID is required'),
        Length(min=4, max=20, message='User ID must be between 4 and 20 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    phone = StringField('Mobile Number', validators=[
        DataRequired(message='Mobile number is required'),
        Length(min=10, max=15, message='Mobile number must be between 10 and 15 digits')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(max=50)
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(),
        Length(max=50)
    ])
    address = TextAreaField('Address', validators=[
        DataRequired()
    ])
    city = StringField('City', validators=[
        DataRequired(),
        Length(max=50)
    ])
    state = StringField('State', validators=[
        DataRequired(),
        Length(max=50)
    ])
    postal_code = StringField('Postal Code', validators=[
        DataRequired(),
        Length(max=20)
    ])
    country = StringField('Country', validators=[
        DataRequired(),
        Length(max=50)
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')

    def validate_user_id(self, user_id):
        user = User.query.filter_by(user_id=user_id.data).first()
        if user:
            raise ValidationError('User ID already exists. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already exists. Please use a different one.') 