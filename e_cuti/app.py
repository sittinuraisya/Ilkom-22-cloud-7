import os, logging, random, string
from pathlib import Path
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, g, redirect, url_for
from flask_migrate import Migrate
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix

from extensions import db, mail, migrate, login_manager, limiter

# Load environment variables
load_dotenv()


def create_app(config_class='config.Config'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Load configuration
    app.config.from_object(config_class)

    from config import Config
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    limiter.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.session_protection = "strong"
    login_manager.remember_cookie_duration = timedelta(days=30)  # Cookie berlaku 30 hari
    login_manager.refresh_view = 'auth.login'  # View untuk refresh login
    login_manager.needs_refresh_message = (u"Session expired, please re-login")
    login_manager.needs_refresh_message_category = "info"
    
    # Setup database
    with app.app_context():
        from models import User, Cuti, AuditLog, LoginLog
        try:
            db.create_all()
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    register_blueprints(app)

    # Register template filters and context
    app.template_filter('format_date')(format_date)
    app.template_filter('format_datetime')(format_datetime)
    app.template_filter('random_string')(random_string)
    app.context_processor(inject_globals)
    app.context_processor(lambda: dict(os=os))

    return app


def register_blueprints(app):
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.atasan import atasan_bp
    from routes.pegawai import pegawai_bp
    from routes.common import common_bp
    from routes.cuti import cuti_bp
    from routes.profile import profile_bp

    blueprints = [
        (auth_bp, None),
        (admin_bp, '/admin'),
        (atasan_bp, '/atasan'),
        (pegawai_bp, '/pegawai'),
        (common_bp, '/common'),
        (cuti_bp, '/cuti'),
        (profile_bp, '/profile')
    ]

    for bp, url_prefix in blueprints:
        app.register_blueprint(bp, url_prefix=url_prefix)


def inject_os():
    return dict(os=os)


def format_date(value, format='%d-%m-%Y'):
    """Template filter for date formatting"""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value
    return value.strftime(format) if value else ''


def format_datetime(value, format='%d %b %Y %H:%M'):
    if value is None:
        return ''
    return value.strftime(format)


def random_string(length=8):
    """Generate random string for unique IDs if needed"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def inject_globals():
    """Inject global variables to templates"""
    from models import UserRole, JenisCuti, CutiStatus
    return {
        'UserRole': UserRole,
        'JenisCuti': JenisCuti,
        'CutiStatus': CutiStatus,
        'current_year': datetime.now().year,
        'now': datetime.now(),
        'app_name': os.getenv('APP_NAME', 'E-Cuti: Sistem Digitalisasi Pengelolaan Cuti Pegawai'),
        'organization': os.getenv('ORGANIZATION', 'Biro Organisasi Setda Prov. Sultra'),
    }


# Create the app instance
app = create_app()


@app.route('/')
def root_redirect():
    """Redirect root URL to login page"""
    return redirect(url_for('auth.login'))


if __name__ == '__main__':
    ssl_context = 'adhoc' if os.getenv('FLASK_ENV') == 'development' else None
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'False').lower() in ['true', '1', 't'],
        ssl_context=ssl_context
    )
