from kenversity import db,lm
from flask import current_app
from flask_login import UserMixin
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import secrets

class CRUDMixin:
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def update(self):
        db.session.commit()
        return self

#staff=Staff(first_name="Admin",last_name="Strator",national_id="32452134",email="admin@kenversity.com",phone_number="254714812912",role="ADMINSTARTOR",status="Active")
@lm.user_loader
def load_staff(id):
    return Staff.query.get(str(id))


def id_unique():
    return secrets.token_hex(8)

class Member(db.Model,UserMixin, CRUDMixin):
    id = db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberNo=db.Column(db.String(5),nullable=True)
    first_name=db.Column(db.String(40),nullable=True)
    last_name=db.Column(db.String(40),nullable=True)
    national_id=db.Column(db.String(8),nullable=True)
    email=db.Column(db.String(40),nullable=True)
    id_front=db.Column(db.String(255),nullable=True)
    id_back=db.Column(db.String(255),nullable=True)
    kra_pin=db.Column(db.String(255),nullable=True)
    photo=db.Column(db.String(255),nullable=True,default="default.jpg")
    password=db.Column(db.String(255),nullable=True)
    phone_number=db.Column(db.String(12),nullable=True,unique=True)
    created_at=db.Column(db.DateTime,default=datetime.now,nullable=False)
    status=db.Column(db.String(40),default="INACTIVE")
    email_confirmed=db.Column(db.String(40),default="FALSE")
    staffID=db.Column(db.String(8),db.ForeignKey('staff.id'),nullable=True)
    deposits = db.relationship('Deposit', backref='member', lazy=True)
    collaterals = db.relationship('Collateral', backref='member', lazy=True)
    guarantors=db.relationship('Guarantor', backref='applicant', lazy=True)
    otps=db.relationship('OTP', backref='member', lazy=True)
    loans=db.relationship('Loan', backref='loan_applier', lazy=True)
    repayments=db.relationship('Repayment', backref='member', lazy=True)

    def __repr__(self):
        return f"{self.memberNo}-<{self.first_name}|{self.last_name}>"

    def get_reset_token(self, expires_sec=18000):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'memberID': self.memberID}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            memberID = s.loads(token)['memberID']
        except Exception as e:
            return None
        return Member.query.get(memberID)

class Staff(db.Model,UserMixin, CRUDMixin):
    id = db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    first_name=db.Column(db.String(40),nullable=False)
    last_name=db.Column(db.String(40),nullable=False)
    national_id=db.Column(db.String(8),nullable=False)
    email=db.Column(db.String(40),nullable=False)
    phone_number=db.Column(db.String(12),nullable=False)
    role=db.Column(db.String(20),nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.now,nullable=False)
    status=db.Column(db.String(40),default="INACTIVE")
    password=db.Column(db.String(255),nullable=True)
    approved_collaterals = db.relationship('Collateral', backref='collateral_approver', lazy=True)
    approved_loans = db.relationship('Loan', backref='loan_approver', lazy=True)
    approved_guarantors = db.relationship('Guarantor', backref='guarantor_approver', lazy=True)
    approved_members = db.relationship('Member', backref='member_approver', lazy=True)

    def __repr__(self):
        return f"<{self.first_name}|{self.last_name}>"

    def get_reset_token(self, expires_sec=18000):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            id = s.loads(token)['id']
        except Exception as e:
            return None
        return Staff.query.get(id)

class Deposit(db.Model, CRUDMixin):
    id = db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberID=db.Column(db.String(8), db.ForeignKey('member.id'),nullable=False)
    transactionID=db.Column(db.String(8),db.ForeignKey('transaction.id'),nullable=True)
    deposit_date=db.Column(db.DateTime,default=datetime.now,nullable=False)
    amount=db.Column(db.Integer,nullable=True)
    CheckoutRequestID=db.Column(db.String(30),nullable=True)

    def __repr__(self):
        return f"<{self.depositID}|{self.amount}>"

