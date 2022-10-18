from kenversity import mail
from flask_mail import Message
from kenversity.models import Member
from flask import url_for

def send_set_password_email(user):
    token = user.get_reset_token()
    msg = Message('Password Setting Email', sender=(
        "Kenversity SACCO", "Ke"), recipients=[user.email])
    msg.body = f'''
    You have been added to Kenversity SACCO portal as one of their Staff.
    To gain access into the system, You are required to set a password and log in
    to the system using this email.


    To set your password follow the following link:
    {url_for('staff.set_password', token=token, _external=True)}



    if you did not make this request just ignore this email.
    '''
    mail.send(msg)

def get_member_No():
    members=Member.query.filter(Member.memberNo!=None).order_by(Member.memberNo.asc()).all()
    if len(members) == 0 :
        return "MB00001"
    else:
        num=members[-1].memberNo
        num=int(num[2:])+1
        num=str(num).zfill(5)
        return f"MB{num}"


def send_approval_email(member):
    msg = Message('Member Approved Email', sender=(
        "Kenversity SACCO", "Ke"), recipients=[member.email])
    msg.body = f'''
    Dear {member.first_name},

    Your membership request has been successfully approved.

    Your membership Number is {member.memberNo}.

    You can now log in into the Kenversity Sacco member's portal and start making deposits to grow your shares.

    Thank you.

    Regards,
    Kenversity Sacco Staff.
    '''
    mail.send(msg)

def send_disapproval_email(member,reason,reg_fees):
    msg = Message('Member Approval Declined', sender=(
        "Kenversity SACCO", "Ke"), recipients=[member.email])
    if reg_fees:
        msg.body = f'''

        Dear {member.first_name},

        Your application to join Kenversity sacco as a member has been declined due to the following reasons:-

        {reason}


        Since it seams that you ahve not paid your registration fees, please follow the following link to pay.

        http://127.0.0.1:5000/member/register?stage=payment&member={member.id}



        If the problem persists, please visit our officess physically.
        Thank you.

        Regards,
        Kenversity Sacco Staff.
        '''
    else:
        msg.body = f'''

        Dear {member.first_name},

        Your application to join Kenversity sacco as a member has been declined due to the following reasons:-

        {reason}


        It seams like there is an issue with your documents.
        Please follow the following link to re-upload your documents.

        http://127.0.0.1:5000/member/register?stage=user_data&member={member.id}

        Make sure the images are cler and readable.


        If the problem persists, please visit our officess physically.

        Thank you.

        Regards,
        Kenversity Sacco Staff.
        '''
    mail.send(msg)

def send_loan_decline_email(member,reason):
    msg = Message('Loan Application Decline Email', sender=(
        "Kenversity SACCO", "Ke"), recipients=[member.email])
    msg.body = f'''
    Dear {member.first_name},

    Your Loan Application has been declined.

    This is due to the following reasons cited by staff:-
    {reason}.


    Thank you.

    Regards,
    Kenversity Sacco Staff.
    '''
    mail.send(msg)



def add_nums(data):
    new_dict={}
    i=1
    for datum in data:
        new_dict[i]=datum
        i+=1
    return new_dict
