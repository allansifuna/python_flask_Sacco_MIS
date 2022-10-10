from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, PasswordField, BooleanField, SelectField, FloatField,TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms.fields.html5 import TelField, DateField, EmailField
from wtforms_sqlalchemy.fields import QuerySelectField

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=8)])
    remember = BooleanField('Remember Me?')

class AddLoanCategoriesForm(FlaskForm):
    name=StringField('Loan Category Name', validators=[DataRequired()])
    min_shares=IntegerField('Minimum Member Shares', validators=[DataRequired()])
    max_amount=IntegerField('Max Loan Amount', validators=[DataRequired()])
    repayment_duration=IntegerField('Repayment Duration In Months', validators=[DataRequired()])
    qualification_duration=IntegerField('Qualification Duration', validators=[DataRequired()])
    interest_rate=FloatField('Qualification Duration', validators=[DataRequired()])

class AddStaffForm(FlaskForm):
    first_name=StringField('First Name', validators=[DataRequired()])
    last_name=StringField('Last Name', validators=[DataRequired()])
    national_id=StringField('National ID', validators=[DataRequired()])
    email=StringField('Email Address', validators=[DataRequired(), Email()])
    phone_number=StringField('Phone Number', validators=[DataRequired()])
    role=SelectField('Select Staff Role', choices=[('', 'Select Staff Role...'),('ADMINSTRATOR', 'Adminstrator'), ('Staff', 'Staff')])

class SetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Password', validators=[
        DataRequired(), Length(min=8)])

class ApproveMemberForm(FlaskForm):
    first_name=StringField('First Name', validators=[DataRequired()])
    last_name=StringField('Last Name', validators=[DataRequired()])
    national_id=StringField('National ID', validators=[DataRequired()])
    reg_fees=IntegerField('Registration Fees', validators=[DataRequired()])
    verdict=SelectField('Select Verdict', choices=[('', 'Select Verdict ...'),('APPROVE', 'Approve'), ('DISAPPROVE', 'Disapprove')])
    reason=TextAreaField("Reason if Disapproved")

class DeclineLoanForm(FlaskForm):
    reason=TextAreaField("Reason for Declining")
