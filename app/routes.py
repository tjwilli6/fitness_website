from app import app
from flask import render_template,redirect,url_for,flash,request
from app.forms import LoginForm, RegistrationForm, WeighInForm, get_remove_weight_form
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Measurement
from werkzeug.urls import url_parse
from app import db
import datetime
import numpy as np
import app.analysis as ana
import app.plotting as plotting
import os
import string
import app.config as cfg
from app.utils import DateUtil
import pickle
from matplotlib import colors


def get_active_users():

    ianausers = list( map( ana.AnaData,User.query.all() ) )
    users = {}
    bad_names = []
    weights = []
    for i,ianauser in enumerate( ianausers ):
        users[ianauser.get_user().email] = ianauser
        if not ianauser.status:
            bad_names.append(ianauser.get_user().email)
            print('User[{}] is bad'.format(i))
            continue
        weights.append( ianauser.get_ydata()[-1] )
    #Remove users who don't have any data
    for name in bad_names:
        print('Pop bad user {}'.format(name))
        users.pop(name)
    ianausers = [ iana for _,iana in sorted(zip(weights,users.values())) ]

    return ianausers

def mangle_filename(fname,size=5):
    """From https://stackoverflow.com/questions/728616/disable-cache-for-some-images
    Adds a random dummy string to the end of the file name so the browser won't cache it"""
    fake_q = np.random.choice(list(string.ascii_uppercase) + list(string.digits),size)
    fname_new = '{}?dummy={}'.format(fname,''.join(fake_q))
    return fname_new


def get_image():
    files = [f for f in os.listdir("app/static/images") if not os.path.isdir( os.path.join('app','static','images',f) ) and '_alpha' in f ]

    if files:
        im = files [np.random.randint(0,len(files))]
        return im

def get_plotting_colors(users):

    cdict = {}
    b_writedict = False
    if os.path.isfile(cfg.COLORS_FNAME):
        with open(cfg.COLORS_FNAME,'rb') as f:
            cdict = pickle.load(f)

    iter_colors = plotting.Plotter.iter_colors()
    for user in users:
        if user.get_user().email in cdict.keys():
            continue
        b_writedict = True
        cdict [user.get_user().email] = next( iter_colors )

    if b_writedict:
        with open(cfg.COLORS_FNAME,'wb') as f:
            pickle.dump(cdict,f)

    return cdict

def plot_user(fname,ianauser,norm=False):
    iname = current_user.first_name
    outdir = os.path.join('app','static','images','plots','user',iname.lower())
    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    fname_full = os.path.join(outdir,fname)

    plotter = plotting.Plotter(norm=norm)
    plotter.plot_user(ianauser)
    plotter.savefig(fname_full)

    fname_rel = os.path.join('..','static','images','plots','user',iname.lower(),os.path.split(fname_full)[-1])

    return mangle_filename(fname_rel)

def plot_active_users(fname,ianausers,norm=True):
    iname = 'results_sum'

    outdir = os.path.join('app','static','images','plots','all',iname.lower())

    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    fname_full = os.path.join(outdir,fname)

    if os.path.isfile(fname_full):
        os.remove(fname_full)
        
    colors = get_plotting_colors(ianausers)

    plotter = plotting.Plotter(norm=norm)

    plotter.plot_all_users(ianausers,colors=colors)

    plotter.savefig(fname_full)

    fname_rel = os.path.join('..','static','images','plots','all',iname.lower(),os.path.split(fname_full)[-1])

    return mangle_filename(fname_rel)

@app.route('/')
@app.route('/index')
#@login_required
def index():
    days_left = np.abs( (cfg.DT_STOP - DateUtil.now().date() ).days )
    users = get_active_users()
    leaders = []
    if users:
        leaders.append(users[0])
        for user in users[1:]:
            if np.isclose(user.get_ydata()[-1],leaders[0].get_ydata()[-1]):
                leaders.append(user)
    return render_template('index.html', title='Home', image=get_image(),
        days_left=days_left,leaders=[l.get_user().first_name for l in leaders])


@app.route('/user/<username>')
@login_required
def user(username):

    
    tSTART = DateUtil.date_to_datetime(cfg.DT_STRT)
    tSTOP = DateUtil.date_to_datetime(cfg.DT_STOP)
    
    measurements = [
            m for m in Measurement.query.filter_by(email=current_user.email).all()
            if m.timestamp >= tSTART and m.timestamp <= tSTOP
    ]
    
    ianauser = ana.AnaData(current_user)

    fname = plot_user("{}-plot.png".format(current_user.first_name.lower()), ianauser )


    date = cfg.DT_STOP
    proj_weight,proj_weight_err = ianauser.get_projected_weight(date)
    return render_template('user.html',measurements=measurements,title="{}'s Page".format(current_user.first_name),
                           fname=fname,user=ianauser,date=date,
                           proj_weight=proj_weight,proj_weight_err=proj_weight_err,
                           image=get_image())

@app.route('/results')
@login_required
def results():

    ianausers = get_active_users()
    fname = plot_active_users("results-plot.png",ianausers)
    icolors = get_plotting_colors(ianausers)
    for key in icolors.keys():
        icolors[key] = colors.to_hex(icolors[key])

    return render_template("results_sum.html",anausers=ianausers,
        fname=fname,image=get_image(),colors=icolors)


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
        #Form provides the date Easter Time Zone 
        #Form doesnt provide a time
        #This is a work around
        #Get the time in the same TZ as the form
        time = DateUtil.now().time()
        #Now get the datetime object and convert it back to UTC
        dt = datetime.datetime.combine(date,time) - DateUtil.get_utc_offset()

        weight = form.weight.data

        measurement = Measurement(timestamp=dt,email=email,weight=weight)
        db.session.add(measurement)
        db.session.commit()
        return redirect(url_for('user',username=current_user.first_name))
    return render_template('weigh_in.html',title='Weigh In',form=form)

#@app.route('/help')
#def help():
#    image = get_image()
#    return render_template('help.html',image=image)
