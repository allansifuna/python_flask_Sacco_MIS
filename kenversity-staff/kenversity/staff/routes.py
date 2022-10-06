from flask import Blueprint, render_template, flash, redirect, url_for, request
from kenversity import db, bcrypt, mail
from .forms import LoginForm,AddLoanCategoriesForm,AddStaffForm,SetPasswordForm
from .utils import send_set_password_email
from kenversity.models import Staff,Member,LoanCategory
from flask_login import login_user, current_user, logout_user, login_required
import secrets
staff = Blueprint('staff', __name__)

@staff.route('/staff')
@login_required
def dashboard():
    pending_member_approvals=len(Member.query.filter_by(memberNo=None).all())
    return render_template('home.html',pending_member_approvals=pending_member_approvals)

@staff.route('/staff/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('staff.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        staff = Staff.query.filter_by(email=email).first()
        if staff and staff.password is not None:
            if bcrypt.check_password_hash(staff.password, password):
                login_user(staff, remember=form.remember.data)
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

@staff.route('/staff/add/loan-categories',methods=["POST","GET"])
@login_required
def add_loan_categories():
    form=AddLoanCategoriesForm()
    if form.validate_on_submit():
        name=form.name.data
        min_shares=form.min_shares.data
        max_amount=form.max_amount.data
        repayment_duration=form.repayment_duration.data
        qualification_duration=form.qualification_duration.data
        interest_rate=form.interest_rate.data
        loan_category=LoanCategory(name=name,min_shares=min_shares,max_amount=max_amount,repayment_duration=repayment_duration,qualification_duration=qualification_duration,interest_rate=interest_rate)
        loan_category.save()
        flash("Loan Category Successfully Added.","success")
        return redirect(url_for("staff.dashboard"))
    return render_template('loan_categories.html', form=form)

@staff.route('/staff/add/new',methods=["POST","GET"])
@login_required
def add_staff():
    form=AddStaffForm()
    if form.validate_on_submit():
        first_name=form.first_name.data
        last_name=form.last_name.data
        national_id=form.national_id.data
        email=form.email.data
        phone_number=form.phone_number.data
        role=form.role.data
        staff=Staff(first_name=first_name,last_name=first_name,national_id=national_id,status="ACTIVE",email=email,phone_number=phone_number,role=role)
        staff.save()
        send_set_password_email(staff)
        flash("New Staff Successfully Added.","success")
        return redirect(url_for("staff.dashboard"))
    return render_template('add_staff.html', form=form)

@staff.route('/set_password/<token>', methods=['POST', 'GET'])
def set_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('staff.dashboard'))
    staff = Staff.verify_reset_token(token)
    if staff is None:
        flash('That is an invalid or expired token,Please get in touch with the system adminstrator', 'warning')
        return redirect(url_for('staff.login'))
    form = SetPasswordForm()
    if form.validate_on_submit():
        password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        staff.password = password
        db.session.commit()
        flash(f'Your password has been set. You can now log in', 'success')
        return redirect(url_for('staff.login'))
    return render_template("set_password.html", form=form)


@staff.route('/staff/member/approvals',methods=["POST","GET"])
@login_required
def member_approvals():
    members=Member.query.filter_by(memberNo=None).all()
    i=1
    ms={}
    for member in members:
        ms[i]=member
        i+=1
    return render_template("member_approvals.html", ms=ms)
