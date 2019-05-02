from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from ..models import User


"""

The registration form uses the Regexp validation function provided by wtforms with a regular parameter to ensure that the nickname field contains only the user, the letter, the number, the underscore and the period.
The last two parameters are the regular flag and the error message for the verification failure.
The registration form has two custom validation functions, implemented as methods.
If a form with a validate_ followed by a field name is defined in the form class, this method is called with the regular validation function.
"""

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),Email()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('rememberme', default=False)


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),Email()])
    nickname = StringField('Nickname', validators=[
        DataRequired(), Length(1, 64), Regexp('^[\u4e00-\u9fa5]|[a-z]|[A-Z][0-9_.]*', 0,'nickname must start with letter or number')])
    password = PasswordField('Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('This email is Already in use')

    def validate_nickname(self, field):
        if User.query.filter_by(nickname=field.data).first():
            raise ValidationError('This Nickname is Already Taken')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm new password', validators=[DataRequired()])