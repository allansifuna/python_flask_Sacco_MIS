from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, PasswordField, BooleanField, SelectField, FloatField,TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms.fields.html5 import TelField, DateField, EmailField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed
from kenversity.models import Member

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
                self.data = datetime.datetime.strptime(date_str, self.format).date()
            except ValueError:
                self.data = None
                raise ValueError(self.gettext('Not a valid date value'))

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
