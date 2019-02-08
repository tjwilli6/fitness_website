from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), index=True)
    last_name = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True, unique=True)
    height = db.Column(db.Float())
    date_created = db.Column(db.DateTime,default=datetime.now)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {} [{}]>'.format(self.first_name,self.email) 
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
  
    
@login.user_loader
def load_user(id):
    return User.query.get(int(id))
    
class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True)
    weight = db.Column(db.Float)
    timestamp = db.Column(db.DateTime,default=datetime.now)
    
    def __repr__(self):
        return '<Weight Measurement by {} on {}>'.format(self.email,self.timestamp)