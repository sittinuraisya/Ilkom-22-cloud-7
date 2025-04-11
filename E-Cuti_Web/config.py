import os
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite3'
    MAIL_SERVER = 'smtp.mailgun.org'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
    GOOGLE_CALENDAR_CREDENTIALS = 'credentials.json'