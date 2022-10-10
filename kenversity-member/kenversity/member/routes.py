from flask import Blueprint, render_template, flash, redirect, url_for, request,current_app,jsonify
from kenversity import db, bcrypt, mail
from .forms import (LoginForm,MemberRegistrationForm,MemberDataForm,MemberRegPayForm,MakeDepositForm,
                    ApplyLoanForm,SearchGuatantorForm,AddCollateralForm)
from .utils import save_picture,save_file,simulate_pay
from kenversity.models import Member, Deposit,Transaction,LoanCategory,Loan,Guarantor,Collateral
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import json
REGISTRATION_FEE_AMOUNT=1

member = Blueprint('member', __name__)

def get_loan_category():
    return LoanCategory.query.all()


def get_loan_category_pk(obj):
    return str(obj)

@member.route('/member')
@login_required
def dashboard():
    total_shares=0
    deps=Deposit.query.filter_by(memberID=current_user.id).all()
    for dep in deps:
        if dep.amount:
            total_shares+=dep.amount
    guarantor_requests = Guarantor.query.filter_by(memberID=current_user.id).filter_by(status="UNCONFIRMED").count()
    return render_template('home.html',total_shares=total_shares,guarantor_requests=guarantor_requests)

@member.route('/member/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('member.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        member = Member.query.filter_by(email=email).first()
        if member and member.password is not None and member.status != "DEACTIVATED":
            if bcrypt.check_password_hash(member.password, password):
                if member.status == "ACTIVE":
                    login_user(member, remember=form.remember.data)
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('member.dashboard'))
                elif member.status == "DISAPPROVED":
                    flash("Your Membership application was disapproved. Please check your email for the reason.", "danger")
                elif member.status == "INACTIVE":
                    flash("Your Membership application has not been approved yet. The Approval will be done within 24hrs. Please be patient.", "danger")
            else:
                flash("Wrong email or Password!!", "danger")
        else:
            flash("Wrong email or Password!!", "danger")
    return render_template('login.html', form=form)


@member.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('member.login'))

@member.route('/member/register', methods=["POST", "GET"])
def register():
    stage=request.args.get("stage")
    if stage is None:
        form=MemberRegistrationForm()
        if form.validate_on_submit():
            fname=form.first_name.data
            lname=form.last_name.data
            email=form.email.data
            phone=form.phone.data
            nat_id=form.national_id.data
            passw=form.password.data
            password=bcrypt.generate_password_hash(passw).decode("utf-8")
            member=Member(first_name=fname,last_name=lname,email=email,phone_number=phone,national_id=nat_id,password=password)
            member.save()
            return redirect(url_for('member.register',stage="user_data",member=member.id))
    elif stage == "user_data":
        memberID=request.args.get("member")
        member=Member.query.get_or_404(memberID)
        if member.status == "DEACTIVATED" or member.status == "ACTIVE":
            return redirect(url_for('member.login'))
        form=MemberDataForm()
        if form.validate_on_submit():
            id_front=save_picture(form.id_front.data)
            id_back=save_picture(form.id_back.data)
            kra_pin=save_file(form.kra_pin.data)
            photo=save_picture(form.photo.data)
            member=Member.query.get(memberID)
            member.id_front=id_front
            member.id_back=id_back
            member.kra_pin=kra_pin
            member.photo=photo
            member.status="INACTIVE"
            member.update()
            return redirect(url_for('member.register',stage="payment",member=member.id))
    elif stage == "payment":
        form=MemberRegPayForm()
        memberID=request.args.get("member")
        member=Member.query.get(memberID)
        if form.validate_on_submit():
            phone=form.phone.data
            resp=simulate_pay(phone,REGISTRATION_FEE_AMOUNT)
            if resp:
                flash("Once payment is successful, you will be verified by our staff  with in 12hrs and you will be able to Login","info")
                return redirect(url_for("member.login"))
            flash("Payment simulation failed. Pleas try again!","danger")
        form.phone.data=member.phone_number

    return render_template('register.html',stage=stage,form=form)

