import os, re, secrets, string, logging, csv, click
from datetime import datetime, timedelta, time
from functools import wraps
from io import BytesIO, StringIO
from pathlib import Path
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, make_response, jsonify, current_app, Response
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func, extract
from itsdangerous import URLSafeTimedSerializer
from fpdf import FPDF
from .extensions import db
from models import User, LoginLog, Cuti, AuditLog, Notification, UserRole, CutiStatus

import pandas as pd

# Load environment variables
load_dotenv()

# Initialize extensions
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()

# Create Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

# Configure paths and database
instance_path = Path(__file__).parent / "instance"
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{instance_path / 'app.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions with app
from extensions import db
db.init_app(app)
migrate.init_app(app, db)
mail.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Import models after db initialization
with app.app_context():
    from models import User, Cuti, AuditLog, Notification, LoginLog
    try:
        db.create_all()
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"SECRET_KEY loaded: {app.config['SECRET_KEY']}")
logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Initialize token serializer
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Import services
from services.Api_GoogleCalendar import GoogleCalendarService
from services.Api_Slack import SlackService

# Import blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.atasan import atasan_bp
from routes.pegawai import pegawai_bp
from routes.common import common_bp

# Register dengan URL prefix
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(atasan_bp, url_prefix='/atasan')
app.register_blueprint(pegawai_bp, url_prefix='/pegawai')
app.register_blueprint(common_bp)

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Template filter
@app.template_filter('format_date')
def format_date(value, format='%d-%m-%Y'):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value
    return value.strftime(format) if value else value

