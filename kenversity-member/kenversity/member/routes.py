from flask import Blueprint, render_template, flash, redirect, url_for, request,current_app
from kenversity import db, bcrypt, mail
from .forms import LoginForm,MemberRegistrationForm,MemberDataForm,MemberRegPayForm
from .utils import save_picture,save_file,simulate_pay
from kenversity.models import Member, Deposit,Transaction
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import json
REGISTRATION_FEE_AMOUNT=1

member = Blueprint('member', __name__)

@member.route('/member')
@login_required
def dashboard():
    return render_template('home.html')

@member.route('/member/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('member.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        member = Member.query.filter_by(email=email).first()
        if member and member.password is not None:
            if bcrypt.check_password_hash(member.password, password):
                login_user(member, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('member.dashboard'))
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
    print(resp)
    resultCode=resp["Body"]["stkCallback"]["ResultCode"]
    print(resultCode)
    if resultCode == 0:
        phone_number=resp["Body"]["stkCallback"]["CallbackMetadata"]["Item"][4]["Value"]
        amount=resp["Body"]["stkCallback"]["CallbackMetadata"]["Item"][0]["Value"]
        transaction_code=resp["Body"]["stkCallback"]["CallbackMetadata"]["Item"][1]["Value"]
        member=Member.query.filter_by(phone_number=phone_number).first()
        if member:
            if not member.memberNo:
                transaction=Transaction(transaction_code=transaction_code,phone_number=phone_number,amount=amount,reason="REG")
                transaction.save()
            #email the person that their transaction was successful
        else:
            transaction=Transaction(transaction_code=transaction_code,phone_number=phone_number,amount=amount,reason="MISC")
            transaction.save()

    else:
        #TODO
        #text the person that their transaction was not prosessed
        print("I Was Here")
    return {"status":"success"}
