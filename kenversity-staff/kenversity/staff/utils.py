from kenversity import mail
from flask_mail import Message
from flask import url_for
def send_set_password_email(user):
    token = user.get_reset_token()
    msg = Message('Password Setting Email', sender=(
        "Kenversity SACCO", "Ke"), recipients=[user.email])
    msg.body = f'''
    You have been added to Kenversity SACCO portal as one of their Employees.
    To gain access into the system, You are required to set a password and log in
    to the system using this email.


    To set your password follow the following link:
    {url_for('staff.set_password', token=token, _external=True)}



    if you did not make this request just ignore this email.
    '''
    mail.send(msg)