# === Role-based access decorator ===
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash('Anda tidak memiliki akses ke halaman ini', 'error')
                return redirect(url_for('unauthorized'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ====================== RUTE AUTHENTIKASI ======================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_to_dashboard(current_user.role)

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Validasi input
        if not username or not password:
            flash('Username dan password harus diisi', 'error')
            return render_template('auth/login.html')

        user = User.query.filter(
            (func.lower(User.username) == func.lower(username)) | 
            (func.lower(User.email) == func.lower(username)
        ).first()

        # Cek user dan password
        if not user or not check_password_hash(user.password, password):
            # Log login attempt
            logging.warning(f'Failed login attempt for username: {username}')
            flash('Username/email atau password salah', 'error')
            return render_template('auth/login.html')

        # Cek akun terkunci
        if user.locked_until and user.locked_until > datetime.utcnow():
            remaining_time = user.locked_until - datetime.utcnow()
            flash(f'Akun terkunci. Coba lagi dalam {int(remaining_time.total_seconds() / 60)} menit', 'error')
            return render_template('auth/login.html')

        # Cek verifikasi email
        if not user.email_verified:
            flash('Email belum diverifikasi. Silakan cek email Anda', 'warning')
            return render_template('auth/login.html')

        # Reset failed attempts setelah login sukses
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        db.session.commit()

        login_user(user)
        flash('Login berhasil', 'success')
        
        # Redirect berdasarkan role
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect_to_dashboard(user.role)

    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Get form data with proper sanitization
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        
        # Set default role to 'pegawai' dan validasi
        role = UserRole.PEGAWAI.value

        # Validasi input
        errors = validate_registration_form(username, email, password, confirm_password, full_name)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html', 
                                username=username,
                                email=email,
                                full_name=full_name)

        # Cek user/email sudah ada
        if User.query.filter(
            (func.lower(User.username) == func.lower(username)) | 
            (func.lower(User.email) == func.lower(email))
        ).first():
            flash('Username atau email sudah terdaftar', 'error')
            return render_template('auth/register.html',
                                username=username,
                                email=email,
                                full_name=full_name)

        try:
            # Buat user baru
            new_user = User(
                username=username,
                email=email,
                password=generate_password_hash(password, method='pbkdf2:sha256'),
                role=role,
                full_name=full_name,
                email_verified=False,
                created_at=datetime.utcnow(),
                last_password_change=datetime.utcnow()
            )

            db.session.add(new_user)
            db.session.commit()

            # Kirim email verifikasi
            send_verification_email(new_user)
            
            flash('Registrasi berhasil! Silakan cek email untuk verifikasi', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Registration error: {str(e)}", exc_info=True)
            flash('Terjadi kesalahan saat registrasi', 'error')
            return render_template('auth/register.html',
                                username=username,
                                email=email,
                                full_name=full_name)

    return render_template('auth/register.html')


def validate_registration_form(username, email, password, confirm_password, full_name):
    """Validasi form registrasi"""
    errors = []
    
    if not all([username, email, password, confirm_password, full_name]):
        errors.append('Semua field harus diisi')
    
    if len(username) < 4 or len(username) > 20:
        errors.append('Username harus antara 4-20 karakter')
        
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors.append('Username hanya boleh mengandung huruf, angka, dan underscore')
        
    if not is_valid_email(email):
        errors.append('Format email tidak valid')
        
    if len(password) < 8:
        errors.append('Password minimal 8 karakter')
    elif not any(char.isdigit() for char in password):
        errors.append('Password harus mengandung angka')
    elif not any(char.isupper() for char in password):
        errors.append('Password harus mengandung huruf besar')
        
    if password != confirm_password:
        errors.append('Password dan konfirmasi password tidak cocok')
        
    if len(full_name.split()) < 2:
        errors.append('Nama lengkap minimal 2 kata')
        
    return errors


def send_verification_email(user):
    """Kirim email verifikasi"""
    try:
        token = generate_verification_token(user.email)
        verify_url = url_for('verify_email', token=token, _external=True)
        
        msg = Message(
            subject='Verifikasi Email Anda',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email],
            html=render_template('email/verification.html',
                               username=user.username,
                               verify_url=verify_url,
                               app_name=app.config['APP_NAME'])
        )
        
        mail.send(msg)
        logging.info(f"Verification email sent to {user.email}")
    except Exception as e:
        logging.error(f"Failed to send verification email to {user.email}: {str(e)}")
        raise


@app.route('/verify-email/<token>')
def verify_email(token):
    if current_user.is_authenticated and current_user.email_verified:
        return redirect_to_dashboard(current_user.role)

    try:
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = serializer.loads(token, salt='email-verify', max_age=86400)  # 24 jam expiry
    except:
        flash('Link verifikasi tidak valid atau sudah kadaluarsa', 'error')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first_or_404()
    
    if user.email_verified:
        flash('Email sudah diverifikasi sebelumnya', 'info')
    else:
        user.email_verified = True
        user.verified_at = datetime.utcnow()
        db.session.commit()
        flash('Email berhasil diverifikasi! Silakan login', 'success')
    
    if current_user.is_authenticated:
        return redirect_to_dashboard(current_user.role)
    return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    # Log aktivitas logout
    logging.info(f"User {current_user.username} logged out")
    logout_user()
    flash('Anda telah logout', 'info')
    return redirect(url_for('login'))


def redirect_to_dashboard(role):
    """Redirect user ke dashboard berdasarkan role"""
    if role == UserRole.ADMIN.value:
        return redirect(url_for('admin.dashboard'))
    elif role == UserRole.ATASAN.value:
        return redirect(url_for('atasan.dashboard'))
    elif role == UserRole.SUPERADMIN.value:
        return redirect(url_for('superadmin.dashboard'))
    else:
        return redirect(url_for('pegawai.dashboard'))
        
# ====================== RUTE LUPA PASSWORD & RESET ======================
@app.route('/lupa-password', methods=['GET', 'POST'])
def lupa_password():
    if current_user.is_authenticated:
        return redirect_to_dashboard(current_user.role)

    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            try:
                token = generate_reset_token(user.email)
                reset_link = url_for('reset_password', token=token, _external=True)
                
                # Kirim email
                msg = Message(
                    'Reset Password E-Cuti',
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[user.email]
                )
                msg.body = f'''Silakan reset password Anda dengan mengklik link berikut:
{reset_link}

Link akan kadaluarsa dalam 1 jam.

Jika Anda tidak meminta reset password, abaikan email ini.
'''
                mail.send(msg)
                
                flash('Link reset password telah dikirim ke email Anda', 'success')
            except Exception as e:
                app.logger.error(f"Error sending reset email: {str(e)}")
                flash('Gagal mengirim email reset password', 'error')
        else:
            flash('Email tidak terdaftar', 'error')

    return render_template('auth/lupa_password.html')

def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect_to_dashboard(current_user.role)

    try:
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = serializer.loads(token, salt='password-reset', max_age=3600)
    except:
        flash('Link reset password tidak valid atau sudah kadaluarsa', 'error')
        return redirect(url_for('lupa_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User tidak ditemukan', 'error')
        return redirect(url_for('lupa_password'))

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Password dan konfirmasi password tidak cocok', 'error')
            return redirect(url_for('reset_password', token=token))

        try:
            user.password = generate_password_hash(password)
            db.session.commit()
            flash('Password berhasil direset. Silakan login dengan password baru.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error resetting password: {str(e)}")
            flash('Gagal reset password', 'error')

    return render_template('auth/reset_password.html', token=token)

# ====================== RUTE EMAIL NOTIFIKASI ======================
@app.route('/send-email', methods=['POST'])
@login_required
def send_email_api():
    data = request.get_json()
    try:
        msg = Message(
            subject=data.get('subject', 'Notifikasi Cuti'),
            sender=app.config['MAIL_USERNAME'],
            recipients=[data['email']]
        )
        msg.html = render_template(
            'emails/notification.html',
            type=data['type'],
            user=current_user,
            data=data.get('data', {})
        )
        mail.send(msg)
        return jsonify(success=True)
    except Exception as e:
        app.logger.error(f"Error sending email: {str(e)}")
        return jsonify(success=False, error=str(e))

# ====================== RUTE RESEND VERIFIKASI ======================
@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('Email tidak terdaftar', 'error')
    elif user.email_verified:
        flash('Email sudah terverifikasi', 'info')
    else:
        try:
            send_verification_email(user)
            flash('Email verifikasi telah dikirim ulang', 'success')
        except Exception as e:
            app.logger.error(f"Error resending verification: {str(e)}")
            flash('Gagal mengirim email verifikasi', 'error')
    
    return redirect(url_for('login'))

# ====================== RUTE DASHBOARD ======================
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    return redirect_to_dashboard(current_user.role)
/"AQ    12"

@app.context_processor
def inject_system_info():
    return {
        'app_name': app.config['APP_NAME'],
        'organization': app.config['ORGANIZATION'],
        'now': datetime.now()
    }

# ====================== RUTE SUPERADMIN =====================
@app.cli.command("create-superadmin")
@click.argument("username")
@click.argument("email")
@click.argument("password")
def create_superadmin(username, email, password):
    """Membuat akun superadmin baru"""
    from app import db
    from models import User
    
    # Cek apakah superadmin sudah ada
    if User.query.filter_by(role='superadmin').first():
        print("Superadmin sudah ada!")
        return

    # Buat user baru
    superadmin = User(
        username=username,
        email=email,
        password=generate_password_hash(password, method='pbkdf2:sha256'),
        role='superadmin',
        email_verified=True,
        jabatan='Super Administrator'
    )
    
    db.session.add(superadmin)
    db.session.commit()
    print(f"Superadmin {username} berhasil dibuat!")

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'superadmin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
    
@app.route('/superadmin/dashboard')
@login_required
@role_required(['superadmin'])
def superadmin_dashboard():
    # Statistik admin
    total_admin = User.query.filter_by(role='admin').count()

    # Statistik atasan dan pegawai
    total_atasan = User.query.filter_by(role='atasan').count()
    total_pegawai = User.query.filter_by(role='pegawai').count()

    # Audit logs (misalnya mengambil 10 log terbaru)
    audit_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()

    # Notifikasi (misalnya mengambil 5 notifikasi terbaru)
    notifications = Notification.query.order_by(Notification.created_at.desc()).limit(5).all()

    # Render template dengan data lengkap
    return render_template("superadmin/dashboard.html", 
        total_admin=total_admin,
        total_atasan=total_atasan,
        total_pegawai=total_pegawai,
        audit_logs=audit_logs,
        notifications=notifications)

@app.template_filter('format_date')
def format_date(value, format='%d-%m-%Y'):
    try:
        if isinstance(value, str):
            value = datetime.strptime(value, '%Y-%m-%d')
        return value.strftime(format)
    except:
        return value

@app.route('/superadmin/manajemen-admin', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin'])
def manajemen_admin():
    if request.method == 'POST':
        try:
            # Mengambil data dari form
            username = request.form['username']
            email = request.form['email']
            password = generate_password_hash(request.form['password'])

            # Cek apakah email sudah ada di database
            existing_admin = User.query.filter_by(email=email).first()
            if existing_admin:
                flash('Email sudah terdaftar', 'error')
                return redirect(url_for('manajemen_admin'))

            # Menambah admin baru ke database
            new_admin = User(
                username=username,
                email=email,
                password=password,
                role='admin'
            )

            db.session.add(new_admin)
            db.session.commit()

            flash('Admin berhasil ditambahkan', 'success')
            return redirect(url_for('manajemen_admin'))

        except Exception as e:
            # Menggunakan rollback jika terjadi error
            db.session.rollback()
            app.logger.error(f"Error adding admin: {str(e)}")
            flash('Gagal menambahkan admin', 'error')

    # Menampilkan daftar admin yang ada
    admins = User.query.filter_by(role='admin').all()
    return render_template('superadmin/manajemen_admin.html', admins=admins)

@app.route('/superadmin/edit-admin/<int:admin_id>', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin'])
def superadmin_edit_user(admin_id):
    user = User.query.get_or_404(admin_id)  
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.role = request.form['role']
        
        db.session.commit()
        flash('Admin berhasil diupdate', 'success')
        return redirect(url_for('superadmin_dashboard'))
    
    return render_template('superadmin/edit_user.html', user=user)

@app.route('/superadmin/delete-admin/<int:admin_id>', methods=['POST', 'GET'])
@login_required
@role_required(['superadmin'])
def superadmin_delete_user(admin_id):
    user = User.query.get_or_404(admin_id)  # Sesuaikan parameter dengan admin_id
    db.session.delete(user)
    db.session.commit()
    flash('Admin berhasil dihapus', 'success')
    return redirect(url_for('superadmin_dashboard'))


@app.route('/superadmin/audit-log')
@login_required
@role_required(['superadmin'])
def audit_log():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).all()
    return render_template('superadmin/audit_log.html', logs=logs)

@app.route('/superadmin/export-users')
@login_required
@role_required(['superadmin'])
def export_users():
    users = User.query.all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Username', 'Email', 'Role'])
    for user in users:
        writer.writerow([user.id, user.username, user.email, user.role])
    
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={
        'Content-Disposition': 'attachment;filename=users.csv'
    })

@app.route('/superadmin/notifications')
@login_required
@role_required(['superadmin'])
def notifications():
    notifications = Notification.query.filter_by(seen=0).all()
    return render_template('superadmin/notifications.html', notifications=notifications)


# ====================== RUTE ADMIN ======================
@app.route('/admin/dashboard')
@login_required
@role_required(['admin'])
def admin_dashboard():
    # Statistik pengguna
    total_pegawai = User.query.filter_by(role='pegawai').count()
    total_atasan = User.query.filter_by(role='atasan').count()
    
    # Statistik cuti
    cuti_pending = Cuti.query.filter_by(status='Pending').count()
    cuti_approved = Cuti.query.filter_by(status='Approved').count()
    
    # Menyusun stats menjadi satu dictionary
    stats = {
        'total_pegawai': total_pegawai,
        'total_atasan': total_atasan,
        'cuti_pending': cuti_pending,
        'cuti_approved': cuti_approved
    }
    
    # Mengirimkan stats ke template
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/manajemen-atasan', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'superadmin'])
def manajemen_atasan():
    if request.method == 'POST':
        try:
            # Ambil data dari form
            username = request.form['username']
            email = request.form['email']
            password = generate_password_hash(request.form['password'])
            
            # Membuat objek atasan baru
            new_atasan = User(
                username=username,
                email=email,
                password=password,
                role='atasan'
            )
            
            # Menambahkan atasan ke database
            db.session.add(new_atasan)
            db.session.commit()
            
            flash('Atasan berhasil ditambahkan', 'success')
        except Exception as e:
            db.session.rollback()  # Rollback jika ada error
            app.logger.error(f"Error adding atasan: {str(e)}")
            flash('Gagal menambahkan atasan', 'error')
    
    # Mengambil daftar atasan dan pegawai dari database
    atasans = User.query.filter_by(role='atasan').all()
    pegawai_list = User.query.filter_by(role='pegawai').all()
    
    # Merender template dengan data atasan dan pegawai
    return render_template('admin/manajemen_atasan.html', atasans=atasans, pegawai_list=pegawai_list)

@app.route('/admin/manajemen-pegawai')
@login_required
@role_required(['admin', 'superadmin'])
def manajemen_pegawai():
    pegawai_list = User.query.filter_by(role='pegawai').all()
    atasans = User.query.filter_by(role='atasan').all()
    return render_template('admin/manajemen_pegawai.html', 
                         pegawai_list=pegawai_list,
                         atasans=atasans)

@app.route('/admin/manajemen-user')
@login_required
@role_required(['admin', 'superadmin'])
def manajemen_user():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) | 
            (User.email.ilike(f'%{search}%')) |
            (User.jabatan.ilike(f'%{search}%')))
    
    users = query.order_by(User.username).paginate(page=page, per_page=per_page)
    
    return render_template('admin/manajemen_user.html', 
                         users=users,
                         search=search)

@app.route('/admin/reset-password-atasan/<int:atasan_id>', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def reset_password_atasan(atasan_id):
    atasan = User.query.get_or_404(atasan_id)
    new_password = request.form.get('new_password')
    
    if not new_password:
        flash('Password baru harus diisi', 'error')
        return redirect(url_for('edit_atasan', atasan_id=atasan_id))
    
    try:
        atasan.password = generate_password_hash(new_password)
        atasan.must_change_password = True
        db.session.commit()
        flash('Password atasan berhasil direset', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error resetting password: {str(e)}")
        flash('Gagal mereset password', 'error')
    
    return redirect(url_for('edit_atasan', atasan_id=atasan_id))

from werkzeug.security import generate_password_hash

# Route untuk tambah atasan
@app.route('/admin/tambah-atasan', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'superadmin'])
def tambah_atasan():
    if request.method == 'POST':
        # Ambil data dari form
        nip = request.form.get('nip', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        jabatan = request.form.get('jabatan', '').strip()
        golongan = request.form.get('golongan', '').strip()
        
        # Validasi field wajib
        if not all([nip, username, email, password, jabatan]):
            flash('Semua field wajib harus diisi', 'error')
            return redirect(url_for('tambah_atasan'))
        
        # Validasi format email
        if '@' not in email or '.' not in email.split('@')[1]:
            flash('Format email tidak valid', 'error')
            return redirect(url_for('tambah_atasan'))
        
        try:
            # Cek duplikasi menggunakan filter()
            existing_nip = User.query.filter_by(nip=nip).first()
            existing_username = User.query.filter_by(username=username).first()
            existing_email = User.query.filter_by(email=email).first()
            
            if existing_nip:
                flash('NIP sudah terdaftar', 'error')
                return redirect(url_for('tambah_atasan'))
            if existing_username:
                flash('Username sudah terdaftar', 'error')
                return redirect(url_for('tambah_atasan'))
            if existing_email:
                flash('Email sudah terdaftar', 'error')
                return redirect(url_for('tambah_atasan'))
            
            # Enkripsi password
            hashed_password = generate_password_hash(password)
            
            # Buat user baru
            new_atasan = User(
                nip=nip,
                username=username,
                email=email,
                password=hashed_password,  # Simpan password yang sudah dienkripsi
                jabatan=jabatan,
                golongan=golongan,
                role='atasan',
                email_verified=True  # Asumsi admin verifikasi langsung
            )
            
            db.session.add(new_atasan)
            db.session.commit()
            
            flash('Atasan baru berhasil ditambahkan', 'success')
            return redirect(url_for('manajemen_atasan'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Gagal tambah atasan: {str(e)}")
            flash('Gagal menambahkan atasan. Silakan coba lagi.', 'error')
    
    # GET request - tampilkan form
    return render_template('admin/tambah_atasan.html')

# Route untuk set atasan ke pegawai
@app.route('/admin/set-atasan/<int:pegawai_id>', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def set_atasan(pegawai_id):
    # Gunakan filter() bukan get()
    pegawai = User.query.filter_by(id=pegawai_id).first_or_404()
    atasan_id = request.form.get('atasan_id')
    
    if not atasan_id:
        flash('Atasan tidak dipilih', 'error')
        return redirect(url_for('manajemen_pegawai'))
    
    try:
        # Validasi atasan menggunakan filter()
        atasan = User.query.filter_by(id=atasan_id, role='atasan').first()
        if not atasan:
            flash('Atasan tidak valid', 'error')
            return redirect(url_for('manajemen_pegawai'))
        
        if str(atasan.id) == str(pegawai.id):
            flash('Tidak bisa memilih diri sendiri sebagai atasan', 'error')
            return redirect(url_for('manajemen_pegawai'))
        
        pegawai.atasan_id = atasan.id
        db.session.commit()
        
        flash(f'Atasan untuk {pegawai.username} berhasil ditetapkan', 'success')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Gagal set atasan: {str(e)}")
        flash('Gagal menetapkan atasan', 'error')
    
    return redirect(url_for('manajemen_pegawai'))

# Route untuk edit atasan
@app.route('/admin/edit-atasan/<int:atasan_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'superadmin'])
def edit_atasan(atasan_id):
    atasan = User.query.get_or_404(atasan_id)
    
    if request.method == 'POST':
        # Handle form submission
        atasan.nip = request.form.get('nip')
        atasan.username = request.form.get('username')
        atasan.email = request.form.get('email')
        atasan.jabatan = request.form.get('jabatan')
        atasan.golongan = request.form.get('golongan')
        
        # Validasi input
        if not all([atasan.nip, atasan.username, atasan.email, atasan.jabatan]):
            flash('Semua field wajib harus diisi', 'error')
            return redirect(url_for('edit_atasan', atasan_id=atasan_id))
        
        try:
            # Cek duplikasi NIP, username, dan email (kecuali untuk diri sendiri)
            existing = User.query.filter(
                (User.id != atasan_id) & 
                ((User.nip == atasan.nip) | (User.username == atasan.username) | (User.email == atasan.email))
            ).first()
            
            if existing:
                flash('NIP, username, atau email sudah terdaftar', 'error')
                return redirect(url_for('edit_atasan', atasan_id=atasan_id))
            
            db.session.commit()
            flash('Data atasan berhasil diperbarui', 'success')
            return redirect(url_for('manajemen_atasan'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating superior: {str(e)}")
            flash('Gagal memperbarui data atasan', 'error')
    
    # GET request - tampilkan form edit
    return render_template('admin/edit_atasan.html', atasan=atasan)

@app.route('/admin/hapus-atasan/<int:atasan_id>')
@login_required
@role_required(['admin', 'superadmin'])
def hapus_atasan(atasan_id):
    atasan = User.query.get_or_404(atasan_id)
    try:
        # Cek apakah atasan memiliki bawahan
        if atasan.subordinates:
            flash('Tidak bisa menghapus atasan yang masih memiliki bawahan', 'error')
            return redirect(url_for('manajemen_atasan'))
        
        db.session.delete(atasan)
        db.session.commit()
        flash('Atasan berhasil dihapus', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting superior: {str(e)}")
        flash('Gagal menghapus atasan', 'error')
    
    return redirect(url_for('manajemen_atasan'))

@app.route('/admin/laporan-cuti')
@login_required
@role_required(['admin', 'superadmin'])
def laporan_cuti():
    # Filter parameters
    tahun = request.args.get('tahun', datetime.now().year, type=int)
    bulan = request.args.get('bulan', type=int)
    status = request.args.get('status')
    jenis_cuti = request.args.get('jenis_cuti')
    
    # Base query
    query = db.session.query(Cuti, User).join(User, Cuti.user_id == User.id)
    
    # Apply filters
    if bulan:
        query = query.filter(db.extract('month', Cuti.tanggal_mulai) == bulan)
    query = query.filter(db.extract('year', Cuti.tanggal_mulai) == tahun)
    
    if status:
        query = query.filter(Cuti.status == status)
    if jenis_cuti:
        query = query.filter(Cuti.jenis_cuti == jenis_cuti)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10
    results = query.order_by(Cuti.tanggal_mulai.desc()).paginate(page=page, per_page=per_page)
    
    # Format data
    cuti_list = [{
        'id': cuti.id,
        'username': user.username,
        'nip': user.nip,
        'jenis_cuti': cuti.jenis_cuti,
        'tanggal_mulai': cuti.tanggal_mulai,
        'tanggal_selesai': cuti.tanggal_selesai,
        'jumlah_hari': cuti.jumlah_hari,
        'status': cuti.status,
        'created_at': cuti.created_at
    } for cuti, user in results.items]
    
    # Get filter options
    tahun_options = sorted(
        [y[0] for y in db.session.query(db.extract('year', Cuti.tanggal_mulai)).distinct().all()],
        reverse=True
    )
    
    return render_template(
        'admin/laporan_cuti.html',
        cuti_list=cuti_list,
        page=page,
        total_pages=results.pages,
        tahun=tahun,
        bulan=bulan,
        status=status,
        jenis_cuti=jenis_cuti,
        tahun_options=tahun_options
    )
    
@app.route('/admin/cetak-laporan-cuti')
@login_required
@role_required(['admin', 'superadmin'])
def cetak_laporan_cuti():
    # Ambil parameter filter
    tahun = request.args.get('tahun', datetime.now().year)
    bulan = request.args.get('bulan')
    departemen = request.args.get('departemen')
    format_file = request.args.get('format', 'pdf')  # pdf atau excel

    # Query data cuti
    query = Cuti.query.join(User)
    
    if bulan:
        query = query.filter(
            db.extract('month', Cuti.tanggal_mulai) == bulan,
            db.extract('year', Cuti.tanggal_mulai) == tahun
        )
    else:
        query = query.filter(db.extract('year', Cuti.tanggal_mulai) == tahun)
    
    if departemen:
        query = query.filter(User.departemen == departemen)
    
    data_cuti = query.order_by(Cuti.tanggal_mulai).all()

    # Format data untuk export
    rekap_data = []
    for cuti in data_cuti:
        rekap_data.append({
            'Nama': cuti.user.username,
            'Departemen': cuti.user.departemen,
            'Jenis Cuti': cuti.jenis_cuti,
            'Tanggal Mulai': cuti.tanggal_mulai.strftime('%d-%m-%Y'),
            'Tanggal Selesai': cuti.tanggal_selesai.strftime('%d-%m-%Y'),
            'Durasi': cuti.jumlah_hari,
            'Status': cuti.status,
            'Perihal': cuti.perihal_cuti[:50] + '...' if len(cuti.perihal_cuti) > 50 else cuti.perihal_cuti
        })

    if format_file == 'excel':
        # Export ke Excel
        df = pd.DataFrame(rekap_data)
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Rekap Cuti', index=False)
        writer.close()
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=rekap_cuti_{tahun}_{bulan if bulan else "all"}.xlsx'
        return response
    else:
        # Export ke PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Header
        pdf.cell(200, 10, txt="Rekap Data Cuti Karyawan", ln=1, align='C')
        pdf.cell(200, 10, txt=f"Periode: {bulan if bulan else 'Tahun'} {tahun}", ln=1, align='C')
        pdf.ln(10)
        
        # Tabel
        col_widths = [40, 30, 25, 25, 25, 15, 20, 40]
        headers = ['Nama', 'Departemen', 'Jenis Cuti', 'Mulai', 'Selesai', 'Durasi', 'Status', 'Perihal']
        
        # Header tabel
        pdf.set_font("Arial", 'B', 10)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, border=1)
        pdf.ln()
        
        # Isi tabel
        pdf.set_font("Arial", size=10)
        for row in rekap_data:
            for i, key in enumerate(['Nama', 'Departemen', 'Jenis Cuti', 'Tanggal Mulai', 'Tanggal Selesai', 'Durasi', 'Status', 'Perihal']):
                pdf.cell(col_widths[i], 10, str(row[key]), border=1)
            pdf.ln()
        
        # Footer
        pdf.ln(10)
        pdf.cell(0, 10, f"Total Data: {len(rekap_data)}", 0, 1, 'L')
        
        response = make_response(pdf.output(dest='S').encode('latin1'))
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=rekap_cuti_{tahun}_{bulan if bulan else "all"}.pdf'
        return response    

# ====================== RUTE ATASAN ======================
@app.route('/atasan/dashboard')
@login_required
@role_required(['atasan'])
def atasan_dashboard():
    # Hitung jumlah cuti berdasarkan status
    total_pending = Cuti.query \
        .join(User) \
        .filter(
            User.atasan_id == current_user.id,
            Cuti.status == 'Pending'
        ).count()
    
    total_approved = Cuti.query \
        .join(User) \
        .filter(
            User.atasan_id == current_user.id,
            Cuti.status == 'Approved'
        ).count()
    
    total_rejected = Cuti.query \
        .join(User) \
        .filter(
            User.atasan_id == current_user.id,
            Cuti.status == 'Rejected'
        ).count()
    
    # Pastikan username tersimpan di session
    if 'username' not in session:
        session['username'] = current_user.username
    
    return render_template('atasan/dashboard.html',
                         total_pending=total_pending,
                         total_approved=total_approved,
                         total_rejected=total_rejected)
        
@app.route('/atasan/manage-cuti', methods=['GET', 'POST'])
@login_required
@role_required(['atasan'])
def manage_cuti():
    status_filter = None

    if request.method == 'POST':
        status_filter = request.form.get('status_filter')

    # Query cuti dari bawahan langsung
    query = Cuti.query.join(User).filter(User.atasan_id == current_user.id)

    if status_filter in ['Pending', 'Approved', 'Rejected']:
        query = query.filter(Cuti.status == status_filter)

    daftar_cuti = query.order_by(Cuti.created_at.desc()).all()

    return render_template('atasan/manage_cuti.html', daftar_cuti=daftar_cuti, current_filter=status_filter)

@app.route('/atasan/approve-cuti/<int:cuti_id>', methods=['POST'])
@login_required
@role_required(['atasan'])
def approve_cuti(cuti_id):
    cuti = Cuti.query.get_or_404(cuti_id)
    user = cuti.user
    
    # Validasi kepemilikan cuti
    if user.atasan_id != current_user.id:
        abort(403)
    
    try:
        # Update status cuti
        cuti.status = 'Approved'
        cuti.updated_at = datetime.utcnow()
        
        # Google Calendar Integration
        if app.config.get('GOOGLE_CALENDAR_ENABLED', False):
            calendar = GoogleCalendarService()
            
            if not cuti.event_id:
                # Buat event baru jika belum ada
                calendar_data = {
                    'user_id': cuti.user_id,
                    'jenis_cuti': cuti.jenis_cuti,
                    'tanggal_mulai': cuti.tanggal_mulai.strftime('%Y-%m-%d'),
                    'tanggal_selesai': cuti.tanggal_selesai.strftime('%Y-%m-%d'),
                    'perihal_cuti': cuti.perihal_cuti,
                    'user_name': user.username,
                    'user_email': user.email
                }
                result = calendar.create_cuti_event(calendar_data)
                if result['success']:
                    cuti.event_id = result['event_id']
            else:
                # Update event yang sudah ada
                event = calendar.service.events().get(
                    calendarId='primary',
                    eventId=cuti.event_id
                ).execute()
                
                event['summary'] = f"APPROVED - Cuti {cuti.jenis_cuti} - {user.username}"
                
                calendar.service.events().update(
                    calendarId='primary',
                    eventId=cuti.event_id,
                    body=event
                ).execute()
        
        db.session.commit()
        
        # Slack Notification
        slack = SlackService()
        slack_data = {
            'user_name': user.username,
            'jenis_cuti': cuti.jenis_cuti,
            'tanggal_mulai': cuti.tanggal_mulai.strftime('%Y-%m-%d'),
            'tanggal_selesai': cuti.tanggal_selesai.strftime('%Y-%m-%d'),
            'jumlah_hari': cuti.jumlah_hari,
            'status': 'Approved'
        }
        slack.send_cuti_notification(slack_data)
        
        # Email notifikasi ke pegawai
        send_cuti_notification_email(
            user.email,
            'Persetujuan Cuti',
            f'Cuti Anda telah disetujui oleh {current_user.username}'
        )
        
        flash('Cuti berhasil disetujui', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error approving cuti: {str(e)}")
        flash('Gagal menyetujui cuti', 'error')
    
    return redirect(url_for('manage_cuti'))

# Route untuk menolak cuti
@app.route('/atasan/reject-cuti/<int:cuti_id>', methods=['POST'])
@login_required
@role_required(['atasan'])
def reject_cuti(cuti_id):
    alasan_penolakan = request.form.get('alasan_penolakan', 'Tidak ada alasan yang diberikan')
    cuti = Cuti.query.get_or_404(cuti_id)
    user = cuti.user
    
    # Validasi kepemilikan cuti
    if user.atasan_id != current_user.id:
        abort(403)
    
    try:
        # Update status cuti
        cuti.status = 'Rejected'
        cuti.alasan_penolakan = alasan_penolakan
        cuti.updated_at = datetime.utcnow()
        
        # Google Calendar Integration (update event jika ada)
        if app.config.get('GOOGLE_CALENDAR_ENABLED', False) and cuti.event_id:
            calendar = GoogleCalendarService()
            event = calendar.service.events().get(
                calendarId='primary',
                eventId=cuti.event_id
            ).execute()
            
            event['summary'] = f"REJECTED - Cuti {cuti.jenis_cuti} - {user.username}"
            event['description'] = f"Alasan penolakan: {alasan_penolakan}\n\n{event.get('description', '')}"
            
            calendar.service.events().update(
                calendarId='primary',
                eventId=cuti.event_id,
                body=event
            ).execute()
        
        db.session.commit()
        
        # Slack Notification
        slack = SlackService()
        slack_data = {
            'user_name': user.username,
            'jenis_cuti': cuti.jenis_cuti,
            'tanggal_mulai': cuti.tanggal_mulai.strftime('%Y-%m-%d'),
            'tanggal_selesai': cuti.tanggal_selesai.strftime('%Y-%m-%d'),
            'jumlah_hari': cuti.jumlah_hari,
            'status': 'Rejected',
            'alasan': alasan_penolakan
        }
        slack.send_cuti_notification(slack_data)
        
        # Email notifikasi ke pegawai
        send_cuti_notification_email(
            user.email,
            'Penolakan Cuti',
            f'Cuti Anda telah ditolak oleh {current_user.username}\nAlasan: {alasan_penolakan}'
        )
        
        flash('Cuti berhasil ditolak', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error rejecting cuti: {str(e)}")
        flash('Gagal menolak cuti', 'error')
    
    return redirect(url_for('manage_cuti'))

def send_cuti_notification_email(to, subject, body):
    try:
        msg = Message(
            subject,
            sender=app.config['MAIL_USERNAME'],
            recipients=[to]
        )
        msg.body = body
        mail.send(msg)
    except Exception as e:
        app.logger.error(f"Error sending email notification: {str(e)}")

# ====================== RUTE PEGAWAI ======================
@app.route('/pegawai/dashboard')
@login_required
@role_required(['pegawai'])
def pegawai_dashboard():
    user = db.session.get(User, current_user.id)
    
    # Kuota cuti tahunan (default 12 jika None)
    total_cuti = user.total_cuti if hasattr(user, 'total_cuti') and user.total_cuti is not None else 12
    
    # Query untuk cuti tahun berjalan
    tahun_ini = datetime.now().year
    cuti_disetujui = db.session.query(db.func.sum(Cuti.jumlah_hari)) \
        .filter(
            Cuti.user_id == current_user.id,
            Cuti.status == 'Approved',
            db.extract('year', Cuti.tanggal_mulai) == tahun_ini
        ).scalar() or 0
        
    cuti_ditolak = db.session.query(db.func.sum(Cuti.jumlah_hari)) \
        .filter(
            Cuti.user_id == current_user.id,
            Cuti.status == 'Rejected',
            db.extract('year', Cuti.tanggal_mulai) == tahun_ini
        ).scalar() or 0
        
    sisa_cuti = total_cuti - cuti_disetujui
    
    # 5 cuti terakhir
    cuti_terakhir = Cuti.query \
        .filter(Cuti.user_id == current_user.id) \
        .order_by(Cuti.tanggal_mulai.desc()) \
        .limit(5) \
        .all()
    
    # Ketentuan cuti berdasarkan role
    ketentuan_cuti = {
        'tahunan': {
            'max_hari': 12,
            'persyaratan': 'Minimal bekerja 1 tahun',
            'keterangan': f"Kuota tersedia: {sisa_cuti}/{total_cuti} hari"
        },
        'sakit': {
            'max_hari': 14,
            'persyaratan': 'Wajib lampirkan surat dokter',
            'keterangan': 'Lebih dari 3 hari butuh persetujuan'
        },
        'penting': {
            'max_hari': 30,
            'persyaratan': 'Keperluan mendesak',
            'keterangan': 'Butuh persetujuan HRD'
        },
        'melahirkan': {
            'max_hari': 90,
            'persyaratan': 'Khusus pegawai perempuan, dengan surat keterangan dokter/bidan',
            'keterangan': 'Dapat diambil sebelum dan sesudah persalinan sesuai regulasi'
        },
        'besar': {
            'max_hari': 90,
            'persyaratan': 'Minimal bekerja 5 tahun',
            'keterangan': 'Maksimal 1x dalam 4 tahun'    
        }
    }
    
    return render_template('pegawai/dashboard.html',
                         user=user,
                         sisa_cuti=sisa_cuti,
                         cuti_disetujui=cuti_disetujui,
                         cuti_ditolak=cuti_ditolak,
                         cuti_terakhir=cuti_terakhir,
                         ketentuan_cuti=ketentuan_cuti)

@app.route('/pegawai/ajukan-cuti', methods=['GET', 'POST'])
@login_required
@role_required(['pegawai'])
def ajukan_cuti():
    # Inisialisasi data form
    form_data = {}
    jenis_cuti_options = get_jenis_cuti_options()
    today = datetime.now().date()
    min_date = today
    max_date = today + timedelta(days=365)

    if request.method == 'POST':
        try:
            # Ambil data dari form
            form_data = {
                'jenis_cuti': request.form.get('jenis_cuti'),
                'tanggal_mulai': request.form.get('tanggal_mulai'),
                'tanggal_selesai': request.form.get('tanggal_selesai'),
                'perihal_cuti': request.form.get('perihal_cuti', '').strip(),
                'alamat_cuti': request.form.get('alamat_cuti', '').strip(),
                'kontak_darurat': request.form.get('kontak_darurat', '').strip(),
                'lampiran': request.files.get('lampiran')
            }

            # Validasi input
            errors = validate_cuti_form(form_data, current_user)
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('pegawai/ajukan_cuti.html',
                                    form_data=form_data,
                                    jenis_cuti_options=jenis_cuti_options,
                                    min_date=min_date.strftime('%Y-%m-%d'),
                                    max_date=max_date.strftime('%Y-%m-%d'))

            # Proses data cuti
            start_date = datetime.strptime(form_data['tanggal_mulai'], '%Y-%m-%d').date()
            end_date = datetime.strptime(form_data['tanggal_selesai'], '%Y-%m-%d').date()
            
            # Hitung hari kerja (exclude weekends)
            jumlah_hari = calculate_working_days(start_date, end_date)
            
            # Validasi sisa cuti untuk cuti tahunan
            if form_data['jenis_cuti'] == 'TAHUNAN':
                if current_user.sisa_cuti < jumlah_hari:
                    flash(f'Sisa cuti tahunan tidak mencukupi. Sisa cuti Anda: {current_user.sisa_cuti} hari', 'error')
                    return render_template('pegawai/ajukan_cuti.html',
                                        form_data=form_data,
                                        jenis_cuti_options=jenis_cuti_options,
                                        min_date=min_date.strftime('%Y-%m-%d'),
                                        max_date=max_date.strftime('%Y-%m-%d'))

            # Simpan lampiran jika ada
            lampiran_path = None
            if form_data['lampiran'] and allowed_file(form_data['lampiran'].filename):
                lampiran_path = save_attachment(form_data['lampiran'])
                if not lampiran_path:
                    flash('Gagal menyimpan lampiran. Format file tidak didukung atau ukuran terlalu besar.', 'error')
                    return render_template('pegawai/ajukan_cuti.html',
                                        form_data=form_data,
                                        jenis_cuti_options=jenis_cuti_options,
                                        min_date=min_date.strftime('%Y-%m-%d'),
                                        max_date=max_date.strftime('%Y-%m-%d'))

            # Dapatkan atasan langsung
            atasan = current_user.atasan
            if not atasan:
                flash('Tidak dapat menemukan atasan untuk persetujuan. Silakan hubungi admin.', 'error')
                return render_template('pegawai/ajukan_cuti.html',
                                    form_data=form_data,
                                    jenis_cuti_options=jenis_cuti_options,
                                    min_date=min_date.strftime('%Y-%m-%d'),
                                    max_date=max_date.strftime('%Y-%m-%d'))

            # Buat pengajuan cuti
            cuti = Cuti(
                user_id=current_user.id,
                atasan_id=atasan.id,
                jenis_cuti=form_data['jenis_cuti'],
                tanggal_mulai=start_date,
                tanggal_selesai=end_date,
                jumlah_hari=jumlah_hari,
                perihal_cuti=form_data['perihal_cuti'],
                address_during_leave=form_data['alamat_cuti'],
                emergency_contact=form_data['kontak_darurat'],
                lampiran=lampiran_path,
                status=CutiStatus.PENDING.value
            )

            # Tambahkan history status
            cuti.add_status_history(CutiStatus.PENDING, current_user.id, "Pengajuan cuti baru")

            db.session.add(cuti)
            db.session.commit()

            # Kirim notifikasi ke atasan
            send_notification(
                user_id=atasan.id,
                title='Pengajuan Cuti Baru',
                message=f'{current_user.full_name} mengajukan cuti {cuti.jenis_cuti.value}',
                notification_type='ALERT',
                link=url_for('atasan.review_cuti', cuti_id=cuti.id)
            )

            # Kirim email notifikasi
            send_cuti_email_notification(cuti, atasan)

            # Update sisa cuti jika cuti tahunan
            if form_data['jenis_cuti'] == 'TAHUNAN':
                current_user.sisa_cuti -= jumlah_hari
                db.session.commit()

            flash('Pengajuan cuti berhasil dikirim! Menunggu persetujuan atasan.', 'success')
            return redirect(url_for('pegawai.status_cuti'))

        except ValueError as ve:
            db.session.rollback()
            current_app.logger.error(f'Value error in ajukan_cuti: {str(ve)}')
            flash('Format tanggal tidak valid. Silakan coba lagi.', 'error')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error in ajukan_cuti: {str(e)}', exc_info=True)
            flash('Terjadi kesalahan sistem. Silakan coba lagi atau hubungi admin.', 'error')

    # GET request atau jika ada error
    return render_template('pegawai/ajukan_cuti.html',
                         form_data=form_data,
                         jenis_cuti_options=jenis_cuti_options,
                         min_date=min_date.strftime('%Y-%m-%d'),
                         max_date=max_date.strftime('%Y-%m-%d'))

# ====================== FUNGSI PEMBANTU ======================
def validate_cuti_form(form_data, user):
    """Validasi form pengajuan cuti"""
    errors = []
    
    # Validasi jenis cuti
    if not form_data['jenis_cuti'] or form_data['jenis_cuti'] not in [jc.value for jc in JenisCuti]:
        errors.append('Jenis cuti tidak valid')
    
    # Validasi tanggal
    try:
        start_date = datetime.strptime(form_data['tanggal_mulai'], '%Y-%m-%d').date()
        end_date = datetime.strptime(form_data['tanggal_selesai'], '%Y-%m-%d').date()
        
        if start_date < datetime.now().date():
            errors.append('Tanggal mulai tidak boleh di masa lalu')
        
        if end_date < start_date:
            errors.append('Tanggal selesai harus setelah tanggal mulai')
            
    except ValueError:
        errors.append('Format tanggal tidak valid')
    
    # Validasi perihal cuti
    if not form_data['perihal_cuti'] or len(form_data['perihal_cuti']) < 10:
        errors.append('Perihal cuti harus diisi minimal 10 karakter')
    
    return errors

def calculate_working_days(start_date, end_date):
    """Menghitung hari kerja (exclude weekends)"""
    delta = end_date - start_date
    total_days = delta.days + 1  # inclusive
    
    # Hitung weekend days
    full_weeks, remainder = divmod(total_days, 7)
    weekend_days = full_weeks * 2
    if remainder:
        start_weekday = start_date.weekday()
        weekend_days += sum(1 for day in range(start_weekday, start_weekday + remainder)
    
    return total_days - weekend_days

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_attachment(file):
    """Save uploaded file to upload folder"""
    try:
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return filename
        return None
    except Exception as e:
        current_app.logger.error(f"Error saving attachment: {str(e)}")
        return None

def send_cuti_notifications(cuti, user):
    """Kirim notifikasi ke berbagai platform"""
    try:
        # Google Calendar
        if app.config.get('GOOGLE_CALENDAR_ENABLED', False):
            calendar = GoogleCalendarService()
            event_data = {
                'jenis_cuti': cuti.jenis_cuti,
                'tanggal_mulai': cuti.tanggal_mulai.strftime('%Y-%m-%d'),
                'tanggal_selesai': cuti.tanggal_selesai.strftime('%Y-%m-%d'),
                'perihal_cuti': cuti.perihal_cuti,
                'user_name': user.username,
                'user_email': user.email
            }
            result = calendar.create_cuti_event(event_data)
            if result.get('success'):
                cuti.event_id = result.get('event_id')
                db.session.commit()
    
    except Exception as e:
        current_app.logger.error(f'Google Calendar error: {str(e)}')
    
    try:
        # Slack Notification
        if app.config.get('SLACK_WEBHOOK_URL'):
            slack = SlackService()
            slack_data = {
                'user_name': user.username,
                'jenis_cuti': cuti.jenis_cuti,
                'tanggal_mulai': cuti.tanggal_mulai.strftime('%Y-%m-%d'),
                'tanggal_selesai': cuti.tanggal_selesai.strftime('%Y-%m-%d'),
                'jumlah_hari': cuti.jumlah_hari,
                'status': 'Pending'
            }
            slack.send_cuti_notification(slack_data)
    
    except Exception as e:
        current_app.logger.error(f'Slack notification error: {str(e)}')

def get_jenis_cuti_options():
    """Daftar pilihan jenis cuti"""
    return ['Tahunan', 'Sakit', 'Melahirkan', 'Besar', 'Penting']

@app.route('/pegawai/status-cuti')
@login_required
@role_required(['pegawai'])
def pegawai_status_cuti():
    # Query dengan join ke tabel User untuk mendapatkan data atasan
    daftar_cuti = db.session.query(
        Cuti,
        User.full_name.label('atasan_nama')
    ).join(
        User, Cuti.atasan_id == User.id, isouter=True
    ).filter(
        Cuti.user_id == current_user.id,
        Cuti.deleted_at.is_(None)  # Exclude deleted leaves
    ).order_by(
        Cuti.created_at.desc()
    ).all()

    # Format data untuk template
    cuti_data = [{
        'cuti': cuti,
        'atasan_nama': atasan_nama,
        'status_class': get_status_class(cuti.status.value),
        'jenis_class': get_jenis_class(cuti.jenis_cuti.value)
    } for cuti, atasan_nama in daftar_cuti]

    # Hitung statistik cuti
    total_cuti = current_user.total_cuti
    sisa_cuti = current_user.sisa_cuti
    cuti_terpakai = total_cuti - sisa_cuti

    return render_template(
        'pegawai/status_cuti.html',
        daftar_cuti=cuti_data,
        total_cuti=total_cuti,
        sisa_cuti=sisa_cuti,
        cuti_terpakai=cuti_terpakai,
        CutiStatus=CutiStatus,  # Pass enum for template
        JenisCuti=JenisCuti     # Pass enum for template
    )

# Helper functions for template styling
def get_status_class(status):
    status_classes = {
        'Pending': 'warning',
        'Disetujui': 'success',
        'Ditolak': 'danger',
        'Dibatalkan': 'secondary',
        'Dalam Review': 'info'
    }
    return status_classes.get(status, 'secondary')

def get_jenis_class(jenis):
    jenis_classes = {
        'Cuti Tahunan': 'primary',
        'Cuti Sakit': 'info',
        'Cuti Melahirkan': 'pink',
        'Cuti Besar': 'purple',
        'Cuti Karena Alasan Penting': 'warning',
        'Cuti Tanpa Gaji': 'secondary',
        'Cuti Istimewa': 'danger'
    }
    return jenis_classes.get(jenis, 'secondary')
    
@app.route('/pegawai/batalkan-cuti/<int:cuti_id>', methods=['POST'])
@login_required
@role_required([UserRole.PEGAWAI.value])  # Menggunakan enum UserRole
def batalkan_cuti(cuti_id):
    cuti = Cuti.query.get_or_404(cuti_id)
    
    # Validasi kepemilikan cuti
    if cuti.user_id != current_user.id:
        abort(403, description="Anda tidak memiliki izin untuk membatalkan cuti ini")
    
    # Validasi status cuti
    if cuti.status != CutiStatus.PENDING.value:  # Menggunakan enum CutiStatus
        flash('Hanya bisa membatalkan cuti yang berstatus Pending', 'error')
        return redirect(url_for('status_cuti'))
    
    alasan_pembatalan = request.form.get('alasan_pembatalan', '').strip()
    if not alasan_pembatalan:
        flash('Harap memberikan alasan pembatalan', 'error')
        return redirect(url_for('detail_cuti', cuti_id=cuti_id))
    
    try:
        # Update status cuti menjadi dibatalkan (soft delete lebih baik daripada hard delete)
        cuti.cancel(current_user.id, alasan_pembatalan)
        
        # Kembalikan sisa cuti jika sudah approved
        if cuti.status == CutiStatus.APPROVED.value:
            current_user.sisa_cuti += cuti.jumlah_hari
            db.session.commit()
        
        # Jika terhubung dengan Google Calendar, hapus event
        if app.config.get('GOOGLE_CALENDAR_ENABLED', False) and cuti.event_id:
            try:
                calendar = GoogleCalendarService()
                calendar.service.events().delete(
                    calendarId='primary',
                    eventId=cuti.event_id
                ).execute()
            except Exception as calendar_error:
                app.logger.error(f"Gagal menghapus event calendar: {str(calendar_error)}")
        
        # Kirim notifikasi ke atasan
        if cuti.atasan_id:
            notification = Notification(
                user_id=cuti.atasan_id,
                title='Pembatalan Cuti',
                message=f'{current_user.full_name} telah membatalkan pengajuan cuti',
                notification_type='WARNING',
                link=url_for('review_cuti', cuti_id=cuti.id)
            )
            db.session.add(notification)
        
        # Kirim notifikasi ke Slack jika diaktifkan
        if app.config.get('SLACK_NOTIFICATIONS_ENABLED', False):
            try:
                slack = SlackService()
                slack.send_notification(
                    f"Pembatalan Cuti oleh {current_user.full_name} ({current_user.nip})\n"
                    f"Jenis Cuti: {cuti.jenis_cuti.value}\n"
                    f"Periode: {cuti.tanggal_mulai.strftime('%d-%m-%Y')} hingga {cuti.tanggal_selesai.strftime('%d-%m-%Y')}\n"
                    f"Alasan: {alasan_pembatalan}"
                )
            except Exception as slack_error:
                app.logger.error(f"Gagal mengirim notifikasi Slack: {str(slack_error)}")
        
        # Catat audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action='CANCEL_LEAVE',
            table_name='cuti',
            record_id=cuti.id,
            old_values={'status': cuti.status},
            new_values={'status': CutiStatus.CANCELLED.value},
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(audit_log)
        
        db.session.commit()
        flash('Cuti berhasil dibatalkan', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error canceling leave: {str(e)}", exc_info=True)
        flash('Gagal membatalkan cuti', 'error')
    
    return redirect(url_for('status_cuti'))

#
@app.route('/status-cuti')
@login_required
def status_cuti():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Query dasar dengan join User
    query = db.session.query(Cuti, User).join(User, Cuti.user_id == User.id)
    
    if current_user.role in [UserRole.ADMIN.value, UserRole.SUPERADMIN.value]:
        # Admin bisa lihat semua cuti
        results = query.order_by(Cuti.created_at.desc()).paginate(page=page, per_page=per_page)
    elif current_user.role == UserRole.ATASAN.value:
        # Atasan hanya lihat cuti bawahan
        results = query.filter(User.atasan_id == current_user.id)\
                      .order_by(Cuti.created_at.desc())\
                      .paginate(page=page, per_page=per_page)
    else:
        # Pegawai hanya lihat cuti sendiri
        results = query.filter(Cuti.user_id == current_user.id)\
                      .order_by(Cuti.created_at.desc())\
                      .paginate(page=page, per_page=per_page)
    
    # Format data untuk template
    cuti_list = [{
        'cuti': cuti,
        'user': user
    } for cuti, user in results.items]
    
    return render_template(
        'pegawai/status_cuti.html',
        cuti_list=cuti_list,
        page=page,
        total_pages=results.pages,
        per_page=per_page,
        current_role=current_user.role.value,
        UserRole=UserRole,
        CutiStatus=CutiStatus
    )

@app.route('/hapus-cuti/<int:cuti_id>', methods=['POST'])
@login_required
def hapus_cuti(cuti_id):
    cuti = Cuti.query.get_or_404(cuti_id)
    
    # Authorization check
    if current_user.role == UserRole.PEGAWAI.value and cuti.user_id != current_user.id:
        flash('Anda tidak memiliki izin untuk menghapus cuti ini', 'error')
        return redirect(url_for('status_cuti'))
    
    if current_user.role == UserRole.ATASAN.value:
        user = User.query.get(cuti.user_id)
        if not user or user.atasan_id != current_user.id:
            flash('Anda hanya dapat menghapus cuti bawahan Anda', 'error')
            return redirect(url_for('status_cuti'))
    
    # Status validation
    if cuti.status not in (CutiStatus.PENDING.value, CutiStatus.CANCELLED.value):
        flash('Hanya cuti berstatus Pending atau Dibatalkan yang dapat dihapus', 'error')
        return redirect(url_for('status_cuti'))
    
    try:
        # Delete from Google Calendar if exists
        if app.config.get('GOOGLE_CALENDAR_ENABLED', False) and cuti.event_id:
            try:
                calendar = GoogleCalendarService()
                calendar.service.events().delete(
                    calendarId='primary',
                    eventId=cuti.event_id
                ).execute()
            except Exception as e:
                app.logger.error(f"Gagal menghapus event dari Google Calendar: {str(e)}")
        
        db.session.delete(cuti)
        db.session.commit()
        
        # Slack notification
        if app.config.get('SLACK_WEBHOOK_URL'):
            slack = SlackService()
            slack.send_notification(
                f"Penghapusan Cuti oleh {current_user.username}\n"
                f"ID Cuti: {cuti_id}\n"
                f"Pemohon: {cuti.pemohon.username}\n"
                f"Status: {cuti.status.value}"
            )
        
        flash('Cuti berhasil dihapus', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Gagal menghapus cuti: {str(e)}")
        flash('Gagal menghapus cuti', 'error')
    
    return redirect(url_for('status_cuti'))

@app.route('/cetak-surat/<int:cuti_id>')
@login_required
def cetak_surat(cuti_id):
    # Query dasar dengan join User
    query = db.session.query(Cuti, User).join(User, Cuti.user_id == User.id).filter(Cuti.id == cuti_id)
    
    if current_user.role in [UserRole.ADMIN.value, UserRole.SUPERADMIN.value]:
        cuti, user = query.first_or_404()
    elif current_user.role == UserRole.ATASAN.value:
        cuti, user = query.filter(User.atasan_id == current_user.id).first_or_404()
    else:
        cuti, user = query.filter(Cuti.user_id == current_user.id).first_or_404()
    
    # Format tanggal
    bulan = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    
    # Handle both date object and string
    if isinstance(cuti.tanggal_mulai, str):
        tgl = datetime.strptime(cuti.tanggal_mulai, '%Y-%m-%d').date()
    else:
        tgl = cuti.tanggal_mulai
        
    tanggal_format = f"{tgl.day} {bulan[tgl.month]} {tgl.year}"
    tahun = tgl.year
    
    # Determine template based on role
    if current_user.role in [UserRole.ADMIN.value, UserRole.SUPERADMIN.value]:
        template = 'admin/cetak_surat.html'
    elif current_user.role == UserRole.ATASAN.value:
        template = 'atasan/cetak_surat.html'
    else:
        template = 'pegawai/cetak_surat.html'
    
    return render_template(
        template,
        cuti=cuti,
        user=user,
        tanggal_format=tanggal_format,
        tahun=tahun,
        current_user=current_user,
        UserRole=UserRole,
        CutiStatus=CutiStatus
    )
processor
# Konfigurasi Upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
PROFILE_UPLOAD_FOLDER = 'uploads/profile'

def allowed_file(filename):
    """Check if the filename has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/profil')
@login_required
def profil():
    """Menampilkan halaman profil pengguna"""
    try:
        user = db.session.get(User, current_user.id)
        
        if not user:
            flash('Data pengguna tidak ditemukan', 'error')
            return redirect(url_for('dashboard'))
        
        # Format data untuk ditampilkan
        profil_data = {
            'tanggal_lahir': user.tanggal_lahir.strftime('%d/%m/%Y') if user.tanggal_lahir else '-',
            'jenis_kelamin': 'Laki-laki' if user.jenis_kelamin == 'L' else 'Perempuan' if user.jenis_kelamin == 'P' else '-',
            'golongan': user.golongan or '-',
            'jabatan': user.jabatan or '-',
            'phone': user.phone or '-',
            'tempat_lahir': user.tempat_lahir or '-',
            'foto_profil': url_for('static', filename=user.foto_profil) if user.foto_profil else url_for('static', filename='images/default-profile.png'),
            'email': user.email,
            'nip': user.nip,
            'full_name': user.full_name
        }
        
        return render_template('pegawai/profil.html', 
                             user=user, 
                             profil_data=profil_data,
                             page_title='Profil Pengguna')
        
    except Exception as e:
        current_app.logger.error(f"Error accessing profile: {str(e)}", exc_info=True)
        flash('Terjadi kesalahan saat mengakses profil', 'error')
        return redirect(url_for('dashboard'))

@app.route('/edit-profil', methods=['GET', 'POST'])
@login_required
def edit_profil():
    """Mengedit data profil pengguna"""
    user = db.session.get(User, current_user.id)
    
    if request.method == 'POST':
        try:
            # Validasi input
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            full_name = request.form.get('full_name', '').strip()
            
            if not email:
                flash('Email tidak boleh kosong', 'error')
                return redirect(url_for('edit_profil'))
            
            # Validasi format email
            if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
                flash('Format email tidak valid', 'error')
                return redirect(url_for('edit_profil'))
            
            # Validasi nomor telepon
            if phone and not re.match(r'^[\d\s+-]+$', phone):
                flash('Format nomor telepon tidak valid', 'error')
                return redirect(url_for('edit_profil'))
            
            # Update data
            user.email = email
            user.phone = phone
            user.full_name = full_name
            user.tempat_lahir = request.form.get('tempat_lahir', '').strip()
            
            # Tanggal lahir
            tanggal_lahir = request.form.get('tanggal_lahir')
            if tanggal_lahir:
                try:
                    user.tanggal_lahir = datetime.strptime(tanggal_lahir, '%Y-%m-%d').date()
                except ValueError:
                    flash('Format tanggal lahir tidak valid (YYYY-MM-DD)', 'error')
                    return redirect(url_for('edit_profil'))
            
            jenis_kelamin = request.form.get('jenis_kelamin')
            if jenis_kelamin in ['L', 'P']:
                user.jenis_kelamin = jenis_kelamin
            
            user.golongan = request.form.get('golongan', '').strip()
            user.jabatan = request.form.get('jabatan', '').strip()
            
            db.session.commit()
            flash('Profil berhasil diperbarui', 'success')
            return redirect(url_for('profil'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating profile: {str(e)}", exc_info=True)
            flash('Terjadi kesalahan saat memperbarui profil', 'error')
    
    # Format tanggal untuk form edit
    tanggal_lahir_form = user.tanggal_lahir.strftime('%Y-%m-%d') if user.tanggal_lahir else ''
    
    return render_template('user/edit_profil.html', 
                         user=user,
                         tanggal_lahir_form=tanggal_lahir_form,
                         page_title='Edit Profil')

@app.route('/upload-foto-profil', methods=['POST'])
@login_required
def upload_foto_profil():
    """Mengupload foto profil pengguna"""
    if 'foto_profil' not in request.files:
        flash('Tidak ada file yang dipilih', 'error')
        return redirect(url_for('profil'))

    file = request.files['foto_profil']
    
    if file.filename == '':
        flash('Tidak ada file yang dipilih', 'error')
        return redirect(url_for('profil'))

    # Validasi file
    if not (file and allowed_file(file.filename)):
        flash('Format file tidak didukung. Gunakan: PNG, JPG, JPEG', 'error')
        return redirect(url_for('profil'))
    
    # Validasi ukuran file
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        flash('Ukuran file terlalu besar. Maksimal 2MB', 'error')
        return redirect(url_for('profil'))

    try:
        # Hapus foto lama jika ada
        if current_user.foto_profil:
            old_path = os.path.join(current_app.static_folder, current_user.foto_profil)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError as e:
                    current_app.logger.error(f"Gagal menghapus foto lama: {str(e)}")

        # Generate nama file unik dan aman
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"profile_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        filename = secure_filename(filename)
        
        upload_path = os.path.join(current_app.static_folder, PROFILE_UPLOAD_FOLDER)
        os.makedirs(upload_path, exist_ok=True)
        
        filepath = os.path.join(upload_path, filename)
        file.save(filepath)
        
        # Simpan path relatif ke database
        current_user.foto_profil = os.path.join(PROFILE_UPLOAD_FOLDER, filename)
        db.session.commit()
        
        flash('Foto profil berhasil diupload', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading profile photo: {str(e)}", exc_info=True)
        flash('Gagal mengupload foto profil', 'error')
    
    return redirect(url_for('profil'))
    
    
# ====================== RUTE ERROR HANDLER ======================
@app.route('/unauthorized')
def unauthorized():
    return render_template('errors/401.html'), 401

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)