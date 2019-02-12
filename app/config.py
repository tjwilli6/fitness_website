import os
import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

WT_ERROR = 5.
DT_STOP = datetime.date(year=2019,month=6,day=1)

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'not_a_doctor___shhh'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
