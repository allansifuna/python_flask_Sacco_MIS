from flask import Blueprint, render_template, flash, redirect, url_for, request
from kenversity import db, bcrypt, mail
from .forms import (LoginForm,AddLoanCategoriesForm,AddStaffForm,SetPasswordForm,ApproveMemberForm,
        DeclineLoanForm,SearchForm,PasswordResetForm,ResetRequestForm,UpdateTicketForm)
from .utils import (send_set_password_email,
                    get_member_No,send_approval_email,
                    send_disapproval_email,
                    add_nums,
                    send_loan_decline_email,
                    send_reset_email,
                    get_deposit_days,
                    send_loan_approval_email,
                    send_loan_disbursement_email)
from kenversity.models import (Staff,
                    Member,
                    LoanCategory,
                    Transaction,
                    Loan,
                    Collateral,
                    Guarantor,
                    Repayment,
                    Ticket,
                    TicketMessage,
                    Deposit)
from flask_login import login_user, current_user, logout_user, login_required
from flask_weasyprint import HTML, render_pdf
import secrets
from datetime import datetime,date
from dateutil.relativedelta import relativedelta
staff = Blueprint('staff', __name__)


@staff.route('/',methods=["POST","GET"])
@staff.route('/staff',methods=["POST","GET"])
@login_required
def dashboard():
    pending_member_approvals=Member.query.filter_by(memberNo=None).count()
    pending_loan_applications=Loan.query.filter_by(staffID=None).count()
    pending_loan_approvals=Loan.query.filter_by(staffID=current_user.id).filter(Loan.status!="DECLINED").filter(Loan.status!="APPROVED").filter(Loan.status!="DISBURSED").filter(Loan.status!="FULFILLED").count()
    open_tickets=Ticket.query.filter_by(status="OPEN").count()
    total_deposits = 0
    if current_user.role == "ADMINSTARTOR":

        all_deps=Deposit.query.all()
        for dep in all_deps:
            total_deposits+=dep.amount
    deposit_days=get_deposit_days()
    loans=[Loan.query.filter_by(status="DISBURSED").count(),Loan.query.filter_by(status="FULFILLED").count(),Loan.query.filter_by(status="DEFAULTED").count()]
    pending_loan_disbursements = Loan.query.filter_by(status="APPROVED").count()
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template('home.html',
                    open_tickets=open_tickets,
                    pending_member_approvals=pending_member_approvals,
                    pending_loan_approvals=pending_loan_approvals,
                    pending_loan_applications=pending_loan_applications,
                    pending_loan_disbursements=pending_loan_disbursements,
                    search=search,
                    total_deposits=total_deposits,
                    deposit_days=deposit_days,
                    loans=loans
                    )

@staff.route('/search/<string:data>', methods=["POST", "GET"])
@login_required
def searches(data):
    members=Member.query.filter_by(first_name=data.capitalize()).filter_by(status="ACTIVE").all()
    members.extend(Member.query.filter_by(last_name=data.capitalize()).filter_by(status="ACTIVE").all())
    members.extend(Member.query.filter_by(memberNo=data).filter_by(status="ACTIVE").all())
    members.extend(Member.query.filter_by(email=data).filter_by(status="ACTIVE").all())
    members.extend(Member.query.filter_by(phone_number=data).filter_by(status="ACTIVE").all())
    members.extend(Member.query.filter_by(first_name=data.capitalize()).filter_by(status="DEACTIVATED").all())
    members.extend(Member.query.filter_by(last_name=data.capitalize()).filter_by(status="DEACTIVATED").all())
    members.extend(Member.query.filter_by(memberNo=data).filter_by(status="DEACTIVATED").all())
    members.extend(Member.query.filter_by(email=data).filter_by(status="DEACTIVATED").all())
    members.extend(Member.query.filter_by(phone_number=data).filter_by(status="DEACTIVATED").all())
    matches=len(members)>0
    found=len(members)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template('search_results.html',members=members,matches=matches,found=found,search=search)
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
                if staff.status != "INACTIVE":
                    if staff.status == "ACTIVE":
                        login_user(staff, remember=form.remember.data)
                        next_page = request.args.get('next')
                        return redirect(next_page) if next_page else redirect(url_for('staff.dashboard'))
                    else:
                        flash("Wrong email or Password!!", "danger")
                else:
                    flash("Your Account is inactive.","danger")
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

