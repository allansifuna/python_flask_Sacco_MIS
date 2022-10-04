from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_mpesa import MpesaAPI
# from flask_redis import FlaskRedis
from logging.handlers import SMTPHandler
import logging
from kenversity.config import conf
import os

db = SQLAlchemy()
bcrypt = Bcrypt()
lm = LoginManager()
lms=LoginManager()
mail = Mail()
mpesa= MpesaAPI()
# redis = FlaskRedis()
lm.login_view = 'member.login'
lm.login_message_category = 'info'
migrate = Migrate()


def create_app(conf_method):
    app = Flask(__name__)
    app.config.from_object(conf.get(conf_method))

    from kenversity.member.routes import member

    db.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    lm.init_app(app)
    mpesa.init_app(app)
    # redis.init_app(app)

    app.register_blueprint(member)

    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr=('no-reply@' + app.config['MAIL_SERVER']),
                toaddrs=app.config['ADMINS'], subject=(
                    "Kenversity SACCO Developers", "Ke"),
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

    return(app)
