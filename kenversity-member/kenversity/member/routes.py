from flask import Blueprint, render_template, flash, redirect, url_for, request,current_app,jsonify
from kenversity import db, bcrypt, mail
from .forms import (LoginForm,MemberRegistrationForm,MemberDataForm,MemberRegPayForm,MakeDepositForm,
                    ApplyLoanForm,SearchGuatantorForm,AddCollateralForm,MemberBioDataForm,MemberEmplDataForm,
                    MakeRepaymentForm,PasswordResetForm,ResetRequestForm)
from .utils import save_picture,save_file,simulate_pay,add_nums,get_loan_No,get_repayment_No,send_reset_email
from kenversity.models import Member, Deposit,Transaction,LoanCategory,Loan,Guarantor,Collateral,Repayment
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import json
from flask_weasyprint import HTML, render_pdf
from datetime import datetime,date
REGISTRATION_FEE_AMOUNT=1

member = Blueprint('member', __name__)

def get_loan_category():
    return LoanCategory.query.all()


def get_loan_category_pk(obj):
    return str(obj)

def get_loan():
    return Loan.query.all()


def get_loan_pk(obj):
    return str(obj)
@member.route('/member')
@login_required
def dashboard():
    total_shares=0
    deps=Deposit.query.filter_by(memberID=current_user.id).all()
    for dep in deps:
        if dep.amount:
            total_shares+=dep.amount

    loans=Loan.query.filter_by(status="DISBURSED").filter_by(memberID=current_user.id).count()
    guarantor_requests = Guarantor.query.filter_by(memberID=current_user.id).filter_by(status="UNCONFIRMED").count()
    pending_loans=Loan.query.filter_by(status="UNAPPROVED").filter_by(memberID=current_user.id).count()
    return render_template('home.html',total_shares=total_shares,guarantor_requests=guarantor_requests,loans=loans,pending_loans=pending_loans)

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

