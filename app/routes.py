from app import app
from flask import render_template,redirect,url_for,flash,request
from app.forms import LoginForm, RegistrationForm, WeighInForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Measurement
from werkzeug.urls import url_parse
from app import db
import datetime


@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')

@app.route('/login',methods=['GET', 'POST'])
def login():
    form = LoginForm()
    #If the user is logged in, they dont need to login again
    if current_user.is_authenticated:
        return redirect( url_for('index') )
    if form.validate_on_submit():
        #Get the user from the form
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        next_page = request.args.get('next')
        login_user(user, remember=form.remember_me.data)
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(first_name=form.first_name.data,last_name=form.last_name.data,email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)



@app.route('/weigh_in',methods=['GET', 'POST'])
@login_required
def weigh_in():
    form = WeighInForm()
    #Shouldnt be possible
    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    if form.validate_on_submit():
        email = current_user.email
        #Measurement wants a datetime, form only gives date
        date = form.timestamp.data
        time = datetime.datetime.now().time()
        dt = datetime.datetime.combine(date,time)
        
        weight = form.weight.data
        
        measurement = Measurement(timestamp=dt,email=email,weight=weight)
        db.session.add(measurement)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('weigh_in.html',title='Weigh In',form=form)