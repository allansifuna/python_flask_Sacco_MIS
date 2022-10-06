import os
import secrets
from PIL import Image
from flask import render_template, url_for,current_app
from flask_mail import Message
from kenversity import mail,mpesa


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