class Collateral(db.Model, CRUDMixin):
    id= db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberID=db.Column(db.String(8),db.ForeignKey('member.id'),nullable=False)
    loanID=db.Column(db.String(8),db.ForeignKey('loan.id'),nullable=False)
    name=db.Column(db.String(50),nullable=False)
    description=db.Column(db.String(255),nullable=False)
    value=db.Column(db.Integer,nullable=False)
    status=db.Column(db.String(40),default="UNAPPROVED")
    staffID=db.Column(db.String(8),db.ForeignKey('staff.id'),nullable=False)

    def __repr__(self):
        return f"<{self.collateralID}|{self.name}>"

class Guarantor(db.Model, CRUDMixin):
    id=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberID=db.Column(db.String(8),db.ForeignKey('member.id'),nullable=False)
    loanID=db.Column(db.String(8),db.ForeignKey('loan.id'),nullable=False)
    status=db.Column(db.String(40),default="UNAPPROVED")
    staffID=db.Column(db.String(8),db.ForeignKey('staff.id'),nullable=False)

    def __repr__(self):
        return f"<{self.guarantorID}|{self.memberID}>"

class LoanCategory(db.Model, CRUDMixin):
    id=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    name=db.Column(db.String(50),nullable=False)
    min_shares=db.Column(db.Integer,nullable=False)
    max_amount=db.Column(db.Integer,nullable=False)
    repayment_duration=db.Column(db.Integer,nullable=False)
    qualification_duration=db.Column(db.Integer,nullable=False)
    interest_rate=db.Column(db.Float,nullable=False)
    loans=db.relationship('Loan', backref='loan_category', lazy=True)

    def __repr__(self):
        return f"<{self.id}|{self.name}>"

class OTP(db.Model, CRUDMixin):
    id=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberID=db.Column(db.String(8),db.ForeignKey('member.id'),nullable=False)
    password=db.Column(db.String(4),nullable=False)
    status=db.Column(db.String(40),default="UNUSED")
    date_created=db.Column(db.DateTime,default=datetime.now,nullable=False)

    def __repr__(self):
        return f"<{self.otpID}|{self.password}>"

class Loan(db.Model, CRUDMixin):
    id=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberID=db.Column(db.String(8),db.ForeignKey('member.id'),nullable=False)
    loan_categoryID=db.Column(db.String(8),db.ForeignKey('loan_category.id'),nullable=False)
    staffID=db.Column(db.String(8),db.ForeignKey('staff.id'),nullable=True)
    amount=db.Column(db.Integer,nullable=False)
    start_date=db.Column(db.Date,nullable=True)
    end_date=db.Column(db.Date,nullable=True)
    status=db.Column(db.String(40),default="UNAPPROVED")
    date_created=db.Column(db.DateTime,default=datetime.now,nullable=False)
    guarantors=db.relationship('Guarantor', backref='loan_guarantor', lazy=True)
    repayments=db.relationship('Repayment', backref='loan_repayment', lazy=True)
    collaterals=db.relationship('Collateral', backref='loan_collaterals', lazy=True)
    transactionID=db.Column(db.String(8),db.ForeignKey('transaction.id'),nullable=True)

    def __repr__(self):
        return f"<{self.id}|{self.amount}>"

class Transaction(db.Model, CRUDMixin):
    id=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    phone_number=db.Column(db.String(12),nullable=False)
    transaction_code=db.Column(db.String(40),nullable=False)
    amount=db.Column(db.Integer,nullable=False)
    date_created=db.Column(db.DateTime,default=datetime.now,nullable=False)
    reason=db.Column(db.String(40),nullable=True)
    repayments=db.relationship('Repayment', backref='repayment_transaction', lazy=True)
    deposits=db.relationship('Deposit', backref='deposit_transaction', lazy=True)
    loans=db.relationship('Loan', backref='loan_transaction', lazy=True)

    def __repr__(self):
        return f"<{self.transactionID}|{self.amount}>"


class Repayment(db.Model, CRUDMixin):
    id=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberID=db.Column(db.String(8),db.ForeignKey('member.id'),nullable=False)
    loanID=db.Column(db.String(8),db.ForeignKey('loan.id'),nullable=False)
    transactionID=db.Column(db.String(8),db.ForeignKey('transaction.id'),nullable=False)
    amount=db.Column(db.Integer,nullable=False)
    date_created=db.Column(db.DateTime,default=datetime.now,nullable=False)
    CheckoutRequestID=db.Column(db.String(30),nullable=True)

    def __repr__(self):
        return f"<{self.repaymentID}|{self.amount}>"