@member.route('/member/reset-request', methods=["POST", "GET"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('member.dashboard'))
    form = ResetRequestForm()
    if form.validate_on_submit():
        member = Member.query.filter_by(email=form.email.data).first()
        send_reset_email(member)
        flash("An email has been sent to your email with instructions to reset your password", 'info')
        return redirect(url_for('member.login'))
    return render_template('reset_request.html', form=form)


@member.route('/member/reset_password/<token>', methods=['POST', 'GET'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('member.dashboard'))
    member = Member.verify_reset_token(token)
    if member is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('member.reset_request'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        member.password = password
        db.session.commit()
        flash(f'Your password has been updated. You can now log in', 'success')
        return redirect(url_for('member.login'))
    return render_template("reset_password.html", form=form)

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
                rep=Repayment.query.filter_by(CheckoutRequestID=checkout_requestID).first()
                if dep:
                    transaction=Transaction(transaction_code=transaction_code,phone_number=phone_number,amount=amount,reason="DEP")
                    transaction.save()
                    dep.transactionID=transaction.id
                    dep.amount=amount
                    dep.update()
                elif rep:
                    transaction=Transaction(transaction_code=transaction_code,phone_number=phone_number,amount=amount,reason="REP")
                    transaction.save()
                    loan=Loan.query.get(rep.loanID)
                    remaining_amount = Loan.get_remaining_amount(loan.id)
                    if amount<remaining_amount:
                        rep.transactionID=transaction.id
                        rep.amount=amount
                        rep.update()
                    elif amount ==  remaining_amount:
                        rep.transactionID=transaction.id
                        rep.amount=amount
                        rep.update()
                        loan.status =  "FULFILLED"
                        loan.update()
                    else:
                        extra_amount=amount-remaining_amount
                        rep.transactionID=transaction.id
                        rep.amount=remaining_amount
                        rep.update()
                        loan.status =  "FULFILLED"
                        loan.update()
                        dep=Deposit(memberID=current_user.id,CheckoutRequestID="NONE",transactionID=transaction.id,amount=remaining_amount)
                        dep.save()
                else:
                    transaction=Transaction(transaction_code=transaction_code,phone_number=phone_number,amount=amount,reason="MISC")
                    transaction.save()
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
        loan=Loan(loan_applier=current_user,loanNo=get_loan_No(),loan_categoryID=loan_cat,amount=loan_amount)
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
    members=Member.query.filter_by(first_name=name).filter_by(status="ACTIVE").filter(Member.id != current_user.id).all()
    members.extend(Member.query.filter_by(last_name=name).filter_by(status="ACTIVE").filter(Member.id != current_user.id).all())
    members.extend(Member.query.filter_by(email=name).filter_by(status="ACTIVE").filter(Member.id != current_user.id).all())
    members.extend(Member.query.filter_by(phone_number=name).filter_by(status="ACTIVE").filter(Member.id != current_user.id).all())
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
    return render_template("add_guarantors.html",form=form,guarantors=guarantors,loan_id=loan_id)

@member.route('/member/guarantors/<loan_id>/<guarantor_id>/remove', methods=["POST", "GET"])
@login_required
def remove_guarantor(loan_id,guarantor_id):
    guarantor=Guarantor.query.get_or_404(guarantor_id)
    if guarantor.status == "APPROVED":
        flash("Cannot delete an approved Guarantor","danger")
        return redirect(url_for('member.add_collateral',loan_id=loan_id))
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
    if collateral.status == "APPROVED":
        flash("Cannot delete an approved Collateral","danger")
        return redirect(url_for('member.add_collateral',loan_id=loan_id))
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


@member.route('/member/loans/view', methods=["POST", "GET"])
@login_required
def view_loans():
    loans=Loan.query.filter_by(memberID=current_user.id).filter(Loan.status!="DISBURSED").order_by(Loan.date_created.desc()).all()
    loans=add_nums(loans)
    return render_template("view_loans.html",loans=loans)

@member.route('/member/disbursed-loans/view', methods=["POST", "GET"])
@login_required
def view_disbursed_loans():
    loans=Loan.query.filter_by(memberID=current_user.id).filter_by(status="DISBURSED").order_by(Loan.date_created.desc()).all()
    loans.extend(Loan.query.filter_by(memberID=current_user.id).filter_by(status="FULFILLED").order_by(Loan.date_created.desc()).all())
    loans=add_nums(loans)
    today=date.today()
    return render_template("view_disbursed_loans.html",loans=loans,Loan=Loan,today=today)

@member.route('/member/transactions/<member_id>/download', methods=["POST", "GET"])
@login_required
def download_transactions(member_id):
    member=Member.query.get(member_id)
    transactions=Transaction.query.filter_by(phone_number=member.phone_number).order_by(Transaction.date_created.desc()).all()
    i=1
    ts={}
    for transaction in transactions:
        ts[i]=transaction
        i+=1
    html=render_template('table.html',ts=ts,member=member,date=datetime.today())
    return render_pdf(HTML(string=html))

@member.route('/member/deposits/<member_id>/download', methods=["POST", "GET"])
@login_required
def download_deposits(member_id):
    member=Member.query.get(member_id)
    transactions=Transaction.query.filter_by(phone_number=member.phone_number).filter_by(reason="DEP").order_by(Transaction.date_created.desc()).all()
    i=1
    ts={}
    for transaction in transactions:
        ts[i]=transaction
        i+=1
    html=render_template('table.html',ts=ts,member=member,date=datetime.today(),deposits=True)
    return render_pdf(HTML(string=html))

@member.route('/member/profile', methods=["POST", "GET"])
@login_required
def member_profile():
    register_form=MemberRegistrationForm()
    docs_form=MemberDataForm()
    biodata_form=MemberBioDataForm()
    empl_form=MemberEmplDataForm()

    if register_form.validate_on_submit():
        current_user.first_name=register_form.first_name.data
        current_user.last_name=register_form.last_name.data
        current_user.email=register_form.email.data
        current_user.phone_number=register_form.phone.data
        current_user.national_id=register_form.national_id.data
        db.session.commit()
        flash("Successfully Updated Registration Data","success")
        return redirect(url_for('member.member_profile'))

    if biodata_form.validate_on_submit():
        current_user.dob=biodata_form.dob.data
        current_user.gender=biodata_form.gender.data
        current_user.marital_status=biodata_form.marital_status.data
        current_user.number_of_dependants=biodata_form.number_of_dependants.data
        current_user.address=biodata_form.address.data
        current_user.town=biodata_form.town.data
        current_user.estate=biodata_form.estate.data
        current_user.street=biodata_form.street.data
        current_user.house_number=biodata_form.house_number.data
        current_user.house_ownership=biodata_form.house_ownership.data
        db.session.commit()
        flash("Successfully Updated Bio Data","success")
        return redirect(url_for('member.member_profile'))

    if empl_form.validate_on_submit():
        if empl_form.employment_status.data == "Employed":
            current_user.employment_status=empl_form.employment_status.data
            current_user.employer_name=empl_form.name.data
            current_user.employer_address=empl_form.address.data
            current_user.employer_phone=empl_form.phone.data
            current_user.employment_terms=empl_form.employment_terms.data
            current_user.retirement_date=empl_form.retirement_date.data
        if empl_form.employment_status.data == "Self-Employed":
            current_user.employment_status=empl_form.employment_status.data
            current_user.business_type=empl_form.business_type.data
            current_user.years_of_operation=empl_form.years_of_operation.data
            current_user.business_income=empl_form.business_income.data
        db.session.commit()
        flash("Successfully Updated Employment Data","success")
        return redirect(url_for('member.member_profile'))

    register_form.first_name.data=current_user.first_name
    register_form.last_name.data=current_user.last_name
    register_form.email.data=current_user.email
    register_form.phone.data=current_user.phone_number
    register_form.national_id.data=current_user.national_id

    biodata_form.dob.data=current_user.dob
    biodata_form.gender.data=current_user.gender
    biodata_form.marital_status.data=current_user.marital_status
    biodata_form.number_of_dependants.data=current_user.number_of_dependants
    biodata_form.address.data=current_user.address
    biodata_form.town.data=current_user.town
    biodata_form.estate.data=current_user.estate
    biodata_form.street.data=current_user.street
    biodata_form.house_number.data=current_user.house_number
    biodata_form.house_ownership.data=current_user.house_ownership

    empl_form.employment_status.data=current_user.employment_status
    empl_form.name.data=current_user.employer_name
    empl_form.address.data=current_user.employer_address
    empl_form.phone.data=current_user.employer_phone
    empl_form.retirement_date.data=current_user.retirement_date
    empl_form.business_type.data=current_user.business_type
    empl_form.years_of_operation.data=current_user.years_of_operation
    empl_form.business_income.data=current_user.business_income
    empl_form.employment_terms.data=current_user.employment_terms

    return render_template('member_profile.html',register_form=register_form,docs_form=docs_form,biodata_form=biodata_form,empl_form=empl_form)

@member.route('/member/repayment/make', methods=["POST", "GET"])
@login_required
def make_repayment():
    form=MakeRepaymentForm()
    form.loan.get_pk = get_loan_pk
    form.loan.query_factory = get_loan
    if form.validate_on_submit():
        loan_no=str(form.loan.data)
        amount=form.amount.data
        loan=Loan.query.filter_by(loanNo=loan_no).first()
        resp=simulate_pay(current_user.phone_number,amount)
        if resp:
            rep=Repayment(memberID=current_user.id,repaymentNo=get_repayment_No(),loanID=loan.id,CheckoutRequestID=resp["CheckoutRequestID"])
            rep.save()
            flash("You will be probpted to authorise the transaction on your phone","info")
            return redirect(url_for('member.dashboard'))

    return render_template("make_repayment.html",form=form)

@member.route('/member/repayments/view', methods=["POST", "GET"])
@login_required
def view_repayments():
    repayments=Repayment.query.all()
    repayments=add_nums(repayments)
    return render_template("view_repayments.html",repayments=repayments)

@member.route('/member/<loan_id>/repayments/view', methods=["POST", "GET"])
@login_required
def view_loan_repayments(loan_id):
    repayments=Repayment.query.filter_by(loanID=loan_id).all()
    loan=Loan.query.get_or_404(loan_id)
    amount=loan.amount
    new_dict={}
    i = 1
    for repayment in repayments:
        new_dict[i]= [repayment,amount-repayment.amount]
        amount-=repayment.amount
        i+=1

    repayments={k:v for k,v in sorted(new_dict.items(),key=lambda x: (x[1][0].date_created),reverse=True)}

    repayments=add_nums(repayments.values())
    return render_template("view_loan_repayments.html",repayments=repayments,loan=loan)

@member.route('/member/<loan_id>/repayments/download',methods=["POST","GET"])
@login_required
def download_loan_repayments(loan_id):
    repayments=Repayment.query.filter_by(loanID=loan_id).all()
    loan=Loan.query.get_or_404(loan_id)
    amount=loan.amount
    new_dict={}
    i = 1
    for repayment in repayments:
        new_dict[i]= [repayment,amount-repayment.amount]
        amount-=repayment.amount
        i+=1
    repayments=new_dict
    html = render_template("download_loan_repayment.html",loan=loan,repayments=repayments,date=datetime.today(),title=f"Kenversity_Sacco_{loan.loanNo}_repayments.pdf")
    return render_pdf(HTML(string=html))
