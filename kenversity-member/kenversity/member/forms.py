from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, PasswordField, BooleanField, SelectField, FloatField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms.fields.html5 import TelField, DateField, EmailField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=8)])
    remember = BooleanField('Remember Me?')

class MemberRegistrationForm(FlaskForm):
    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    email = EmailField('Email')
    phone = TelField('Phone Number')
    national_id = StringField('National ID')
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password'), Length(min=8)])


class MemberDataForm(FlaskForm):
    id_front = FileField('ID Front', validators=[FileAllowed(['jpg', 'png'])])
    id_back = FileField('ID Back', validators=[FileAllowed(['jpg', 'png'])])
    kra_pin = FileField('KRA PIN Certificate', validators=[FileAllowed(['pdf'])])
    photo = FileField('Passport Photo', validators=[FileAllowed(['jpg', 'png'])])
