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
    MAIL_USERNAME = 'noreply.sifuna@gmail.com'
    MAIL_PASSWORD = 'yogeroyogerodinero33'
    MAIL_DEFAULT_SENDER = 'Kenversity SACCO Developers'
    SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
    API_ENVIRONMENT="production"
    APP_KEY="kAXqU8JZzdzxUchRKnnaKVPX5AVl1MLZ"
    APP_SECRET="Dmpu7oYaCULD1xZG"
    BUSINESS_SHORTCODE="4029829"
    PASSCODE="2ce084c9f634b1334c806ce7c7b3cbfdf8f6a5e5b1a4a94f64a5495a3cb27960"
    CALLBACK_URL="https://550e-105-50-230-22.eu.ngrok.io/callback_url"

class Development(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:////home/allan/Documents/kenversityMIS/kenversity.db'

class Producton(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/eacdt?user=postgres&password=admin123'

conf={"dev":Development,"prod":Producton}
