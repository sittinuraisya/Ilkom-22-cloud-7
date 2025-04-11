from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

app = Flask(__name__)
app.config.from_object('config.Config')
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
mail = Mail(app)

from app.routes import auth, leave, admin, supervisor
app.register_blueprint(auth.bp)
app.register_blueprint(leave.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(supervisor.bp)