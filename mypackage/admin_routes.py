from functools import wraps
from datetime import datetime,timedelta
from flask import render_template,flash,redirect,url_for,session,request
from flask_mail import Message
from werkzeug.security import generate_password_hash,check_password_hash
from mypackage import app,mail
from .models import db, Employee,Promotion,Admin,Designation,JobHistory,State,Lga,Department,Leave
from .forms import AdminLoginForm


@app.template_filter('date')
def format_date(value, format="%d %b, %Y"):
    return value.strftime(format) if value else ""


def calculate_promotion_date(date_employed):
    """
    Calculates the promotion date, 3 years after the employment date.
    """
    return date_employed + timedelta(days=3 * 365)


def send_email(fname,userpsw,email): # onboarding email to be sent to an employee
    msg = Message(subject='Onboarding!',sender=('Olu','noreply@gmail.com'),recipients=[email])
            
    msg.body = f"""Hello, {fname}, 
                An account has been created for you, please login to proceed to your dashboard. 
                Your paswword is {userpsw}. You're required to change the password."""

    mail.send(msg)

def send_leave_email(employee, leave, status): #response to employee leave application
    subject = f"Leave Application {status}"
    recipient = employee.employee_email
    message = Message(subject, recipients=[recipient])
    message.body = f"""
        Hi {employee.employee_fname},
        
        Your leave application from {leave.start_date} to {leave.end_date} has been {status}.
        Leave Type: {leave.leave_type}
        Reason: {leave.reason}

        Thank you,
        HR/Admin Team
        """
    mail.send(message)


def login_required(f):
    @wraps(f)
    def login_decoration(*args,**kwargs):
        adminid = session.get('adminonline')
        if adminid:
            return f(*args,**kwargs)
        else:
            flash("You must be logged in to view the page", category='failed')
            return redirect(url_for('admin_login'))
    return login_decoration

@app.errorhandler(500)
def internal_server_error(error):
    return render_template("admin/500.html", error=error),500

@app.errorhandler(404)
def page_not_found(error):
    return render_template("admin/404.html", error=error),404

