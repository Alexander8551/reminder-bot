import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'my_secret_key'
    SQLALCHEMY_DATABASE_URI = 'mariadb+mariadbconnector://reminder:vi8AJit8@localhost/telegram_reminders'
    SQLALCHEMY_TRACK_MODIFICATIONS = False