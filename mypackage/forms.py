from flask_wtf import FlaskForm
from flask_wtf.file import FileField,FileRequired,FileAllowed
from wtforms import StringField, PasswordField, SubmitField, DateField,SelectField
from wtforms.validators import DataRequired, Email,EqualTo


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message="Your email is required"),Email()])
    password = PasswordField('Password', validators=[DataRequired(message='Enter your password')])
    login = SubmitField('Login')

class Meta:
        csrf = True
        csrf_time_limit = 7200

class SignupForm(FlaskForm):
    lname = StringField('Surname',validators=[DataRequired(message='Surname is reguired')])
    fname = StringField('Firstname',validators=[DataRequired(message='firstname is reguired')])
    middlename = StringField('Othername')
    file_num = StringField('File Number')
    dob = DateField('Date of Birth',validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(),Email()])
    phone = StringField('Phone')
    pswd = PasswordField('Create Password', validators=[DataRequired(message='Password can not be empty')])
    date_employed = DateField('Date of First Appointment',validators=[DataRequired()])
    origin_state = StringField('State of Origin')
    dept = SelectField('Department', choices=[('', 'Select your deptartment..'),('gap', 'GAP'), ('eops', 'EOPs'), ('ict', 'ICT'),('acct', 'F&A'),('legal', 'Legal')])
    gender = SelectField('Gender', choices=[('', 'Select your gender'),('male', 'Male'), ('female', 'Female')])
    signup = SubmitField('Sign Up')


class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message="Your Username is required")])
    password = PasswordField('Password', validators=[DataRequired(message='Enter your password')])
    login = SubmitField('Login')

class DpForm(FlaskForm):
        photo = FileField(validators=[FileRequired(),FileAllowed(['jpg','jpeg','png'], 'Only images are allowed')])
        uploadbtn = SubmitField('Upload Picture')

class ChangePswForm(FlaskForm):
    current_pwd = PasswordField('Current Password', validators=[DataRequired(message='Enter your password')])
    new_pwd = PasswordField('New Password', validators=[DataRequired(message='Enter new password')])
    confirm_newpwd = PasswordField('Confirm New Password', validators=[DataRequired(),EqualTo('new_pwd', message='Confirm password must be the same as new password')])
    submit = SubmitField('Submit')