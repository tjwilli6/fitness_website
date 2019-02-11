from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField,DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User,Measurement
from datetime import date

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()] )
    last_name = StringField('Last Name', validators=[DataRequired()] )
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
            

class WeighInForm(FlaskForm):
    timestamp = DateField('Date',default=date.today())
    weight = FloatField('Weight [lbs]',validators=[DataRequired()])
    submit = SubmitField('Submit')
    
    def validate_weight(self,weight):
        if weight.data <=0 or weight.data >= 5000:
            raise ValidationError("I don't believe that is your weight. Idiot.")
            
            
def get_remove_weight_form(user):
    measurements = Measurement.query.filter_by(email=user.email)
    class RemoveWeightForm(FlaskForm):
        pass
        
    for i,meas in enumerate(measurements):
        name = '{} ({}, {} lbs)'.format(i+1,meas.timestamp.date(),meas.weight)
        setattr(RemoveWeightForm,'field_{}'.format(i+1),BooleanField(name))
        
    RemoveWeightForm.submit = SubmitField('Remove Data')
    
    return RemoveWeightForm()