@app.route("/admin/login/",methods=['GET','POST'])
def admin_login():
    form = AdminLoginForm()
    
    if form.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')
        admindeets = Admin.query.filter(Admin.admin_username==username).first()
        if admindeets:
            hashed_pswd = admindeets.admin_pswd
            checkpass = check_password_hash(hashed_pswd,password)
            if checkpass:
                session['adminonline'] = admindeets.admin_id
                flash("Welcome!", category='success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Wrong password", category='error')
                return redirect("/admin/login/")
        else:
                flash("Enter correct username", category='error')
                return redirect("/admin/login/")
    else:
        return render_template('admin/login.html',loginform=form)
    

@app.route('/admin/dashboard/')
@login_required
def admin_dashboard():
    departments = Department.query.all()
    total_employees = db.session.query(Employee).filter_by(is_active=True).count()
    inactive_employees = db.session.query(Employee).filter_by(is_active=False).count()
    pending_leaves_count = Leave.query.filter_by(status='pending').count()
    designations = Designation.query.all()
    query = request.args.get('q')
  

    if query:
        employees = Employee.query.filter(
            (Employee.employee_fname.ilike(f"%{query}%")) |
            (Employee.employee_lname.ilike(f"%{query}%")) |
            (Employee.employee_email.ilike(f"%{query}%")) |
            (Employee.employee_file_No.ilike(f"%{query}%"))
        ).all()
    else:    
        employees = db.session.query(Employee).filter_by(is_active=True).all()
        # employees = Employee.query.filter_by(is_active=True)

        
    return render_template('admin/admin_dashboard.html',
                            employees=employees,total_employees=total_employees, designations=designations, 
                            departments=departments, pending_leaves_count=pending_leaves_count, inactive=inactive_employees)


@app.route('/add/employee/', methods=['POST'])
@login_required
def add_employee():
    fname = request.form.get('fname')
    lname = request.form.get('lname')
    email = request.form.get('email')
    fileno = request.form.get('fileno')
    degree = request.form.get('qualification')
    dob = request.form.get('dob')
    designation_id = request.form.get('designation_id')
    dept_id = request.form.get('dept')
    grade_level = request.form.get('grade_level')

    date_employed_str = request.form.get('dateEmployed')
    date_employed = datetime.strptime(date_employed_str, "%Y-%m-%d").date()
    promotion_due_date = calculate_promotion_date(date_employed)

    userpsw = str(datetime.utcnow())
    print(f"Temporary password for {fname} is: {userpsw}")
    hashed_pswd = generate_password_hash(str(datetime.utcnow()))  # Temp password
    
    existing = Employee.query.filter_by(employee_email=email).first()
    if existing:
        return "Email already exists"
    else:# Create new employee
        employee = Employee(
            employee_lname=lname,
            employee_fname=fname,
            employee_file_No=fileno,
            employee_email=email,
            employee_dob=dob,
            date_employed=date_employed,
            employee_loginpwd=hashed_pswd,
            qualification=degree,
            # current_designation_id=designation_id,
            promotion_due_date=promotion_due_date
        )
        db.session.add(employee)
        db.session.commit()
        # Create job history record
        job_history = JobHistory(
            employeeid=employee.employee_id,
            designation_id=designation_id,
            department_id=dept_id,
            grade_level=grade_level,
            start_date=date_employed
        )
        db.session.add(job_history)
        db.session.commit()

    # Notify employee
        send_email(fname,userpsw,email)
        return 'Employee Onboarding Successful.'

#edit employee datails route
@app.route('/employee/<int:id>/edit/', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    history = employee.job_history
    states = State.query.all()
    lgas=Lga.query.all()
    departments = Department.query.all()

    latest_job = history[-1]

    if request.method == 'POST':
        employee.employee_fname = request.form.get('fname')
        employee.employee_lname = request.form.get('lname')
        employee.employee_othername = request.form.get('othername')
        employee.employee_email = request.form.get('email')
        employee.employee_file_No = request.form.get('fileno')
        employee.qualification = request.form.get('qualification')
        employee.gender = request.form.get('gender')
        employee.stateof_originid = request.form.get('state')
        employee.station = request.form.get('lga')
        employee.phone = request.form.get('phone')
        employee.employee_dob = datetime.strptime(request.form.get('dob'), "%Y-%m-%d").date()
        employee.date_employed = datetime.strptime(request.form.get('dateEmployed'), "%Y-%m-%d").date()
        employee.promotion_due_date = calculate_promotion_date(employee.date_employed)
        
        latest_job.department_id=request.form.get('dept') #update department in job_history

        db.session.commit()
        flash("Employee record updated.", category='success')
        return redirect(url_for('admin_dashboard'))

    return render_template("admin/edit_employee.html", employee=employee, states=states,lgas=lgas,
                            latest_job=latest_job, departments=departments)


@app.route('/get_lgas', methods=['POST'])
def get_lgas():
    state_id = request.form.get('state')
    if not state_id:
        return '<option value="">Select LGA</option>'
    
    lgas = Lga.query.filter_by(state_id=state_id).all()
    options = '<option value="">Select LGA</option>'
    for lga in lgas:
        options += f'<option value="{lga.lga_id}">{lga.lga_name}</option>'
    
    return options


@app.route('/employee/<int:id>/view/', methods=['GET', 'POST'])
@login_required
def view_employee(id):
    employee = Employee.query.get_or_404(id)
    job_history = employee.job_history
    lgas=Lga.query.all()

    # Get the current grade_level and step from the latest job history entry
    if job_history:
        latest_job = job_history[-1]

    return render_template("admin/view_employee.html", employee=employee,latest_job=latest_job,lgas=lgas)


@app.route('/employee/<int:employee_id>/offboard', methods=['POST'])
def offboard_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    employee.is_active = False
    db.session.commit()
    flash('Employee has been offboarded.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route("/promotion/list/")
@login_required
def promotion_list():
    # Get current year from query parameter or default to current year
    year = request.args.get('year', datetime.now().year, type=int)

    # Get all employees due for promotion in that year
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)

    employees_due = Employee.query.filter(
        Employee.promotion_due_date >= start_date,
        Employee.promotion_due_date <= end_date
    ).all()

    return render_template("admin/promotion_list.html", employees_due=employees_due, year=year)


@app.route("/promote/employee/", methods=["POST","GET"])
@login_required
def promote_employee():
    if request.method == "POST":
        email = request.form.get('email')
        designation_id = request.form.get('designation_id')
        grade_level = int(request.form.get('grade_level'))
        step = int(request.form.get('step'))  
        date_promoted = datetime.strptime(request.form.get('date_promoted'), '%Y-%m-%d')

        employee = Employee.query.filter_by(employee_email=email).first()
        if not employee:
            flash("Employee not found", category='failed')
            return redirect(url_for('admin_dashboard'))

        # Create Promotion record
        promotion = Promotion(
            employee_id=employee.employee_id,
            new_designation_id=designation_id,
            newgrade_level=grade_level,
            new_step=step,
            date_promoted=date_promoted
        )
        db.session.add(promotion)
        # Update promotion_due_date
        employee.promotion_due_date = date_promoted + timedelta(days=3 * 365)

        # update designation on employee table
        # employee.current_designation_id = designation_id

        # END the previous job history entry if it exists
        last_job = JobHistory.query.filter_by(employeeid=employee.employee_id).order_by(JobHistory.start_date.desc()).first()
        if last_job:
            last_job.end_date = date_promoted

        # Create new JobHistory entry
        department_id = request.form.get('dept_id')
        role_id = request.form.get('role_id')
        salary_id = request.form.get('salary_id')

        new_history = JobHistory(
            employeeid=employee.employee_id,
            designation_id=designation_id,
            grade_level=grade_level,
            step=step,
            department_id=department_id,
            role_id=role_id,
            employee_salaryid=salary_id,
            start_date=date_promoted
        )
        db.session.add(new_history)

        db.session.commit()
        flash("Employee promoted and job history updated successfully")
        return redirect(url_for('admin_dashboard'))
    else:
        designations = Designation.query.all()
        departments = Department.query.all()
        return render_template("admin/promote_employee.html", designations=designations, departments=departments)


@app.route("/view/<int:id>/jobhistory")
@login_required
def job_history(id):
    employee = Employee.query.get_or_404(id)
    job_history = employee.job_history
    return render_template("admin/job_history.html", job_history=job_history, employee=employee)



@app.route('/view/leave_applications')
@login_required
def leave_applications():
    all_leaves = Leave.query.order_by(Leave.start_date.desc()).all()
    return render_template('admin/leave_applications.html', leaves=all_leaves)


@app.route('/leave/<int:leave_id>/approve')
@login_required
def approve_leave(leave_id):
    leave = Leave.query.get_or_404(leave_id)
    leave.status = 'Approved'
    db.session.commit()
    send_leave_email(leave.employee, leave, 'approved')
    flash('Leave approved and email sent.', 'success')
    return redirect(url_for('leave_applications'))


@app.route('/leave/<int:leave_id>/reject')
@login_required
def reject_leave(leave_id):
    leave = Leave.query.get_or_404(leave_id)
    leave.status = 'Rejected'
    db.session.commit()
    send_leave_email(leave.employee, leave, 'rejected')
    flash('Leave rejected and email sent.', category='failed')
    return redirect(url_for('leave_applications'))


@app.route("/admin/logout/")
def admin_logout():
    session.pop('adminonline',None)
    return redirect(url_for('portal'))