@member.route('/callback_url', methods=["POST"])
def callback_url():
    request_data = request.data
    decoded = request_data.decode()
    resp=json.loads(decoded)
    resultCode=resp["Body"]["stkCallback"]["ResultCode"]
    if resultCode == 0:
        phone_number=resp["Body"]["stkCallback"]["CallbackMetadata"]["Item"][4]["Value"]
        amount=resp["Body"]["stkCallback"]["CallbackMetadata"]["Item"][0]["Value"]
        transaction_code=resp["Body"]["stkCallback"]["CallbackMetadata"]["Item"][1]["Value"]
        checkout_requestID=resp["Body"]["stkCallback"]["CheckoutRequestID"]
        member=Member.query.filter_by(phone_number=phone_number).first()
        if member:
            if not member.memberNo:
                transaction=Transaction(transaction_code=transaction_code,phone_number=phone_number,amount=amount,reason="REG")
                transaction.save()
                member.status="INACTIVE"
                member.update()
            elif member.memberNo:
                dep=Deposit.query.filter_by(CheckoutRequestID=checkout_requestID).first()
                if dep:
                    transaction=Transaction(transaction_code=transaction_code,phone_number=phone_number,amount=amount,reason="DEP")
                    transaction.save()
                    dep.transactionID=transaction.id
                    dep.amount=amount
                    dep.update()

            #email the person that their transaction was successful
        else:
            transaction=Transaction(transaction_code=transaction_code,phone_number=phone_number,amount=amount,reason="MISC")
            transaction.save()

    else:
        checkout_requestID=resp["Body"]["stkCallback"]["CheckoutRequestID"]
        dep=Deposit.query.filter_by(CheckoutRequestID=checkout_requestID).first()
        if dep:
            dep.delete()
        #TODO
        #text the person that their transaction was not prosessed
        print("I Was Here")
    return {"status":"success"}

@member.route('/member/make/deposit', methods=["POST", "GET"])
@login_required
def make_deposit():
    form = MakeDepositForm()
    if form.validate_on_submit():
        phone=form.phone.data
        amount=form.amount.data
        resp=simulate_pay(phone,REGISTRATION_FEE_AMOUNT)
        if resp:
            dep=Deposit(memberID=current_user.id,CheckoutRequestID=resp["CheckoutRequestID"])
            dep.save()
            flash(f"A payment request has been sent to youe phone.","success")
            return redirect(url_for("member.dashboard"))
        flash("Payment simulation failed. Pleas try again!","danger")
    form.phone.data=current_user.phone_number
    return render_template("make_deposit.html",form=form)

@member.route('/member/view/deposits', methods=["POST", "GET"])
@login_required
def view_deposits():
    deposits=Deposit.query.filter_by(memberID=current_user.id).filter(Deposit.amount!=None).all()
    i=1
    ds={}
    for deposit in deposits:
        ds[i]=deposit
        i+=1
    return render_template("member_deposits.html",ds=ds)

@member.route('/member/view/transactions', methods=["POST", "GET"])
@login_required
def view_transactions():
    transactions=Transaction.query.filter_by(phone_number=current_user.phone_number).order_by(Transaction.date_created.desc()).all()
    i=1
    ts={}
    for transaction in transactions:
        ts[i]=transaction
        i+=1
    return render_template("member_transactions.html",ts=ts)

@member.route('/member/loan/apply', methods=["POST", "GET"])
@login_required
def apply_loan():
    form=ApplyLoanForm()
    form.loan_category.get_pk = get_loan_category_pk
    form.loan_category.query_factory = get_loan_category
    if form.validate_on_submit():
        loan_cat=str(form.loan_category.data)
        loan_amount = int(form.loan_amount.data)
        loan=Loan(loan_applier=current_user,loan_categoryID=loan_cat,amount=loan_amount)
        loan.save()
        flash(f"Loan application has been successfully submitted","success")
        return redirect(url_for('member.add_guarantor',loan_id=loan.id))
    return render_template("apply_loan.html",form=form)

@member.route('/get/lc/<loan_cat_id>', methods=["POST", "GET"])
@login_required
def get_loan_cat(loan_cat_id):
    lc = LoanCategory.query.get(loan_cat_id)
    data={}
    if lc:
        data["min_shares"] = lc.min_shares
        data["max_amount"] = lc.max_amount
        data["repayment_duration"]=lc.repayment_duration
        data["interest_rate"] = lc.interest_rate
    return jsonify(data)

