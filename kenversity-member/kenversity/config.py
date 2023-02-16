import os
import secrets


class Config:
    basedir = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = 'kdhjgvfcmvyugdiqygiqebudb'
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    ADMINS = 'allansifuna324@gmail.com'
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = 'Kenversity SACCO Developers'
    SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
    API_ENVIRONMENT="production"
    APP_KEY=os.environ.get("APP_KEY")
    APP_SECRET=os.environ.get("APP_SECRET")
    BUSINESS_SHORTCODE=os.environ.get("BUSINESS_SHORTCODE")
    PASSCODE=os.environ.get("PASSCODE")
    CALLBACK_URL="https://3209-154-122-233-254.in.ngrok.io/callback_url"

class Development(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:////home/allan/Documents/kenversityMIS/kenversity.db'

class Producton(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/kenversity?user=postgres&password=admin123'

conf={"dev":Development,"prod":Producton}
