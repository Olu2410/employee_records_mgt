from flask import Flask
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_mail import Mail


mail = Mail()
csrf = CSRFProtect()
def create_app(): 
    from mypackage.models import db
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_pyfile("config.py")

    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    migrate = Migrate(app,db)
    return app

app = create_app()


from mypackage import forms, employee_routes,admin_routes