@staff.route('/staff/reset-request', methods=["POST", "GET"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('staff.dashboard'))
    form = ResetRequestForm()
    if form.validate_on_submit():
        staff = Staff.query.filter_by(email=form.email.data).first()
        send_reset_email(staff)
        flash("An email has been sent to your email with instructions to reset your password", 'info')
        return redirect(url_for('staff.login'))
    return render_template('reset_request.html', form=form)


@staff.route('/staff/reset-password/<token>', methods=['POST', 'GET'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('staff.dashboard'))
    staff = Staff.verify_reset_token(token)
    if staff is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('staff.reset_request'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        staff.password = password
        db.session.commit()
        flash(f'Your password has been updated. You can now log in', 'success')
        return redirect(url_for('staff.login'))
    return render_template("reset_password.html", form=form)

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
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template('loan_categories.html', form=form,search=search)

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
        staff=Staff(first_name=first_name,last_name=last_name,national_id=national_id,status="INACTIVE",email=email,phone_number=phone_number,role=role)
        staff.save()
        send_set_password_email(staff)
        flash("New Staff Successfully Added.","success")
        return redirect(url_for("staff.view_staff"))
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template('add_staff.html', form=form,search=search)

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
        staff.status = "ACTIVE"
        db.session.commit()
        flash(f'Your password has been set. You can now log in', 'success')
        return redirect(url_for('staff.login'))

    return render_template("set_password.html", form=form)


@staff.route('/staff/member/approvals',methods=["POST","GET"])
@login_required
def member_approvals():
    members=Member.query.filter_by(memberNo=None).filter_by(status="INACTIVE").all()
    i=1
    ms={}
    for member in members:
        ms[i]=member
        i+=1
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("member_approvals.html", ms=ms,search=search)

@staff.route('/staff/<member_id>/approve',methods=["POST","GET"])
@login_required
def member_approval(member_id):
    form=ApproveMemberForm()
    member=Member.query.get_or_404(member_id)
    member.member_approver=current_user
    member.update()
    reg=Transaction.query.filter_by(phone_number=member.phone_number).filter_by(reason="REG").first()
    if form.validate_on_submit():
        verdict=form.verdict.data
        if verdict=="APPROVE":
            member.memberNo=get_member_No()
            member.status="ACTIVE"
            member.update()
            # send_approval_email(member)
            flash("Member Successfully Approved","success")
            return redirect(url_for('staff.member_approvals'))
        else:
            member.status="DISAPPROVED"
            member.update()
            if reg:
                print(f"I was called {form.reason.data}")
                send_disapproval_email(member,form.reason.data,True)
            else:
                print(f"I was called {form.reason.data}")
                send_disapproval_email(member,form.reason.data,False)
            flash("Member has been notified of the disapproval.","success")
            return redirect(url_for('staff.member_approvals'))

    reg_fees=0
    if reg:
        reg_fees=reg.amount
    form.first_name.data=member.first_name
    form.last_name.data=member.last_name
    form.national_id.data=member.national_id
    form.reg_fees.data=reg_fees
    return render_template("member_approval.html",form=form,member=member)

@staff.route('/staff/loans/view',methods=["POST","GET"])
@login_required
def view_loans():
    loans=Loan.query.filter_by(staffID=None).all()
    loans=add_nums(loans)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("view_loans.html",loans=loans,search=search)

@staff.route('/staff/loan/<loan_id>/approve',methods=["POST","GET"])
@login_required
def approve_loan(loan_id):
    loan=Loan.query.get_or_404(loan_id)
    loan.staffID=current_user.id
    loan.update()
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("approve_loan.html",loan=loan,search=search,Member=Member)

@staff.route('/staff/loan/<loan_id>/<verdict>/approve',methods=["POST","GET"])
@login_required
def staff_verdict(loan_id,verdict):
    loan=Loan.query.get_or_404(loan_id)
    if verdict == "DECLINED":
        loan.status ="DECLINED"
        loan.update()
        return redirect(url_for("staff.decline_loan",loan_id=loan_id))
    elif verdict == "APPROVED":
        loan.profile_status="APPROVED"
        loan.update()
        flash("Member profile successfully Approved","success")
        return redirect(url_for("staff.view_staff_loans"))
    else:
        flash("Wrong Verdict. Please Try Again","danger")
        return redirect(url_for("staff.approve_loan",loan_id=loan_id))

@staff.route('/staff/loans/<loan_id>/decline',methods=["POST","GET"])
@login_required
def decline_loan(loan_id):
    loan=Loan.query.get_or_404(loan_id)
    form=DeclineLoanForm()
    if form.validate_on_submit():
        reason=form.reason.data
        # send_loan_decline_email(loan.loan_applier,reason)
        flash("Loan Application Successfully Declined.The Member will be duly Notified","success")
        return redirect(url_for("staff.view_loans"))
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("decline_loan.html",form=form,search=search)

@staff.route('/staff/pending-loans/view',methods=["POST","GET"])
@login_required
def view_staff_loans():
    loans=Loan.query.filter_by(staffID=current_user.id).filter(Loan.status!="DECLINED").filter(Loan.status!="APPROVED").filter(Loan.status!="DISBURSED").filter(Loan.status!="FULFILLED").filter(Loan.status!="DEFAULTED").all()
    loans=add_nums(loans)
    has_gs={}
    has_cols={}
    for i,loan in loans.items():
        gs=Guarantor.query.filter_by(loanID=loan.id).count()
        if gs > 0:
            has_gs[i]=True
        cols= Collateral.query.filter_by(loanID=loan.id).count()
        if cols > 0:
            has_cols[i]=True

    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("view_staff_loans.html",loans=loans,has_cols=has_cols,has_gs=has_gs,search=search)

@staff.route('/staff/<loan_id>/guarantors/view',methods=["POST","GET"])
@login_required
def view_guarantors(loan_id):
    guarantors=Guarantor.query.filter_by(loanID=loan_id).all()
    guarantors=add_nums(guarantors)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("approve_guarantors.html",guarantors=guarantors,loan_id=loan_id,search=search)

@staff.route('/staff/<loan_id>/<member_id>/approve',methods=["POST","GET"])
@login_required
def approve_guarantor(loan_id,member_id):
    member=Member.query.get_or_404(member_id)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("approve_guarantor.html",loan_id=loan_id,member=member,search=search,Member=Member)

@staff.route('/staff/guarantor/<loan_id>/<member_id>/<verdict>/approve',methods=["POST","GET"])
@login_required
def guarantor_verdict(loan_id,member_id,verdict):
    guarantor=Guarantor.query.filter_by(loanID=loan_id).filter_by(memberID=member_id).first()
    loan=Loan.query.get_or_404(loan_id)
    guarantor.staffID=current_user.id
    if verdict == "DECLINED":
        guarantor.status ="DECLINED"
        guarantor.update()
        flash("Loan Guarantor successfully Declined","success")
    elif verdict == "APPROVED":
        guarantor.status="APPROVED"
        guarantor.save()
        flash("Loan Guarantor successfully Approved","success")
    else:
        flash("Wrong Verdict. Please Try Again","danger")
    guarantors=Guarantor.query.filter_by(loanID=loan_id).all()
    approved_all=[]
    declined=[]
    unconfirmed=[]
    unapproved=[]
    for g in guarantors:
        approved_all.append(g.status=="APPROVED")
        declined.append(g.status=="DECLINED")
        unconfirmed.append(g.status == "UNCONFIRMED")
        unapproved.append(g.status == "UNAPPROVED")
    if not any(unconfirmed) and not any(unapproved):
        if all(approved_all):
            loan.guarantor_status = "APPROVED"
            loan.update()

        if any(declined):
            loan.guarantor_status = "DECLINED"
            loan.update()

    return redirect(url_for("staff.view_guarantors",loan_id=loan_id))

@staff.route('/staff/<loan_id>/collaterals/view',methods=["POST","GET"])
@login_required
def view_collaterals(loan_id):
    collaterals=Collateral.query.filter_by(loanID=loan_id).all()
    collaterals=add_nums(collaterals)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("approve_collaterals.html",collaterals=collaterals,loan_id=loan_id,search=search)

@staff.route('/staff/collateral/<collateral_id>/<verdict>/approve',methods=["POST","GET"])
@login_required
def approve_collateral(collateral_id,verdict):
    col=Collateral.query.get_or_404(collateral_id)
    col.staffID=current_user.id
    if verdict == "DECLINED":
        col.status = "DECLINED"
        col.update()
        flash("Collateral has been declined.","success")
    elif verdict == "APPROVED":
        col.status = "APPROVED"
        col.update()
        flash("Collateral has been Approved.","success")
    loan=Loan.query.get_or_404(col.loanID)
    collaterals=Collateral.query.filter_by(loanID=col.loanID).all()
    approved_all=[]
    declined=[]
    unapproved=[]
    for g in collaterals:
        approved_all.append(g.status=="APPROVED")
        declined.append(g.status=="DECLINED")
        unapproved.append(g.status == "UNAPPROVED")
    if not any(unapproved):
        if all(approved_all):
            loan.collateral_status = "APPROVED"
            loan.update()

        if any(declined):
            loan.collateral_status = "DECLINED"
            loan.update()
    return redirect(url_for('staff.view_collaterals',loan_id=col.loanID))

@staff.route('/staff/members/view',methods=["POST","GET"])
@login_required
def view_members():
    members=Member.query.filter_by(status="ACTIVE").filter(Member.memberNo!=None).order_by(Member.memberNo.asc()).all()
    members=add_nums(members)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("view_members.html",members=members,search=search)

@staff.route('/staff/members/download',methods=["POST","GET"])
@login_required
def download_members():
    members=Member.query.filter_by(status="ACTIVE").filter(Member.memberNo!=None).order_by(Member.memberNo.asc()).all()
    members=add_nums(members)
    html=render_template("download_members.html",members=members,date=datetime.today(),title="Kenversity_Sacco_members.pdf")
    return render_pdf(HTML(string=html))

@staff.route('/staff/member/<member_id>/profile',methods=["POST","GET"])
@login_required
def member_profile(member_id):
    member=Member.query.get_or_404(member_id)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template('member_profile.html',member=member,Member=Member,search=search)

@staff.route('/staff/loan/<loan_id>/recommend',methods=["POST","GET"])
@login_required
def recommend_disbursement(loan_id):
    loan=Loan.query.get_or_404(loan_id)
    loan.status="APPROVED"
    loan.update()
    send_loan_approval_email(loan)
    flash("Loan has been fowarded to the credit manager for Disbursment.","success")
    return redirect(url_for('staff.view_staff_loans'))

@staff.route('/admin/loans/disburse',methods=["POST","GET"])
@login_required
def loan_disburse():
    approved_loans=Loan.query.filter_by(status="APPROVED").all()
    approved_loans=add_nums(approved_loans)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template('loan_disburse.html',search=search,approved_loans=approved_loans)

@staff.route('/admin/loan/<loan_id>/disburse',methods=["POST","GET"])
@login_required
def disburse_loan(loan_id):
    loan=Loan.query.get_or_404(loan_id)
    return render_template("disburse_loan.html",loan=loan)

@staff.route('/admin/loan/<loan_id>/<verdict>',methods=["POST","GET"])
@login_required
def disbursement_verdict(loan_id,verdict):
    loan=Loan.query.get_or_404(loan_id)
    if verdict == "DISBURSED":
        tdelta=relativedelta(months=loan.loan_cat.repayment_duration)
        loan.status="DISBURSED"
        loan.start_date=datetime.today()
        loan.end_date= datetime.today()+tdelta
        loan.amount=int(loan.amount*(1+(loan.loan_cat.interest_rate/100)))
        loan.update()
        send_loan_disbursement_email(loan)
        flash("Loan successfully disbursed.","success")
        return redirect(url_for('staff.loan_disburse'))
    else:
        loan.status="DECLINED"
        loan.update()
        flash("Loan Application has been Declined. The Loan Applicant will be duly informed","info")
        return redirect(url_for('staff.loan_disburse'))

@staff.route('/staff/view/all',methods=["POST","GET"])
@login_required
def view_staff():
    staff=Staff.query.all()
    staff=add_nums(staff)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("view_staff.html",staff=staff,search=search)

@staff.route('/staff/<staff_id>/disbursed-loans/view',methods=["POST","GET"])
@login_required
def view_my_disbursed_loans(staff_id):
    loans=Loan.query.filter_by(staffID=staff_id).filter_by(status="DISBURSED").order_by(Loan.start_date.desc()).all()
    loans=add_nums(loans)
    today=date.today()
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("view_my_disbursed_loans.html",loans=loans,search=search,Loan=Loan,today=today,not_all=True)

@staff.route('/staff/<staff_id>/defaulted-loans/view',methods=["POST","GET"])
@login_required
def view_my_defaulted_loans(staff_id):
    today=date.today()
    loans=Loan.query.filter_by(staffID=staff_id).filter_by(status="DISBURSED").filter(Loan.end_date < today).order_by(Loan.start_date.desc()).all()
    loans=add_nums(loans)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("view_my_disbursed_loans.html",loans=loans,search=search,Loan=Loan,today=today,defaulted=True,not_all=True)

@staff.route('/staff/disbursed-loans/view/all',methods=["POST","GET"])
@login_required
def view_all_disbursed_loans():
    loans=Loan.query.filter_by(status="DISBURSED").order_by(Loan.start_date.desc()).all()
    loans.extend(Loan.query.filter_by(status="FULFILLED").order_by(Loan.start_date.desc()).all())
    loans=add_nums(loans)
    today=date.today()
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("view_my_disbursed_loans.html",loans=loans,search=search,Loan=Loan,today=today,all_dis=True)

@staff.route('/staff/defaulted-loans/view/all',methods=["POST","GET"])
@login_required
def view_all_defaulted_loans():
    today=date.today()
    loans=Loan.query.filter_by(status="DISBURSED").filter(Loan.end_date < today).order_by(Loan.start_date.desc()).all()
    # loans.extend(Loan.query.filter_by(staffID=staff_id).filter_by(status="FULFILLED").filter(Loan.end_date < today).order_by(Loan.start_date.desc()).all())
    loans=add_nums(loans)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("view_my_disbursed_loans.html",loans=loans,search=search,Loan=Loan,today=today,all_def=True,defaulted=True)

@staff.route('/staff/<member_id>/loans/view',methods=["POST","GET"])
@login_required
def view_member_loans(member_id):
    member=Member.query.get_or_404(member_id)
    loans=Loan.query.filter_by(memberID=member_id).filter_by(status="DISBURSED").all()
    loans.extend(Loan.query.filter_by(memberID=member_id).filter_by(status="DEFAULTED").all())
    loans.extend(Loan.query.filter_by(memberID=member_id).filter_by(status="FULFILLED").all())
    loans=add_nums(loans)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("view_member_loans.html",loans=loans,search=search,Loan=Loan,today=date.today(),member=member)

@staff.route('/staff/<loan_id>/repayments/view',methods=["POST","GET"])
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
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("view_loan_repayments.html",repayments=repayments,loan=loan,search=search)

@staff.route('/staff/disbursed-loans/download',methods=["POST","GET"])
@login_required
def download_disbursed_loans():
    loans=Loan.query.filter_by(staffID=current_user.id).filter_by(status="DISBURSED").order_by(Loan.start_date.desc()).all()
    loans=add_nums(loans)
    today=date.today()
    html = render_template("download_disbursed_loans.html",loans=loans,staff=current_user,Loan=Loan,today=today,date=datetime.today(),title="Kenversity_Sacco_disbursed_loans.pdf")
    return render_pdf(HTML(string=html))

@staff.route('/staff/defaulted-loans/download',methods=["POST","GET"])
@login_required
def download_defaulted_loans():

    today=date.today()
    loans=Loan.query.filter_by(staffID=current_user.id).filter_by(status="DISBURSED").filter(Loan.end_date < today).order_by(Loan.start_date.desc()).all()
    loans=add_nums(loans)
    html = render_template("download_disbursed_loans.html",loans=loans,staff=current_user,Loan=Loan,today=today,date=datetime.today(),defaulted=True,title="Kenversity_Sacco_defaulted_loans.pdf")
    return render_pdf(HTML(string=html))

@staff.route('/staff/download',methods=["POST","GET"])
@login_required
def download_staff():
    staff=Staff.query.all()
    staff=add_nums(staff)
    html=render_template("download_members.html",staff=staff,date=datetime.today(),is_staff=True,title="Kenversity_Sacco_Staff.pdf")
    return render_pdf(HTML(string=html))

@staff.route('/staff/all-disbursed-loans/download',methods=["POST","GET"])
@login_required
def download_all_disbursed_loans():
    loans=Loan.query.filter_by(status="DISBURSED").order_by(Loan.start_date.desc()).all()
    loans=add_nums(loans)
    today=date.today()
    html = render_template("download_disbursed_loans.html",loans=loans,Loan=Loan,today=today,date=datetime.today(),title="Kenversity_Sacco_all_disbursed_loans.pdf")
    return render_pdf(HTML(string=html))

@staff.route('/staff/all-defaulted-loans/download',methods=["POST","GET"])
@login_required
def download_all_defaulted_loans():

    today=date.today()
    loans=Loan.query.filter_by(status="DISBURSED").filter(Loan.end_date < today).order_by(Loan.start_date.desc()).all()
    loans=add_nums(loans)
    html = render_template("download_disbursed_loans.html",loans=loans,Loan=Loan,today=today,date=datetime.today(),defaulted=True,title="Kenversity_Sacco_all_defaulted_loans.pdf")
    return render_pdf(HTML(string=html))

@staff.route('/staff/<loan_id>/repayments/download',methods=["POST","GET"])
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

@staff.route('/staff/<staff_id>/profile',methods=["POST","GET"])
@login_required
def staff_profile(staff_id):
    staff=Staff.query.get_or_404(staff_id)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template('staff_profile.html',staff=staff,Staff=Staff,search=search)

@staff.route('/staff/<member_id>/profile/download',methods=["POST","GET"])
@login_required
def download_member_profile(member_id):
    member=Member.query.get_or_404(member_id)
    today=date.today()
    html = render_template("download_member_profile.html",member=member,Member=Member,date=datetime.today(),title=f"Kenversity_Sacco_{member.memberNo}_profile.pdf")
    return render_pdf(HTML(string=html))

@staff.route('/staff/<staff_id>/staff/profile/download',methods=["POST","GET"])
@login_required
def download_staff_profile(staff_id):
    staff=Staff.query.get(staff_id)
    today=date.today()
    html = render_template("download_staff_profile.html",staff=staff,Staff=Staff,date=datetime.today(),title=f"Kenversity_Sacco_profile.pdf")
    return render_pdf(HTML(string=html))

@staff.route('/staff/ticket/<ticket_id>/view',methods=["POST","GET"])
@login_required
def view_ticket(ticket_id):
    form=UpdateTicketForm()
    form.ticket_id.data=ticket_id
    if form.validate_on_submit():
        ticket_msg=TicketMessage(ticketID=form.ticket_id.data,message=form.message.data,sender="STAFF",staffID=current_user.id)
        ticket_msg.save()
        return redirect(url_for("staff.view_ticket",ticket_id=ticket_id))
    ticket=Ticket.query.get_or_404(ticket_id)
    ticket_msgs=TicketMessage.query.filter_by(ticketID=ticket.id)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("view_ticket.html",ticket=ticket,ticket_msgs=ticket_msgs,form=form,search=search)

@staff.route('/staff/ticket/<ticket_id>/close',methods=["POST","GET"])
@login_required
def close_ticket(ticket_id):
    ticket=Ticket.query.get_or_404(ticket_id)
    ticket.status = "CLOSED"
    ticket.save()
    flash("Ticket closed","success")
    return redirect(url_for('staff.view_ticket',ticket_id=ticket_id))

@staff.route('/staff/tickets/all/view',methods=["POST","GET"])
@login_required
def view_all_tickets():
    tickets=Ticket.query.all()
    tickets=add_nums(tickets)
    search=SearchForm()
    if search.validate_on_submit():
        return redirect(url_for('staff.searches', data=search.text.data))
    return render_template("view_all_ticket.html",tickets=tickets,Ticket=Ticket,search=search)

@staff.route('/staff/member/<member_id>/delete',methods=["POST","GET"])
@login_required
def delete_member(member_id):
    member=Member.query.get_or_404(member_id)
    member.status = "DEACTIVATED"
    member.update()
    flash("Member inactivated successfully","warning")
    return redirect(url_for('staff.member_profile',member_id=member_id))

@staff.route('/staff/member/<member_id>/activate',methods=["POST","GET"])
@login_required
def activate_member(member_id):
    member=Member.query.get_or_404(member_id)
    member.status = "ACTIVE"
    member.update()
    flash("Member activated successfully","success")
    return redirect(url_for('staff.member_profile',member_id=member_id))
