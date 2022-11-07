import os
import secrets
from PIL import Image
from flask import render_template, url_for,current_app
from flask_mail import Message
from kenversity import mail,mpesa
from kenversity.models import Loan,Repayment,Ticket,Deposit,Transaction
from random import choice
from random import randrange
from datetime import datetime,timedelta

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/ids', picture_fn)
    output_size = (640, 480)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

def save_file(form_file):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_file.filename)
    file_fn = random_hex + f_ext
    file_path = os.path.join(current_app.root_path, 'static/kra', file_fn)
    form_file.save(file_path)

    return file_fn

def simulate_pay(phone,amount):
    data = {
        "business_shortcode": current_app.config.get("BUSINESS_SHORTCODE"),
        "passcode": current_app.config.get("PASSCODE"),
        "amount": amount,
        "phone_number":phone, #phone number to be prompted to pay
        "reference_code": f"REG_{phone}",
        "callback_url": current_app.config.get("CALLBACK_URL"), # cllback url should be exposes. for testing putposes you can route on host 0.0.0.0 and set the callback url to be https://youripaddress:yourport/endpoint
        "description": "Registration fees on Kenversity" #a description of the transaction its optional
    }
    resp = mpesa.MpesaExpress.stk_push(**data)
    if resp.get("ResponseCode")=="0":
        return resp
    return False

def add_nums(data):
    new_dict={}
    i=1
    for datum in data:
        new_dict[i]=datum
        i+=1
    return new_dict

def get_loan_No():
    loans=Loan.query.order_by(Loan.loanNo.asc()).all()
    if len(loans) == 0 :
        return "LN00001"
    else:
        num=loans[-1].loanNo
        num=int(num[2:])+1
        num=str(num).zfill(5)
        return f"LN{num}"


def get_ticket_No():
    tickets=Ticket.query.order_by(Ticket.ticketNo.asc()).all()
    if len(tickets) == 0 :
        return "TK00001"
    else:
        num=tickets[-1].ticketNo
        num=int(num[2:])+1
        num=str(num).zfill(5)
        return f"TK{num}"
def get_repayment_No():
    repayments=Repayment.query.order_by(Repayment.repaymentNo.asc()).all()
    if len(repayments) == 0 :
        return "RP00001"
    else:
        num=repayments[-1].repaymentNo
        num=int(num[2:])+1
        num=str(num).zfill(5)
        return f"RP{num}"

def send_reset_email(member):
    token = member.get_reset_token()
    msg = Message('Password Reset Request', sender=("Kenversity SACCO", "Ke"), recipients=[member.email])
    msg.body = f'''
    To reset your password follow the following link:
    {url_for('member.reset_token', token=token, _external=True)}



    if you did not make this request just ignore this email.
    '''
    mail.send(msg)

def get_random_date():
    tdelta=timedelta(days=90)
    end=datetime.now()
    start=end-tdelta
    rand_delta=randrange(90)
    t_delta=timedelta(days=rand_delta)
    return start+t_delta

def mock_deposits(member,num):
    values=[1,2,3,4,5,6,7,8,9,0,"A","B","C","D","E","F","H","G","I","J","K","L","M","N","O","P","Z","R","S","T"]
    for i in range(num):
        date_created=get_random_date()
        code=["Q"]
        for i in range(9):
            code.append(str(choice(values)))

        vs=[1,2,3,4,5,6,7,8,9,0]
        chrid=[]
        for i in range(5):
            chrid.append(str(choice(vs)))
        chrid="".join(chrid)
        transaction=Transaction(transaction_code="".join(code),phone_number=member.phone_number,amount=choice([1000,500,700,600,2000,1500]),reason="DEP",date_created=date_created)
        transaction.save()
        dep=Deposit(memberID=member.id,CheckoutRequestID=f"ws_CO_061020222032{chrid}{transaction.phone_number[3:]}",transactionID=transaction.id,amount=transaction.amount,deposit_date=date_created)
        dep.save()
def mock_repayments(member,loan,num):
    values=[1,2,3,4,5,6,7,8,9,0,"A","B","C","D","E","F","H","G","I","J","K","L","M","N","O","P","Z","R","S","T"]
    amnt=Loan.get_remaining_amount(loan.id)
    for i in range(num):
        code=["Q"]
        for i in range(9):
            code.append(str(choice(values)))

        vs=[1,2,3,4,5,6,7,8,9,0]
        chrid=[]
        for i in range(5):
            chrid.append(str(choice(vs)))
        chrid="".join(chrid)
        amount=choice([1000,2500,2700,650,500])
        done=False
        if amount >= amnt:
            amount=amnt
            done=True
        else:
            amnt-=amount
        transaction=Transaction(transaction_code="".join(code),phone_number=member.phone_number,amount=amount,reason="REP")
        transaction.save()
        rep=Repayment(memberID=member.id,repaymentNo=get_repayment_No(),loanID=loan.id,CheckoutRequestID=f"ws_CO_061020222032{chrid}{transaction.phone_number[3:]}",transactionID=transaction.id,amount=transaction.amount)
        rep.save()
        if done:
            loan.status =  "FULFILLED"
            loan.update()
            return
