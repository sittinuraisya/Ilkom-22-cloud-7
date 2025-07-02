from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)

from flask.json.provider import DefaultJSONProvider
from datetime import datetime, date
from decimal import Decimal

class CustomJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        if hasattr(o, '__html__'):
            return str(o.__html__())
        return super().default(o)