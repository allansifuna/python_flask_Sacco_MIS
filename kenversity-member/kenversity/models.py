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

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

@lm.user_loader
def load_member(id):
    return Member.query.get(str(id))


def id_unique():
    return secrets.token_hex(8)

class Member(db.Model,UserMixin, CRUDMixin):
    id = db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberNo=db.Column(db.String(7),nullable=True)
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
    dob=db.Column(db.Date,nullable=True)
    gender=db.Column(db.String(10),nullable=True)
    marital_status=db.Column(db.String(20),nullable=True)
    number_of_dependants=db.Column(db.Integer,nullable=True)
    address=db.Column(db.String(50),nullable=True)
    town=db.Column(db.String(50),nullable=True)
    estate=db.Column(db.String(50),nullable=True)
    street=db.Column(db.String(50),nullable=True)
    house_number=db.Column(db.String(50),nullable=True)
    house_ownership=db.Column(db.String(50),nullable=True)
    employment_status=db.Column(db.String(50),nullable=True)
    employer_name=db.Column(db.String(50),nullable=True)
    employer_address=db.Column(db.String(50),nullable=True)
    employer_phone=db.Column(db.String(50),nullable=True)
    retirement_date=db.Column(db.Date,nullable=True)
    business_type=db.Column(db.String(50),nullable=True)
    years_of_operation=db.Column(db.Integer,nullable=True)
    business_income=db.Column(db.Integer,nullable=True)
    employment_terms=db.Column(db.String(50),nullable=True)
    staffID=db.Column(db.String(8),db.ForeignKey('staff.id'),nullable=True)
    deposits = db.relationship('Deposit', backref='member', lazy=True)
    collaterals = db.relationship('Collateral', backref='member', lazy=True)
    guarantors=db.relationship('Guarantor', backref='applicant', lazy=True)
    loans=db.relationship('Loan', backref='loan_applier', lazy=True)
    repayments=db.relationship('Repayment', backref='member', lazy=True)

    def __repr__(self):
        return f"{self.memberNo}-<{self.first_name}|{self.last_name}>"

    def get_reset_token(self, expires_sec=18000):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'memberID': self.id}).decode('utf-8')

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
        return s.dumps({'staffID': self.staffID}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            staffID = s.loads(token)['staffID']
        except Exception as e:
            return None
        return Staff.query.get(staffID)

    @staticmethod
    def get_members_approved(staff_id):
        members=Member.query.filter_by(staffID=staff_id).count()
        return members

    @staticmethod
    def get_loans_approved(staff_id):
        loans=Loan.query.filter_by(staffID=staff_id).count()
        return loans

    @staticmethod
    def get_pending_loans(staff_id):
        loans=Loan.query.filter_by(staffID=staff_id).filter(Loan.status!="DISBURSED").filter(Loan.status!="FULFILLED").count()
        return loans

class Deposit(db.Model, CRUDMixin):
    id = db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    memberID=db.Column(db.String(8), db.ForeignKey('member.id'),nullable=False)
    transactionID=db.Column(db.String(8),db.ForeignKey('transaction.id'),nullable=True)
    CheckoutRequestID=db.Column(db.String(30),nullable=True)
    deposit_date=db.Column(db.DateTime,default=datetime.now,nullable=False)
    amount=db.Column(db.Integer,nullable=True)


    def __repr__(self):
        return f"<{self.depositID}|{self.amount}>"

class Collateral(db.Model, CRUDMixin):
    id= db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    collateralNo=db.Column(db.String(7),nullable=True)
    memberID=db.Column(db.String(8),db.ForeignKey('member.id'),nullable=False)
    loanID=db.Column(db.String(8),db.ForeignKey('loan.id'),nullable=False)
    name=db.Column(db.String(50),nullable=False)
    description=db.Column(db.String(255),nullable=False)
    value=db.Column(db.Integer,nullable=False)
    status=db.Column(db.String(40),default="UNAPPROVED")
    staffID=db.Column(db.String(8),db.ForeignKey('staff.id'),nullable=True)

    def __repr__(self):
        return f"<{self.collateralID}|{self.name}>"

class Guarantor(db.Model, CRUDMixin):
    id=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    guarantorNo=db.Column(db.String(7),nullable=True)
    memberID=db.Column(db.String(8),db.ForeignKey('member.id'),nullable=False)
    loanID=db.Column(db.String(8),db.ForeignKey('loan.id'),nullable=False)
    status=db.Column(db.String(40),default="UNCONFIRMED")
    staffID=db.Column(db.String(8),db.ForeignKey('staff.id'),nullable=True)

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
    loans=db.relationship('Loan', backref='loan_cat', lazy=True)

    def __repr__(self):
        return f"{self.id}"

class Loan(db.Model, CRUDMixin):
    id=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    loanNo=db.Column(db.String(7),nullable=True)
    memberID=db.Column(db.String(8),db.ForeignKey('member.id'),nullable=False)
    loan_categoryID=db.Column(db.String(8),db.ForeignKey('loan_category.id'),nullable=False)
    staffID=db.Column(db.String(8),db.ForeignKey('staff.id'),nullable=True)
    amount=db.Column(db.Integer,nullable=False)
    start_date=db.Column(db.Date,nullable=True)
    end_date=db.Column(db.Date,nullable=True)
    status=db.Column(db.String(40),default="UNAPPROVED")
    profile_status=db.Column(db.String(40),default="UNAPPROVED")
    collateral_status=db.Column(db.String(40),default="UNAPPROVED")
    guarantor_status=db.Column(db.String(40),default="UNAPPROVED")
    loan_reason=db.Column(db.String(255))
    supporting_documents= db.Column(db.String(40))
    rejection_reason = db.Column(db.String(255))
    date_created=db.Column(db.DateTime,default=datetime.now,nullable=False)
    guarantors=db.relationship('Guarantor', backref='loan_guarantor', lazy=True)
    repayments=db.relationship('Repayment', backref='loan_repayment', lazy=True)
    collaterals=db.relationship('Collateral', backref='loan_collaterals', lazy=True)
    transactionID=db.Column(db.String(8),db.ForeignKey('transaction.id'),nullable=True)

    def __repr__(self):
        return f"{self.loanNo}"

    @staticmethod
    def get_remaining_amount(loan_id):
        amount=0
        loan=Loan.query.get(loan_id)
        repayments=Repayment.query.filter_by(loanID=loan_id).all()
        for repayment in repayments:
            amount+=repayment.amount
        return loan.amount - amount

class Transaction(db.Model, CRUDMixin):
    id=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    transactionNo=db.Column(db.String(9),nullable=True)
    phone_number=db.Column(db.String(12),nullable=False)
    transaction_code=db.Column(db.String(40),nullable=False)
    amount=db.Column(db.Integer,nullable=False)
    date_created=db.Column(db.DateTime,default=datetime.now,nullable=False)
    reason=db.Column(db.String(40),nullable=True)
    repayments=db.relationship('Repayment', backref='repayment_transaction', lazy=True)
    deposits=db.relationship('Deposit', backref='deposit_transaction', lazy=True)
    loans=db.relationship('Loan', backref='loan_transaction', lazy=True)

    def __repr__(self):
        return f"<{self.id}|{self.amount}>"


class Repayment(db.Model, CRUDMixin):
    id=db.Column(db.String(8),default=id_unique, unique=True, primary_key=True)
    repaymentNo=db.Column(db.String(7),nullable=True)
    memberID=db.Column(db.String(8),db.ForeignKey('member.id'),nullable=False)
    loanID=db.Column(db.String(8),db.ForeignKey('loan.id'),nullable=False)
    transactionID=db.Column(db.String(8),db.ForeignKey('transaction.id'),nullable=True)
    amount=db.Column(db.Integer,nullable=False)
    date_created=db.Column(db.DateTime,default=datetime.now,nullable=False)
    CheckoutRequestID=db.Column(db.String(30),nullable=True)

    def __repr__(self):
        return f"<{self.id}|{self.amount}>"
