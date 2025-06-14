import secrets
from datetime import datetime,date
from dateutil.relativedelta import relativedelta
from functools import wraps
from flask import render_template,redirect,request,url_for,flash,session
from flask_mail import Message
from mypackage import mail

from werkzeug.security import check_password_hash, generate_password_hash
from mypackage import app
from mypackage.forms import LoginForm,DpForm,ChangePswForm
from mypackage.models import db, Employee,Promotion,State,JobHistory,Designation,Leave


@app.errorhandler(500)
def internal_server_error(error):
    return render_template("employee/error500.html", error=error),500

@app.errorhandler(404)
def page_not_found(error):
    return render_template("employee/error404.html", error=error),404


def login_required(f):
    @wraps(f) 
    def login_decoration(*args,**kwargs):
        guestid = session.get('employeeonline')
        if guestid:
            return f(*args,**kwargs)
        else:
            flash("You must be logged in to view this page", category='failed')
            return redirect(url_for('portal'))
    return login_decoration


@app.route('/home/')
def home():
    return render_template('index.html')

@app.route("/")
def portal():
    loginform = LoginForm()
    return render_template("portal.html", loginform=loginform)

@app.route('/employee/login/', methods=["GET","POST"])
def employee_login():
    loginform = LoginForm()
    if loginform.validate_on_submit():
        email = request.form.get('email')
        pswd = request.form.get('password')
    
        deets = db.session.query(Employee).filter(Employee.employee_email==email).first()  #check if supplied email exist
        if deets:
            if not deets.is_active:  #check if employee is active
                flash('Your account has been deactivated. Please contact admin.', 'failed')
                return redirect(url_for('employee_login'))
            #else compare password supplied to password stored in the database
            checkpass = check_password_hash(deets.employee_loginpwd,pswd) 
            if checkpass:
                session['employeeonline'] = deets.employee_id
                return redirect(url_for('employee_dashboard'))
            else:
                flash("Password incorrect", category='failed')
                print("Incorrect password")
                return redirect(url_for('portal'))
        else:
            flash("Email not registered",category='failed')
            return redirect(url_for('portal'))
    else:
        return render_template('portal.html',loginform=loginform)


@app.route("/employee/dashboard/")
def employee_dashboard():
    employee_id = session.get('employeeonline')
    if employee_id:
        today = date.today()

        deets = Employee.query.get_or_404(employee_id)
        designations = Designation.query.all()  # Fetch all designations
        promotions = Promotion.query.filter_by(employee_id=employee_id).all()
        job_history = JobHistory.query.filter_by(employeeid=employee_id).all()  #job_history = deets.job_history (Fetch job history for the employee)
        # Get the latest job history entry
        if job_history:
            latest_job = job_history[-1]

        # leaves_taken = Leave.query.filter_by(employee_id=deets.employee_id, status='approved').count()
        # Fetch approved leave requests
        approved_leaves = Leave.query.filter_by(employee_id=deets.employee_id, status='approved').all()

    # Calculate total days
        total_leave_days = sum((leave.end_date - leave.start_date).days + 1 for leave in approved_leaves)

        # Calculate work duration
        work_duration = relativedelta(today, deets.date_employed)
        work_duration_str = f"{work_duration.years} years {work_duration.months} months {work_duration.days} days"

        birthdays_today = Employee.query.filter(
        db.extract('day', Employee.employee_dob) == today.day,
        db.extract('month', Employee.employee_dob) == today.month
        ).all()

        return render_template("employee/dashboard.html",
            deets=deets,
            designations=designations,
            promotions=promotions,
            job_history=job_history,
            latest_job=latest_job,
            total_leave_days=total_leave_days, 
            birthdays_today=birthdays_today,
            work_duration=work_duration_str
        )
    else:
        flash("You have to login to view the page",category='failed')
        return redirect(url_for('portal'))


@app.route('/update/record/',methods=['POST','GET'])
@login_required
def update_record():
    employee = Employee.query.get(session['employeeonline'])
    states = State.query.all()
    if request.method == 'POST': #retrieve form data
        othername = request.form.get('othername')
        phone = request.form.get('phone')
        gender = request.form.get('gender')
        state_id = request.form.get('state')
        state_id = int(state_id)
    
        employee.employee_othername = othername
        employee.phone = phone
        employee.gender = gender
        employee.stateof_originid = state_id

        db.session.commit()
        flash('Profile updated successfully', category='success')
        return redirect(url_for('employee_dashboard'))
    return render_template("employee/update_record.html",employee=employee,states=states)


@app.route("/upload/pic/", methods=['GET','POST'])
@login_required
def upload_picture():
    dpform = DpForm()
    id = session.get('employeeonline')
    deets = db.session.query(Employee).get(id)
    if request.method == "GET":
        return render_template('employee/upload_pic.html',deets=deets,dpform=dpform)
    else:
        if dpform.validate_on_submit():
            file = request.files.get('photo')
            filename = file.filename
            extension = filename.split('.')
            ext = extension[-1]
            generated_filename = secrets.token_urlsafe(5)+ "."+ ext

            file.save('mypackage/static/uploads/'+generated_filename)
            deets.employee_dp = generated_filename
            db.session.commit()
            return redirect(url_for('employee_dashboard'))
        else: 
            return render_template('employee/upload_pic.html',deets=deets,dpform=dpform)


@app.route('/employee/job_history/')
@login_required
def view_job_history():
    employee_id = session.get('employeeonline')
    employee = Employee.query.get_or_404(employee_id)
    job_history = employee.job_history

    return render_template('employee/job_history.html', job_history=job_history)


@app.route('/change_password/', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePswForm()
    employee_id = session.get('employeeonline')
    current_user = Employee.query.get_or_404(employee_id)
    if form.validate_on_submit():
        current_pwd = request.form.get('current_pwd')
        new_pwd = request.form.get('new_pwd')

        # Check if current password is correct
        if not check_password_hash(current_user.employee_loginpwd, current_pwd):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('change_password'))

        # Update the password
        current_user.employee_loginpwd = generate_password_hash(new_pwd)
        db.session.commit()
        flash('Password changed successfully.', 'success')
        return redirect(url_for('employee_dashboard'))
    else:
        return render_template('employee/change_password.html',form=form)


@app.route('/apply/leave/', methods=['GET', 'POST'])
@login_required
def apply_leave():
    id = session.get('employeeonline')
    
    if request.method == 'POST':
        leave_type = request.form.get('leave_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        reason = request.form.get('reason')

        leave = Leave(
            employee_id=id,
            leave_type=leave_type,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
            reason=reason,
            status='Pending'
        )
        db.session.add(leave)
        db.session.commit()
        flash('Leave application submitted successfully.',category= 'success')
        return redirect(url_for('employee_dashboard')) 

    return render_template('employee/apply_leave.html')


@app.route("/employee/logout/")
def employee_logout():
    session.pop('employeeonline', None)
    return redirect(url_for('portal'))


@app.route('/contact/', methods=['POST'])
def contact():
    name = request.form.get('name')
    email = request.form.get('email')
    message_content = request.form.get('message')

    msg = Message(
        subject=f'New Contact Form Message from {name}',
        recipients=['olumuyiwaolu@gmail.com'], 
        body=f"From: {name} <{email}>\n\nMessage:\n{message_content}"
    )
    try:
        mail.send(msg)
        flash('Your message has been sent successfully!', 'success')
    except Exception as e:
        flash(f'An error occurred while sending the message: {e}', 'failed')

    return redirect(url_for('home'))
