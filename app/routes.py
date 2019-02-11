from app import app
from flask import render_template,redirect,url_for,flash,request,make_response
from functools import wraps, update_wrapper
from app.forms import LoginForm, RegistrationForm, WeighInForm, get_remove_weight_form
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Measurement
from werkzeug.urls import url_parse
from app import db
import datetime
import numpy as np
import analysis as ana
import plotting
import os
import string


def mangle_filename(fname,size=5):
    """From https://stackoverflow.com/questions/728616/disable-cache-for-some-images
    Adds a random dummy string to the end of the file name so the browser won't cache it"""
    fake_q = np.random.choice(list(string.ascii_uppercase) + list(string.digits),size)
    fname_new = '{}?dummy={}'.format(fname,''.join(fake_q))
    return fname_new


def get_image():
    files = [f for f in os.listdir("app/static/images") if not os.path.isdir(f)]
    
    if files:
        im = files [np.random.randint(0,len(files))]
        print im
        return im
 
def plot_user(fname):
    iname = current_user.first_name
    outdir = os.path.join('app','static','images','plots','user',iname.lower())
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    
    fname_full = os.path.join(outdir,fname)
    
    ianauser = ana.AnaData(current_user)

    plotter = plotting.Plotter()
    plotter.plot_user(ianauser)
    plotter.savefig(fname_full)
    
    fname_rel = os.path.join('..','static','images','plots','user',iname.lower(),os.path.split(fname_full)[-1])
    
    return mangle_filename(fname_rel)
    

@app.route('/')
@app.route('/index')
#@login_required
def index():
    return render_template('index.html', title='Home', image=get_image())


@app.route('/user/<username>')
@login_required
def user(username):
    
    measurements = Measurement.query.filter_by(email=current_user.email)
    
    fname = plot_user("{}-plot.png".format(current_user.first_name.lower()))
    
    return render_template('user.html',measurements=measurements,title="{}'s Page".format(current_user.first_name),
                           fname=fname)

@app.route('/user/remove_data',methods=['GET', 'POST'])
@login_required
def remove_data():
    
    form = get_remove_weight_form(current_user)
    
    if form.validate_on_submit():
        measurements = Measurement.query.filter_by(email=current_user.email)
        for i,meas in enumerate(measurements):
            cbox = getattr(form,'field_{}'.format(i+1),None)
            if cbox is None:
                continue
            if cbox.data:
                db.session.delete(meas)
                db.session.commit()
        
        return redirect(url_for('user', username=current_user.first_name))
    return render_template('remove_data.html',form=form)

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
        return redirect(url_for('user',username=current_user.first_name))
    return render_template('weigh_in.html',title='Weigh In',form=form)