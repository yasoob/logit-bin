from flask_wtf import Form
from wtforms import TextField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Required


class LoginForm(Form):
    email = TextField('email', validators=[DataRequired(), Email()])
    password = TextField('password', validators=[DataRequired()])


class SignupForm(Form):
    name = TextField('Name', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', [
        Required(),
        EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    email = TextField('Email', validators=[DataRequired(), Length(min=5, max=35), Email()])
