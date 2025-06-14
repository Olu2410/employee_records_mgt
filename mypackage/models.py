from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Admin(db.Model):
    admin_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_username = db.Column(db.String(50),nullable=False)
    admin_pswd = db.Column(db.String(200),nullable=False)

class Employee(db.Model):
    employee_id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    employee_file_No = db.Column(db.String(100))
    employee_lname = db.Column(db.String(100),nullable=False)
    employee_fname = db.Column(db.String(100),nullable=False)
    employee_othername = db.Column(db.String(100))
    employee_dob = db.Column(db.Date,nullable=False)
    employee_email = db.Column(db.String(100),nullable=False,unique=True)
    phone = db.Column(db.String(50))
    gender = db.Column(db.Enum('male','female'))
    date_employed = db.Column(db.Date, nullable=False)
    qualification = db.Column(db.Enum('phd','msc','bsc'))
    station = db.Column(db.Integer, db.ForeignKey('lga.lga_id')) #place of primary assignment
    promotion_due_date = db.Column(db.Date)
    stateof_originid = db.Column(db.Integer, db.ForeignKey('state.state_id'))
    usergroup_id = db.Column(db.Integer, db.ForeignKey('usergroup.usergroup_id'))
    employee_dp = db.Column(db.String(100))
    employee_loginpwd = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)

    state = db.relationship("State", backref="employee_origin")
    assigned_lga = db.relationship("Lga", backref="employees")
    promotions = db.relationship("Promotion", back_populates="employee")  # Relationship to Promotion
    job_history = db.relationship("JobHistory", back_populates="employee")

    def __repr__(self):
            return f"<Employee {self.employee_fname} - {self.employee_email}>"


class Promotion(db.Model):
    __tablename__ = 'promotion'
    promotion_id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.employee_id'), nullable=False)
    new_designation_id = db.Column(db.Integer, db.ForeignKey('designation.designation_id'), nullable=False)
    newgrade_level = db.Column(db.Integer, nullable=False)
    new_step = db.Column(db.Integer)
    date_promoted = db.Column(db.Date, nullable=False)
    
    new_designation = db.relationship("Designation",backref="promotion") #relationship to designation
    employee = db.relationship("Employee", back_populates="promotions")


class Designation(db.Model):
    designation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    designation = db.Column(db.String(100))


class Department(db.Model):
    __tablename__ = 'departments'
    dept_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    department = db.Column(db.String(200))


class Leave(db.Model):
    leave_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.employee_id'))
    leave_type = db.Column(db.String(100)) 
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    reason = db.Column(db.Text)
    status = db.Column(db.Enum('Pending', 'Approved', 'Rejected'), default='Pending')

    employee = db.relationship('Employee', backref='leaves')


class State(db.Model):
    state_id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    state_name = db.Column(db.String(80),nullable=False)

    def __repr__(self):
        return f"{self.state_id}"


class Lga(db.Model):
    __tablename__ = 'lga'
    lga_id = db.Column(db.Integer,primary_key=True, autoincrement=True)
    state_id = db.Column(db.Integer,db.ForeignKey('state.state_id'),nullable=False)
    lga_name = db.Column(db.String(50),nullable=False)

    state = db.relationship("State", backref="lgas")


class JobHistory(db.Model):
    __tablename__ = 'job_history'
    job_historyid = db.Column(db.Integer,primary_key=True,autoincrement=True)
    employeeid = db.Column(db.Integer, db.ForeignKey('employee.employee_id'), nullable=False)
    designation_id = db.Column(db.Integer, db.ForeignKey('designation.designation_id'), nullable=False)
    grade_level = db.Column(db.Integer, nullable=False)
    step = db.Column(db.Integer)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.dept_id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.role_id'))
    employee_salaryid = db.Column(db.Integer, db.ForeignKey('salary.salary_id'))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)

    employee = db.relationship("Employee", back_populates="job_history") # Relationship to Employee
    designation = db.relationship("Designation",backref='job_history') #relationship to designation
    department = db.relationship("Department", backref='job_history') #relationship to department
    role = db.relationship("Role",backref="job_history") #relationship to Role
    salary = db.relationship("Salary", backref='job_history') #relationship to salary


class Usergroup(db.Model):
    usergroup_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usergroup = db.Column(db.Enum('admin','user'))

class Role(db.Model):
    role_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role = db.Column(db.String(100))
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.employee_id'))


class Salary(db.Model):
    salary_id = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    salary_amount = db.Column(db.Float)