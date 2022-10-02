from flask import Blueprint, render_template, flash, redirect, url_for, request
from kenversity import db, bcrypt, mail
from .forms import LoginForm,MemberRegistrationForm,MemberDataForm
from kenversity.models import Member, Deposit
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
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
        user = User.query.filter_by(email=email).first()
        if user and user.password is not None:
            if bcrypt.check_password_hash(user.password, password):
                login_user(user, remember=form.remember.data)
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
            return redirect(url_for('member.register',stage="user_data"))
    elif stage == "user_data":
        form=MemberDataForm()
        if form.validate_on_submit():
            return redirect(url_for('member.register',stage="payment"))
    elif stage == "payment":
        pass

    return render_template('register.html',stage=stage)
