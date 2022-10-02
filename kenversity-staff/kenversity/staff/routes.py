from flask import Blueprint, render_template, flash, redirect, url_for, request
from kenversity import db, bcrypt, mail
from .forms import LoginForm
from kenversity.models import Staff
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
staff = Blueprint('staff', __name__)

@staff.route('/staff')
@login_required
def dashboard():
    return render_template('home.html')

@staff.route('/staff/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('staff.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user and user.password is not None:
            if bcrypt.check_password_hash(user.password, password):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('staff.dashboard'))
            else:
                flash("Wrong email or Password!!", "danger")
        else:
            flash("Wrong email or Password!!", "danger")
    return render_template('login.html', form=form)


@staff.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('staff.login'))
