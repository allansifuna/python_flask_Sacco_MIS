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

class MemberRegPayForm(FlaskForm):
    phone = TelField('Phone Number')

class MakeDepositForm(FlaskForm):
    phone = TelField('Phone Number')
    amount = IntegerField('Amount', validators=[DataRequired()])

class ApplyLoanForm(FlaskForm):
    loan_category=QuerySelectField('Select Loan Category', validators=[DataRequired()], get_label='name', allow_blank=True)
    min_shares = StringField('Minimum Shares')
    max_amount = StringField('Maximum Amount')
    interest_rate = StringField('Interest Rate')
    repayment_duration = StringField('Repayment Duration')
    repayment_amount = StringField('Repayment Amount')
    loan_amount=IntegerField("Loan Amount", validators=[DataRequired()])

    def validate_loan_amount(self, loan_amount):
        mxa = int(self.max_amount.data.split(" ")[1])
        if int(loan_amount.data) > mxa:
            raise ValidationError('Loan Amount should be less that the Max Amount')
