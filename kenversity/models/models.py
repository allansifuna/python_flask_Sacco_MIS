from kenversity import db
from datetime import datetime
import secrets
from kenversity import app


def id_unique():
    return secrets.token_hex(8)

class Member(db.Model):
    memberID = db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    first_name=db.Column(db.String(40),nullable=False)
    last_name=db.Column(db.String(40),nullable=False)
    national_id=db.Column(db.String(9),nullable=False)
    email=db.Column(db.String(40),nullable=False)
    id_front=db.Column(db.String(255),nullable=False)
    id_back=db.Column(db.String(255),nullable=False)
    kra_pin=db.Column(db.String(255),nullable=False)
    phone_number=db.Column(db.String(40),nullable=False,unique=True)
    created_at=db.Column(db.Datetime,default=datetime.utc_now,nullable=False)
    status=db.Column(db.String(40),default="INACTIVE")
    deposits = db.relationship('Deposit', backref='member', lazy=True)
    collaterals = db.relationship('Collateral', backref='member', lazy=True)
    guarantors=db.relationship('Guarantor', backref='applicant', lazy=True)
    otps=db.relationship('OTP', backref='member', lazy=True)
    loans=db.relationship('Loan', backref='loan_applier', lazy=True)
    repayments=db.relationship('Repayment', backref='member', lazy=True)

class Staff(db.Model):
    staffID = db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    first_name=db.Column(db.String(40),nullable=False)
    last_name=db.Column(db.String(40),nullable=False)
    national_id=db.Column(db.String(9),nullable=False)
    email=db.Column(db.String(40),nullable=False)
    phone_number=db.Column(db.String(40),nullable=False)
    role=db.Column(db.String(20),nullable=False)
    created_at=db.Column(db.Datetime,default=datetime.utc_now,nullable=False)
    status=db.Column(db.String(40),default="INACTIVE")
    approved_collaterals = db.relationship('Collateral', backref='collateral_approver', lazy=True)
    approved_loans = db.relationship('Loan', backref='loan_approver', lazy=True)
    approved_guarantors = db.relationship('Guarantor', backref='guarantor_approver', lazy=True)

class Deposit(db.Model):
    depositID = db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberID=db.Column(db.String(8), db.ForeignKey('member.memberID'),nullable=False)
    transactionID=db.Column(db.String(8),db.ForeignKey('transaction.transactionID'),nullable=False)
    deposit_date=db.Column(db.Datetime,default=datetime.utc_now,nullable=False)
    amount=db.Column(db.Integer,nullable=False)

class Collateral(db.Model):
    collateralID= db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberID=db.Column(db.String(8),db.ForeignKey('member.memberID'),nullable=False)
    loanID=db.Column(db.String(8),db.ForeignKey('loan.loanID'),nullable=False)
    name=db.Column(db.String(50),nullable=False)
    description=db.Column(db.String(255),nullable=False)
    value=db.Column(db.Integer,nullable=False)
    status=db.Column(db.String(40),default="UNAPPROVED")
    staffID=db.Column(db.String(8),db.ForeignKey('staff.staffID'),nullable=False)

class Guarantor(db.Model):
    guarantorID=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberID=db.Column(db.String(8),db.ForeignKey('member.memberID'),nullable=False)
    loanID=db.Column(db.String(8),db.ForeignKey('loan.loanID'),nullable=False)
    status=db.Column(db.String(40),default="UNAPPROVED")
    staffID=db.Column(db.String(8),db.ForeignKey('staff.staffID'),nullable=False)

class LoanCategories(db.Model):
    loan_categoryID=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    name=db.Column(db.String(50),nullable=False)
    min_shares=db.Column(db.Integer,nullable=False)
    max_amount=db.Column(db.Integer,nullable=False)
    repayment_duration=db.Column(db.Integer,nullable=False)
    qualification_duration=db.Column(db.Integer,nullable=False)
    interest_rate=db.Column(db.Float,nullable=False)
    loans=db.relationship('Loan', backref='loan_category', lazy=True)

class OTP(db.Model):
    otpID=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberID=db.Column(db.String(8),db.ForeignKey('member.memberID'),nullable=False)
    password=db.Column(db.String(4),nullable=False)
    status=db.Column(db.String(40),default="UNUSED")
    date_created=db.Column(db.Datetime,default=datetime.utc_now,nullable=False)

class Loan(db.Model):
    loanID=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberID=db.Column(db.String(8),db.ForeignKey('member.memberID'),nullable=False)
    loan_categoryID=db.Column(db.String(8),db.ForeignKey('loan_category.loan_categoryID'),nullable=False)
    staffID=db.Column(db.String(8),db.ForeignKey('staff.staffID'),nullable=False)
    amount=db.Column(db.Integer,nullable=False)
    start_date=db.Column(db.Date,nullable=False)
    end_date=db.Column(db.Date,nullable=False)
    status=db.Column(db.String(40),default="UNAPPROVED")
    date_created=db.Column(db.Datetime,default=datetime.utc_now,nullable=False)
    guarantors=db.relationship('Guarantor', backref='loan_guarantor', lazy=True)
    repayments=db.relationship('Repayment', backref='loan_repayment', lazy=True)
    collaterals=db.relationship('Collateral', backref='loan_collaterals', lazy=True)
    transactionID=db.Column(db.String(8),db.ForeignKey('transaction.transactionID'),nullable=True)

class Transaction(db.Model):
    transactionID=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    phone_number=db.Column(db.String(40),nullable=False)
    transactionCode=db.Column(db.String(40),nullable=False)
    amount=db.Column(db.Integer,nullable=False)
    date_created=db.Column(db.Datetime,default=datetime.utc_now,nullable=False)
    repayments=db.relationship('Repayment', backref='repayment_transaction', lazy=True)
    deposits=db.relationship('Deposit', backref='deposit_transaction', lazy=True)
    loans=db.relationship('Loan', backref='loan_transaction', lazy=True)


class Repayment(db.Model):
    repaymentID=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberID=db.Column(db.String(8),db.ForeignKey('member.memberID'),nullable=False)
    loanID=db.Column(db.String(8),db.ForeignKey('loan.loanID'),nullable=False)
    transactionID=db.Column(db.String(8),db.ForeignKey('transaction.transactionID'),nullable=False)
    amount=db.Column(db.Integer,nullable=False)
    date_created=db.Column(db.Datetime,default=datetime.utc_now,nullable=False)