@member.route('/get/member/<name>', methods=["POST", "GET"])
@login_required
def get_member(name):
    members=Member.query.filter_by(first_name=name).filter(Member.id != current_user.id).all()
    members.extend(Member.query.filter_by(last_name=name).filter(Member.id != current_user.id).all())
    members.extend(Member.query.filter_by(email=name).filter(Member.id != current_user.id).all())
    members.extend(Member.query.filter_by(phone_number=name).filter(Member.id != current_user.id).all())
    data=[]
    for member in members:
        datas={}
        datas["id"]=member.id
        datas["name"]= f"{member.first_name} {member.last_name}"
        data.append(datas)
    return jsonify(data)

@member.route('/member/guarantors/<loan_id>/add', methods=["POST", "GET"])
@login_required
def add_guarantor(loan_id):
    form = SearchGuatantorForm()
    guarantors=Guarantor.query.filter_by(loanID=loan_id).all()
    members=[]
    for guarantor in guarantors:
        members.append(Member.query.get(guarantor.memberID))
    if request.method == "POST":
        guarantor=form.guarantor.data
        if guarantor == "":
            flash("Please Select a Guarantor before Adding.","danger")
            return redirect(url_for('member.add_guarantor',loan_id=loan_id))
        has_g=Guarantor.query.filter_by(memberID=guarantor).filter_by(loanID=loan_id).first()
        if has_g:
            flash("Guarantor Already exist. Please select another.","danger")
            return redirect(url_for('member.add_guarantor',loan_id=loan_id))
        g=Guarantor(memberID=guarantor,loanID=loan_id)
        g.save()
        flash("Added a guarantor","success")
        return redirect(url_for('member.add_guarantor',loan_id=loan_id))
    form.name.data=""
    return render_template("add_guarantors.html",form=form,members=members,loan_id=loan_id)

@member.route('/member/guarantors/<loan_id>/<guarantor_id>/remove', methods=["POST", "GET"])
@login_required
def remove_guarantor(loan_id,guarantor_id):
    guarantor=Guarantor.query.get_or_404(guarantor_id)
    guarantor.delete()
    flash("Successfully Deleted A Guarantor","success")
    return redirect(url_for('member.add_guarantor',loan_id=loan_id))

@member.route('/member/collateral/<loan_id>/add', methods=["POST", "GET"])
@login_required
def add_collateral(loan_id):
    form = AddCollateralForm()
    cols=Collateral.query.filter_by(loanID=loan_id).all()
    collaterals={}
    i=1
    for col in cols:
        collaterals[i]=col
        i+=1
    if form.validate_on_submit():
        name=form.name.data
        value=form.value.data
        description=form.description.data
        col=Collateral(memberID=current_user.id,loanID=loan_id,name=name,value=value,description=description)
        col.save()
        flash("Added a Collateral","success")
        return redirect(url_for('member.add_collateral',loan_id=loan_id))
    return render_template("add_collateral.html",form=form,collaterals=collaterals,loan_id=loan_id)

@member.route('/member/collateral/<loan_id>/<collateral_id>/remove', methods=["POST", "GET"])
@login_required
def remove_collateral(loan_id,collateral_id):
    collateral=Collateral.query.get_or_404(collateral_id)
    collateral.delete()
    flash(" Successfully Deleted A Collateral","success")
    return redirect(url_for('member.add_collateral',loan_id=loan_id))

@member.route('/member/guarantor/confirm', methods=["POST", "GET"])
@login_required
def confirm_guarantor_request():
    reqs_=Guarantor.query.filter_by(memberID=current_user.id).filter_by(status="UNCONFIRMED").all()
    reqs={}
    i=1
    for req in reqs_:
        reqs[i]=req
        i+=1
    return render_template("confirm_g_reqs.html",reqs=reqs)

@member.route('/member/guarantor/confirm/<guarantor_id>/<verdict>', methods=["POST", "GET"])
@login_required
def confirm_request(guarantor_id,verdict):
    req=Guarantor.query.get_or_404(guarantor_id)
    if verdict == "CONFIRMED":
        req.status="UNAPPROVED"
        req.update()
    elif verdict ==  "DECLINED":
        req.status="DECLINED"
        req.update()
    else:
        flash("Wrong verdict!!","warning")
        return redirect(url_for('member.confirm_guarantor_request'))
    flash("You have successfuly updated the guarantor request status","success")
    return redirect(url_for('member.confirm_guarantor_request'))

