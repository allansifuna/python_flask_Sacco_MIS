from flask_wtf import FlaskForm
from flask_login import current_user
from flask import flash
from wtforms import StringField, IntegerField, SubmitField, PasswordField, BooleanField, SelectField, FloatField,TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms.fields.html5 import TelField, DateField, EmailField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed
from kenversity.models import Member
import re
from datetime import date, timedelta,datetime

class NullableDateField(DateField):
    """Native WTForms DateField throws error for empty dates.
    Let's fix this so that we could have DateField nullable."""
    def process_formdata(self, valuelist):
        if valuelist:
            date_str = ' '.join(valuelist).strip()
            if date_str == '':
                self.data = None
                return
            try:
                self.data = datetime.strptime(date_str, self.format).date()
            except ValueError:
                self.data = None
                raise ValueError(self.gettext('Not a valid date value'))

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=8)])
    remember = BooleanField('Remember Me?')

class MemberRegistrationForm(FlaskForm):
    first_name = StringField('First Name',validators=[DataRequired(), Length(min=2)])
    last_name = StringField('Last Name',validators=[DataRequired(), Length(min=2)])
    email = EmailField('Email',validators=[DataRequired(), Email()])
    phone = TelField('Phone Number')
    national_id = StringField('National ID', validators=[Length(min=8,max=8)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password'), Length(min=8)])

    def validate_email(self, email):
        member = Member.query.filter_by(email=email.data).first()
        if member:
            raise ValidationError('There is an existing account with that email. Use another email to register.')
    def validate_phone(self,phone):
        pattern="\+?(254|0)(7|1)\d{8}"
        phone_number=phone.data
        if not re.match(pattern,phone_number):
            raise ValidationError('Invalid Phone Number!!!!')
        member = Member.query.filter_by(phone_number=phone.data).first()
        if member:
            raise ValidationError('There is an existing account with that phone number. Use another phone number to register.')

class MemberUpdateDetailsForm(FlaskForm):
    first_name = StringField('First Name',validators=[DataRequired(), Length(min=2)])
    last_name = StringField('Last Name',validators=[DataRequired(), Length(min=2)])
    email_addr = EmailField('Email',validators=[DataRequired(), Email()])
    phone_no = TelField('Phone Number')
    national_id = StringField('National ID', validators=[Length(min=8,max=8)])
    submit1 = SubmitField('Save')

    def validate_email_addr(self, email):
        member = Member.query.filter_by(email=email.data).first()
        if member and member.id != current_user.id:
            flash("Email already Exists","danger")
            raise ValidationError('There is an existing account with that email. Use another email to register.')

    def validate_phone_no(self,phone):
        pattern="\+?(254|0)(7|1)\d{8}"
        phone_number=phone.data
        if not re.match(pattern,phone_number):
            flash("Invalid Phone Number","danger")
            raise ValidationError('Invalid Phone Number!!!!')
        if phone.data.startswith("0"):
            phone_no=f"254{phone.data[1:]}"
        elif phone.data.startswith("+"):
            phone_no=phone.data[1:]
        else:
            phone_no=phone.data
        member = Member.query.filter_by(phone_number=phone_no).first()
        if member and member.id != current_user.id:
            flash("Phone number already exists","danger")
            raise ValidationError('There is an existing account with that phone number. Use another phone number to register.')


class MemberDataForm(FlaskForm):
    id_front = FileField('ID Front', validators=[FileAllowed(['jpg', 'png']),DataRequired()])
    id_back = FileField('ID Back', validators=[FileAllowed(['jpg', 'png']),DataRequired()])
    kra_pin = FileField('KRA PIN Certificate', validators=[FileAllowed(['pdf']),DataRequired()])
    photo = FileField('Passport Photo', validators=[FileAllowed(['jpg', 'png']),DataRequired()])
    submit4 = SubmitField('Save')

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

class SearchGuatantorForm(FlaskForm):
    name = StringField('First Name or Last Name or Email or Phone Number')
    guarantor=SelectField('Select Guarantor', choices=[('','')])

class AddCollateralForm(FlaskForm):
    name = StringField('Collateral Name')
    description = TextAreaField('Collateral Description')
    value = IntegerField("Collateral Value")

class MemberBioDataForm(FlaskForm):
    dob=DateField("Enter Date Of Birth")
    gender = SelectField('Select Gender', choices=[('','Select Gender'),('Male','Male'),('Female','Female')])
    marital_status = SelectField('Select Marital Status', choices=[('','Select Marital Status'),('Single','Single'),('Married','Married'),('Married','Married'),('Widowed','Widowed')])
    number_of_dependants = IntegerField('Number of dependants')
    address = StringField('Physical Address')
    town = StringField('Town')
    estate = StringField('Estate')
    street = StringField('Street')
    house_number = StringField('Enter House Number')
    house_ownership = SelectField('Select House Ownership', choices=[('','Select House Ownership'),('Rented','Rented'),('Owned','Owned')])
    bank_name = StringField('Bank Name')
    bank_account = StringField('Bank Account No.')
    submit = SubmitField('Save')

    def validate_dob(self,dob):
        today=date.today()
        y=365*18
        t_delta=timedelta(days=y)
        ago=today-t_delta

        if ago < dob.data:
            flash("Invalid Date of Birth","danger")
            raise ValidationError('Invalid Date of Birth')

class MemberEmplDataForm(FlaskForm):
    employment_status = SelectField('Select Employement Status', choices=[('','Select Employment Status'),('Employed','Employed'),('Self-Employed','Self-Employed')])
    name=StringField("Employer Name")
    address=StringField("Employer Address")
    phone=TelField("Employer Tel.")
    retirement_date=NullableDateField("Enter Date Of Retirement")
    business_type=StringField("Business Type")
    years_of_operation=IntegerField("Years of Operation")
    business_income=IntegerField("Business Income in KES")
    employment_terms = SelectField('Select Employment Terms', choices=[('','Select Employment Terms'),('Permanent','Permanent'),('Casual','Casual'),('Contarct','Contarct')])
    submit2 = SubmitField('Save')



class MakeRepaymentForm(FlaskForm):
    loan=QuerySelectField('Select Loan', validators=[DataRequired()], get_label='loanNo', allow_blank=True)
    amount=IntegerField("Amount",validators=[DataRequired()])

class PasswordResetForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password'), Length(min=8)])


class ResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        member = Member.query.filter_by(email=email.data).first()
        if member is None:
            raise ValidationError('There is no account with that email. You must register first.')

class OpenTicketForm(FlaskForm):
    issue=SelectField('What is your issue about? ', choices=[('','Select ...'),('Deposits','Deposits'),('Loans','Loans'),('Repayments','Repayments')])
    message=TextAreaField("Ticket Description")

class UpdateTicketForm(FlaskForm):
    ticket_id=StringField()
    message=TextAreaField("Add Description.")

class MockDepositForm(FlaskForm):
    num=IntegerField("Number of Deposits",validators=[DataRequired()])

class MockLoanRepaymentForm(FlaskForm):
    mocks=IntegerField("Number of Deposits",validators=[DataRequired()])
    loan_no=StringField("Loan No",validators=[DataRequired()])
