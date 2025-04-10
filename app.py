# --- Built-in Python Modules ---
import os
import re
import time
import sqlite3
import smtplib
import traceback
from datetime import datetime, timedelta, date

# --- Flask Core ---
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, make_response, jsonify, abort, current_app
)
from flask_login import (
    LoginManager, current_user, login_user,
    logout_user, login_required, UserMixin
)

# --- Config & Local Modules ---
from config import Config
from models import User
from services.email_service import EmailService
from services.calendar_service import GoogleCalendarService

# --- Flask Utils ---
from functools import wraps
from itsdangerous import URLSafeTimedSerializer

# --- Werkzeug ---
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException

# --- Third-party Libraries ---
import pdfkit
import numpy as np
import requests
from email.mime.text import MIMEText
from dotenv import load_dotenv

# --- Google APIs ---
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from google_auth_oauthlib.flow import Flow
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- Load .env Credentials ---
load_dotenv('credentials/.env')

# --- Initialize Flask App ---
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# --- App Configuration ---
app.config['ENV'] = 'development'  # ganti ke 'production' saat deploy
app.config['SYSTEM_NAME'] = "E-Cuti: Sistem Digitalisasi Pengelolaan Cuti Pegawai"
app.config['ORGANIZATION'] = "Biro Organisasi Setda Prov. Sultra"
app.config['UPLOAD_FOLDER'] = 'static/uploads/profile'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret')
app.config['SECURITY_PASSWORD_SALT'] = 'your-password-salt'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
app.config['WKHTMLTOPDF_PATH'] = '/usr/local/bin/wkhtmltopdf'
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
app.config['REDIRECT_URI'] = os.getenv('REDIRECT_URI')
app.config['SLACK_WEBHOOK_URL'] = os.getenv('SLACK_WEBHOOK_URL')
app.config['MAILGUN_API_KEY'] = os.getenv('MAILGUN_API_KEY')
app.config['MAILGUN_DOMAIN'] = os.getenv('MAILGUN_DOMAIN')
app.config['MAILGUN_SENDER'] = os.getenv('MAILGUN_SENDER')

# --- Print to Confirm Environment ---
print(f"SECRET_KEY loaded: {app.config['SECRET_KEY']}")

# --- Serializer for Token (e.g., email confirmation) ---
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# --- Initialize Login Manager ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # nama fungsi view login kamu

# --- Initialize Custom Services ---
email_service = EmailService()
calendar_service = GoogleCalendarService()

class Config:
    # Google Calendar
    GOOGLE_CALENDAR_CREDENTIALS = 'service-account.json'
    GOOGLE_CALENDAR_ID = 'primary'

# --- PDF Config (gunakan di mana perlu) ---
PDF_CONFIG = {
    'page-size': 'A4',
    'margin-top': '15mm',
    'margin-right': '15mm',
    'margin-bottom': '15mm',
    'margin-left': '15mm',
    'encoding': 'UTF-8',
    'quiet': ''
}

# --- Optional Fallback Check ---
if not app.config.get('GOOGLE_CLIENT_ID'):
    print("Warning: GOOGLE_CLIENT_ID is not set. Check your .env file.")

class User(UserMixin):
    def __init__(self, id, username, password, role, email_verified, email):  
        self.id = id
        self.username = username
        self.password = password
        self.role = role
        self.email_verified = email_verified
        self.email = email  

    # Optional (Flask-Login compatible)
    def get_id(self):
        return str(self.id)
    
# --- Database Functions ---
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()

    try:
        conn.execute("ALTER TABLE cuti ADD COLUMN lampiran TEXT")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise 
    # Tabel users
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nip TEXT UNIQUE,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            email_verified BOOLEAN DEFAULT 0,
            verification_token TEXT,
            phone TEXT,
            tempat_lahir TEXT,
            tanggal_lahir TEXT,
            jenis_kelamin TEXT,
            golongan TEXT,
            jabatan TEXT,
            foto_profil TEXT,
            role TEXT NOT NULL DEFAULT 'pegawai',
            reset_token TEXT,
            reset_token_expiry TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabel cuti (dengan fitur cancel)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cuti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            jenis_cuti TEXT NOT NULL,
            tanggal_mulai TEXT NOT NULL,
            tanggal_selesai TEXT NOT NULL,
            jumlah_hari INTEGER,
            perihal_cuti TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            admin_notes TEXT,
            is_cancelled BOOLEAN DEFAULT 0,
            cancel_reason TEXT,
            cancelled_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Tabel login_logs
    conn.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            ip_address TEXT,
            success BOOLEAN,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Add default admin user if not exists
    admin_exists = conn.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin_exists:
        hashed_password = generate_password_hash('admin123')
        conn.execute('''
            INSERT INTO users (username, password, email, phone, role, nip, jabatan, golongan, email_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', hashed_password, 'admin@example.com', '08123456789', 'admin', '123456', 'Administrator', 'IV/a', 1))
    conn.commit()
    conn.close()

# --- Helper Functions ---
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if user:
            return User(
                id=user['id'],
                username=user['username'],
                password=user['password'],
                role=user['role'],
                email_verified=user['email_verified'],
                email=user['email']  # ← pastikan kolom `email` ada di database
            )
        return None
    finally:
        conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def send_email(to, subject, html):
    api_key = current_app.config.get('MAILGUN_API_KEY')
    domain = current_app.config.get('MAILGUN_DOMAIN')
    sender = current_app.config.get('MAILGUN_SENDER')

    if not all([api_key, domain, sender]):
        current_app.logger.warning('Mailgun config not set properly.')
        return None

    return requests.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
        auth=("api", api_key),
        data={
            "from": sender,
            "to": [to],
            "subject": subject,
            "html": html
        }
    )


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Akses terbatas untuk admin', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def verified_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        conn = get_db_connection()
        verified = conn.execute('SELECT email_verified FROM users WHERE id = ?', (session['user_id'],)).fetchone()[0]
        conn.close()
        if not verified:
            flash('Email Anda belum diverifikasi. Silakan cek email Anda', 'warning')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_working_days(start_date, end_date):
    delta = end_date - start_date
    working_days = 0
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)
        if day.weekday() < 5:  # Monday to Friday
            working_days += 1
    return working_days

def get_user_by_id(user_id):
    conn = sqlite3.connect('your_database.db')
    c = conn.cursor()
    c.execute("SELECT id, username, password, role, email_verified FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return User(*row)
    return None

def send_verification_email(email, token):
    verification_url = url_for('verify_email', token=token, _external=True)
    
    subject = "Verifikasi Email Anda"
    body = f"""
    <h2>Verifikasi Email Sistem Cuti</h2>
    <p>Silakan klik link berikut untuk verifikasi akun Anda:</p>
    <a href="{verification_url}">{verification_url}</a>
    <p>Link ini berlaku selama 24 jam.</p>
    """
    
    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = app.config['MAIL_USERNAME']
    msg['To'] = email
    
    try:
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_password_reset_email(user_email):
    token = serializer.dumps(user_email, salt=app.config['SECURITY_PASSWORD_SALT'])
    reset_url = url_for('reset_password_token', token=token, _external=True)
    
    msg = MIMEText(f"""
    Untuk reset password, klik link berikut:
    {reset_url}
    
    Link ini berlaku selama 1 jam.
    Jika Anda tidak meminta reset password, abaikan email ini.
    """)
    msg['Subject'] = 'Reset Password - Sistem Cuti'
    msg['From'] = app.config['MAIL_USERNAME']
    msg['To'] = user_email
    
    try:
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        app.logger.error(f"Error sending email: {str(e)}")
        return False

def log_login_attempt(user_id, username, success):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO login_logs (user_id, username, ip_address, success)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, request.remote_addr, success))
    conn.commit()
    conn.close()

def validate_password(password):
    """
    Minimal 8 karakter
    Minimal 1 huruf besar
    Minimal 1 angka
    Minimal 1 karakter spesial
    """
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    if not any(c in '!@#$%^&*()' for c in password):
        return False
    return True

def is_valid_email(email):
    """Validasi format email dengan regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def format_date(value, format='%d-%m-%Y'):
    if value is None:
        return ''
    if isinstance(value, str):
        value = datetime.strptime(value, '%Y-%m-%d')
    return value.strftime(format)

def get_cuti_by_id(cuti_id):
    """Ambil data cuti dari database berdasarkan ID"""
    conn = get_db_connection()
    cuti = conn.execute('''
        SELECT c.*, u.username 
        FROM cuti c
        JOIN users u ON c.user_id = u.id
        WHERE c.id = ?
    ''', (cuti_id,)).fetchone()
    conn.close()
    
    if not cuti:
        raise ValueError(f"Data cuti dengan ID {cuti_id} tidak ditemukan")
    
    return dict(cuti)  

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# Pastikan folder upload ada
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --- Routes ---
@app.context_processor
def inject_system_info():
    return {
        'system_name': app.config['SYSTEM_NAME'],
        'organization': app.config['ORGANIZATION'],
        'now': datetime.now()
    }

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        if not username or not password:
            flash('Username dan password harus diisi', 'error')
            return redirect(url_for('login'))

        conn = get_db_connection()
        try:
            user_row = conn.execute(
                'SELECT * FROM users WHERE username = ?', (username,)
            ).fetchone()

            if not user_row or not check_password_hash(user_row['password'], password):
                flash('Username atau password salah', 'error')
                return redirect(url_for('login'))

            # Cek verifikasi email
            if 'email_verified' in user_row and not user_row['email_verified']:
                flash('Email belum diverifikasi. Silakan cek email Anda', 'warning')
                return redirect(url_for('login'))

            # Buat objek User (dari UserMixin)
            user = User(
                id=user_row['id'],
                username=user_row['username'],
                password=user_row['password'],
                role=user_row['role'],
                email_verified=user_row['email_verified']
            )

            # Login pakai Flask-Login
            login_user(user, remember=remember, duration=timedelta(days=30))

            flash('Login berhasil', 'success')
            return redirect(url_for('user_dashboard'))

        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            flash('Terjadi kesalahan saat login', 'error')
            return redirect(url_for('login'))

        finally:
            conn.close()

    return render_template('auth/login.html')

@app.route('/verify-email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-verification', max_age=86400)  # 24 jam
        conn = get_db_connection()
        
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?', (email,)
        ).fetchone()

        if user and user['verification_token'] == token:
            conn.execute(
                'UPDATE users SET email_verified = 1, verification_token = NULL WHERE email = ?',
                (email,)
            )
            conn.commit()
            flash('Email berhasil diverifikasi! Silakan login.', 'success')
        else:
            flash('Link verifikasi tidak valid.', 'error')

    except Exception as e:
        print(f"[Verifikasi Gagal] {str(e)}")
        flash('Link verifikasi tidak valid atau kadaluarsa.', 'error')

    finally:
        if 'conn' in locals():
            conn.close()

    return redirect(url_for('login'))

@app.route('/send-email', methods=['POST'])
def send_email_api():
    data = request.get_json()
    success = email_service.send(
        to=data['email'],
        subject="Notifikasi Cuti",
        template=render_template('emails/notification.html', type=data['type'])
    )
    return jsonify(success=success)

@app.route('/callback')
def callback():
    from services.calendar_service import GoogleCalendarService
    try:
        calendar = GoogleCalendarService()
        calendar.get_credentials()  # Ini akan menyimpan token
        flash('Autentikasi Google Calendar berhasil!', 'success')
    except Exception as e:
        flash(f'Gagal autentikasi: {str(e)}', 'error')
    return redirect(url_for('dashboard'))

@app.route('/sync-calendar', methods=['POST'])
def sync_calendar():
    cuti_data = {
        'jenis_cuti': request.form.get('jenis_cuti'),
        'user_name': current_user.username,
        'user_email': current_user.email,
        'perihal_cuti': request.form.get('perihal_cuti'),
        'tanggal_mulai': request.form.get('tanggal_mulai'),
        'tanggal_selesai': request.form.get('tanggal_selesai')
    }
    
    result = calendar_service.create_cuti_event(cuti_data)
    if result['success']:
        return redirect(url_for('cuti.index'))
    else:
        flash('Gagal menyinkronkan dengan Google Calendar', 'error')
        return redirect(url_for('cuti.create'))
        return jsonify(error=str(e)), 500

@app.route('/test-calendar')
def test_calendar():
    calendar = GoogleCalendarService()
    creds = calendar.get_credentials()
    return "Berhasil mendapatkan credentials!"

@app.route('/lupa-password', methods=['GET', 'POST'])
def lupa_password():
    if request.method == 'POST':
        email = request.form.get('email')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user:
            if send_password_reset_email(email):
                flash('Link reset password telah dikirim ke email Anda', 'success')
            else:
                flash('Gagal mengirim email reset password', 'error')
        else:
            flash('Email tidak terdaftar', 'error')
        
        return redirect(url_for('lupa_password'))
    
    return render_template('auth/lupa_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=3600  # 1 jam expiry
        )
    except:
        flash('Link reset password tidak valid atau sudah kadaluarsa', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Password tidak cocok', 'error')
            return redirect(url_for('reset_password_token', token=token))
        
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        conn.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_password, email))
        conn.commit()
        conn.close()
        
        flash('Password berhasil direset. Silakan login dengan password baru.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/reset_password.html', token=token)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Kamu berhasil logout.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'pegawai')  # Default role pegawai

        # Validate inputs
        if not all([username, email, password, confirm_password]):
            flash('Semua field harus diisi', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Password dan konfirmasi password tidak cocok', 'error')
            return redirect(url_for('register'))

        if not is_valid_email(email):  # kamu harus punya fungsi ini
            flash('Format email tidak valid', 'error')
            return redirect(url_for('register'))

        # Hash password
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            # Insert new user
            conn.execute(
                'INSERT INTO users (username, email, password, role, email_verified) VALUES (?, ?, ?, ?, ?)',
                (username, email, hashed_password, role, 1 if app.config['ENV'] == 'development' else 0)
            )
            conn.commit()

            # Ambil kembali user untuk login
            user_row = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            user = User(**user_row)
            login_user(user)  # Login user langsung

            # Handle email verification based on environment
            if app.config['ENV'] == 'development':
                flash('Registrasi berhasil! (Development mode - verifikasi email dilewati)', 'success')
            else:
                try:
                    send_verification_email(email)  # harus punya fungsi ini
                    flash('Registrasi berhasil! Silakan cek email untuk verifikasi', 'success')
                except Exception as e:
                    print(f"Error sending verification email: {e}")
                    flash('Registrasi berhasil tetapi gagal mengirim email verifikasi. Silakan hubungi admin.', 'warning')

            return redirect(url_for('dashboard'))  # arahkan ke halaman utama login

        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                flash('Username sudah digunakan', 'error')
            elif 'email' in str(e):
                flash('Email sudah terdaftar', 'error')
            else:
                flash('Terjadi kesalahan saat registrasi', 'error')
            return redirect(url_for('register'))

        finally:
            conn.close()

    return render_template('auth/register.html')

@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    email = request.form.get('email')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    
    if not user:
        flash('Email tidak terdaftar', 'error')
    elif user['email_verified']:
        flash('Email sudah terverifikasi', 'info')
    else:
        try:
            # Coba gunakan token yang sudah ada
            token = user['verification_token'] or serializer.dumps(email, salt='email-verification')
            send_verification_email(email, token)
            flash('Email verifikasi telah dikirim ulang', 'success')
        except Exception as e:
            print(f"Gagal mengirim ulang: {str(e)}")
            flash('Gagal mengirim email. Hubungi admin.', 'error')
    
    conn.close()
    return redirect(url_for('login'))

# --- User Routes ---
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    
    # Get user data
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # Calculate leave statistics
    total_cuti = 12  # Default annual leave quota (adjust as needed)
    
    # Get approved leave days
    cuti_disetujui = conn.execute('''
        SELECT SUM(jumlah_hari) 
        FROM cuti 
        WHERE user_id = ? AND status = 'Approved' AND strftime('%Y', tanggal_mulai) = strftime('%Y', 'now')
    ''', (session['user_id'],)).fetchone()[0] or 0
    
    # Get rejected leave days
    cuti_ditolak = conn.execute('''
        SELECT SUM(jumlah_hari) 
        FROM cuti 
        WHERE user_id = ? AND status = 'Rejected' AND strftime('%Y', tanggal_mulai) = strftime('%Y', 'now')
    ''', (session['user_id'],)).fetchone()[0] or 0
    
    # Calculate remaining leave
    sisa_cuti = total_cuti - cuti_disetujui
    
    # Get latest leave requests
    cuti_terakhir = conn.execute('''
        SELECT * FROM cuti 
        WHERE user_id = ? 
        ORDER BY tanggal_mulai DESC 
        LIMIT 5
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    # Leave policy details
    ketentuan_cuti = {
        'tahunan': {
            'max_hari': 12,
            'persyaratan': 'Minimal bekerja 1 tahun',
            'keterangan': f"Kuota tahunan: {total_cuti} hari (Tersisa: {sisa_cuti} hari)"
        },
        'sakit': {
            'max_hari': 14,
            'persyaratan': 'Wajib lampirkan surat dokter',
            'keterangan': 'Lebih dari 3 hari butuh persetujuan atasan'
        },
        'melahirkan': {
            'max_hari': 90,
            'persyaratan': 'Untuk karyawan wanita',
            'keterangan': 'Wajib surat dokter kandungan'
        },
        'penting': {
            'max_hari': 30,
            'persyaratan': 'Untuk keperluan mendesak',
            'keterangan': 'Maksimal 5 hari berturut-turut'
        }
    }
    
    return render_template('user/dashboard.html',
                         user=user,
                         ketentuan_cuti=ketentuan_cuti,
                         sisa_cuti=sisa_cuti,
                         cuti_disetujui=cuti_disetujui,
                         cuti_ditolak=cuti_ditolak,
                         cuti_terakhir=cuti_terakhir)

@app.template_filter('format_date')
def format_date(value, format='%d-%m-%Y'):
    try:
        if isinstance(value, str):
            value = datetime.strptime(value, '%Y-%m-%d')
        return value.strftime(format)
    except:
        return value  # Return as-is if formatting fails

@app.route('/ajukan-cuti', methods=['GET', 'POST'])
@login_required
def ajukan_cuti():
    if request.method == 'POST':
        try:
            # Validasi data
            required_fields = {
                'jenis_cuti': request.form.get('jenis_cuti'),
                'tanggal_mulai': request.form.get('tanggal_mulai'),
                'tanggal_selesai': request.form.get('tanggal_selesai'),
                'perihal_cuti': request.form.get('perihal_cuti')
            }

            if not all(required_fields.values()):
                missing = [k for k, v in required_fields.items() if not v]
                flash(f'Field wajib diisi: {", ".join(missing)}', 'error')
                return redirect(url_for('ajukan_cuti'))

            # Validasi tanggal
            try:
                start_date = datetime.strptime(required_fields['tanggal_mulai'], '%Y-%m-%d')
                end_date = datetime.strptime(required_fields['tanggal_selesai'], '%Y-%m-%d')
            except ValueError:
                flash('Format tanggal tidak valid', 'error')
                return redirect(url_for('ajukan_cuti'))

            if end_date < start_date:
                flash('Tanggal selesai harus setelah tanggal mulai', 'error')
                return redirect(url_for('ajukan_cuti'))

            if start_date < datetime.now():
                flash('Tanggal mulai tidak boleh di masa lalu', 'error')
                return redirect(url_for('ajukan_cuti'))

            # Penanganan lampiran
            lampiran_path = None
            lampiran = request.files.get('lampiran')
            if lampiran and lampiran.filename:
                if not allowed_file(lampiran.filename):
                    flash('Format file tidak didukung. Gunakan PDF, JPG, atau PNG', 'error')
                    return redirect(url_for('ajukan_cuti'))

                filename = secure_filename(f"cuti_{current_user.id}_{int(time.time())}_{lampiran.filename}")
                lampiran_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                try:
                    lampiran.save(lampiran_path)
                except IOError as e:
                    current_app.logger.error(f'File save error: {str(e)}')
                    flash('Gagal menyimpan lampiran', 'error')
                    return redirect(url_for('ajukan_cuti'))

            # Hitung jumlah hari kerja (pastikan integer!)
            business_days = int(np.busday_count(
                start_date.date(),
                (end_date + timedelta(days=1)).date()  # Include end_date
            ))

            if business_days <= 0:
                flash('Durasi cuti harus minimal 1 hari kerja', 'error')
                return redirect(url_for('ajukan_cuti'))

            # Simpan ke database
            conn = get_db_connection()
            try:
                cur = conn.execute('''
                    INSERT INTO cuti (
                        user_id, jenis_cuti, tanggal_mulai, tanggal_selesai, 
                        jumlah_hari, perihal_cuti, lampiran, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    RETURNING id
                ''', (
                    current_user.id,
                    required_fields['jenis_cuti'],
                    required_fields['tanggal_mulai'],
                    required_fields['tanggal_selesai'],
                    business_days,  # sudah dipastikan tipe int
                    required_fields['perihal_cuti'],
                    lampiran_path,
                    'Pending'
                ))
                cuti_id = cur.fetchone()['id']
                conn.commit()

                # Integrasi Google Calendar
                if current_app.config.get('GOOGLE_CALENDAR_ENABLED', False):
                    try:
                        calendar_service = GoogleCalendarService()
                        event_result = calendar_service.create_cuti_event({
                            'jenis_cuti': required_fields['jenis_cuti'],
                            'tanggal_mulai': required_fields['tanggal_mulai'],
                            'tanggal_selesai': required_fields['tanggal_selesai'],
                            'perihal_cuti': required_fields['perihal_cuti'],
                            'user_name': current_user.username,
                            'user_email': current_user.email
                        })

                        if event_result['success']:
                            conn.execute('''
                                UPDATE cuti SET calendar_event = ? WHERE id = ?
                            ''', (event_result['event_link'], cuti_id))
                            conn.commit()
                    except Exception as e:
                        current_app.logger.error(f'Calendar error: {str(e)}')

                # Kirim notifikasi ke Slack
                if current_app.config.get('SLACK_WEBHOOK_URL'):
                    try:
                        slack_data = {
                            "text": f"Pengajuan Cuti Baru - {current_user.username}",
                            "blocks": [
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": f"*{current_user.username}* mengajukan cuti *{required_fields['jenis_cuti']}*"
                                    }
                                },
                                {
                                    "type": "section",
                                    "fields": [
                                        {
                                            "type": "mrkdwn",
                                            "text": f"*Periode:*\n{start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}"
                                        },
                                        {
                                            "type": "mrkdwn",
                                            "text": f"*Durasi:*\n{business_days} hari kerja"
                                        }
                                    ]
                                }
                            ]
                        }
                        requests.post(
                            current_app.config['SLACK_WEBHOOK_URL'],
                            json=slack_data,
                            timeout=5
                        )
                    except Exception as e:
                        current_app.logger.error(f'Slack error: {str(e)}')


                    # Kirim notifikasi email via Mailgun
                    try:
                        html_email = render_template('email_cuti.html',
                            nama=current_user.username,
                            email=current_user.email,
                            jenis_cuti=required_fields['jenis_cuti'],
                            tanggal_mulai=start_date.strftime('%d %B %Y'),
                            tanggal_selesai=end_date.strftime('%d %B %Y'),
                            jumlah_hari=business_days,
                            perihal=required_fields['perihal_cuti']
                        )

                        send_email(
                            to=current_user.email,
                            subject='Pengajuan Cuti Berhasil Dikirim',
                            html=html_email
                        )

                        # Jika ingin cc ke HRD atau atasan:
                        # send_email(to='hrd@ecuti-sultra.com', subject='Pengajuan Cuti Baru', html=html_email)

                    except Exception as e:
                        current_app.logger.error(f'Mailgun email error: {str(e)}')

                flash('Pengajuan cuti berhasil dikirim!', 'success')
                return redirect(url_for('status_cuti'))

            except sqlite3.Error as e:
                conn.rollback()
                current_app.logger.error(f'Database error: {str(e)}')
                flash('Terjadi kesalahan database', 'error')
            finally:
                conn.close()

        except Exception as e:
            current_app.logger.error(f'Unexpected error: {str(e)}')
            flash('Terjadi kesalahan sistem', 'error')

    # GET method - tampilkan form
    today = datetime.now().strftime('%Y-%m-%d')
    max_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')

    return render_template('user/ajukan_cuti.html',
                           min_date=today,
                           max_date=max_date,
                           jenis_cuti_options=['Tahunan', 'Sakit', 'Melahirkan', 'Penting'],
                           form_data=request.form if request.method == 'POST' else None)

@app.route('/batalkan-cuti/<int:cuti_id>', methods=['POST'])
@login_required
def batalkan_cuti(cuti_id):
    conn = get_db_connection()
    
    # Verifikasi pemilik cuti
    cuti = conn.execute('SELECT user_id FROM cuti WHERE id = ?', (cuti_id,)).fetchone()
    
    if not cuti:
        flash('Data cuti tidak ditemukan', 'error')
        return redirect(url_for('status_cuti'))
    
    if cuti['user_id'] != session['user_id'] and session['role'] != 'admin':
        flash('Anda tidak memiliki izin untuk membatalkan cuti ini', 'error')
        return redirect(url_for('status_cuti'))
    
    # Update status cuti
    conn.execute('UPDATE cuti SET status = "Dibatalkan" WHERE id = ?', (cuti_id,))
    conn.commit()
    conn.close()
    
    flash('Cuti berhasil dibatalkan', 'success')
    return redirect(url_for('status_cuti'))

@app.route('/status_cuti')
@login_required
def status_cuti():
    # Tambahkan parameter pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Jumlah item per halaman

    conn = get_db_connection()
    
    if session['role'] == 'admin':
        # Hitung total data
        total = conn.execute('SELECT COUNT(*) FROM cuti').fetchone()[0]
        # Query dengan pagination
        cuti_list = conn.execute('''
            SELECT c.*, u.username, u.nip 
            FROM cuti c JOIN users u ON c.user_id = u.id
            ORDER BY c.created_at DESC
            LIMIT ? OFFSET ?
        ''', (per_page, (page-1)*per_page)).fetchall()
    else:
        # Hitung total data untuk user
        total = conn.execute('SELECT COUNT(*) FROM cuti WHERE user_id = ?', 
                           (session['user_id'],)).fetchone()[0]
        # Query dengan pagination
        cuti_list = conn.execute('''
            SELECT * FROM cuti 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (session['user_id'], per_page, (page-1)*per_page)).fetchall()
    
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('user/status_cuti.html',
                         cuti_list=cuti_list,
                         page=page,
                         total_pages=total_pages,
                         per_page=per_page)

@app.route('/hapus-cuti/<int:cuti_id>', methods=['POST'])
@login_required
def hapus_cuti(cuti_id):
    conn = get_db_connection()
    cuti = conn.execute('SELECT * FROM cuti WHERE id = ?', (cuti_id,)).fetchone()

    if not cuti:
        flash('Data cuti tidak ditemukan', 'error')
        return redirect(url_for('status_cuti'))

    if cuti['user_id'] != session['user_id'] and session.get('role') != 'admin':
        flash('Anda tidak punya izin untuk menghapus cuti ini', 'error')
        return redirect(url_for('status_cuti'))

    if cuti['status'] not in ('Pending', 'Dibatalkan'):
        flash('Cuti yang sudah diproses tidak bisa dihapus', 'error')
        return redirect(url_for('status_cuti'))

    # Hapus dari database
    conn.execute('DELETE FROM cuti WHERE id = ?', (cuti_id,))
    conn.commit()
    conn.close()

    flash('Pengajuan cuti berhasil dihapus', 'success')
    return redirect(url_for('status_cuti'))


    
@app.route('/cetak-surat/<int:cuti_id>')
@login_required 
def cetak_surat(cuti_id):
    conn = get_db_connection()
    
    # Query database
    if session.get('role') == 'admin':
        cuti = conn.execute('SELECT c.*, u.* FROM cuti c JOIN users u ON c.user_id = u.id WHERE c.id = ?', (cuti_id,))
    else:
        cuti = conn.execute('SELECT c.*, u.* FROM cuti c JOIN users u ON c.user_id = u.id WHERE c.id = ? AND c.user_id = ?',
                          (cuti_id, session['user_id']))
    
    cuti = cuti.fetchone()
    conn.close()
    
    if not cuti:
        abort(403)
    
    # Konversi ke dictionary
    cuti_dict = dict(cuti)
    
    # Daftar bulan dalam Bahasa Indonesia
    bulan = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    
    # Format tanggal
    if isinstance(cuti_dict['tanggal_mulai'], str):
        tgl = datetime.strptime(cuti_dict['tanggal_mulai'], '%Y-%m-%d').date()
        cuti_dict['tanggal_format'] = f"{tgl.day} {bulan[tgl.month]} {tgl.year}"
        cuti_dict['tahun'] = tgl.year
    else:
        tgl = cuti_dict['tanggal_mulai']
        cuti_dict['tanggal_format'] = f"{tgl.day} {bulan[tgl.month]} {tgl.year}" 
        cuti_dict['tahun'] = tgl.year
    
    template = 'admin/cetak_surat.html' if session.get('role') == 'admin' else 'user/cetak_surat.html'
    return render_template(template, cuti=cuti_dict)

@app.route('/cetak-surat/<int:cuti_id>/pdf')
@login_required
def cetak_pdf(cuti_id):
    try:
        # Validasi input
        if not isinstance(cuti_id, int) or cuti_id <= 0:
            flash('ID cuti tidak valid', 'error')
            return redirect(url_for('status_cuti'))

        conn = get_db_connection()
        
        # Query dengan error handling
        try:
            cuti = conn.execute('''
                SELECT 
                    c.id as cuti_id,
                    c.jenis_cuti,
                    strftime('%d/%m/%Y', c.tanggal_mulai) as tanggal_mulai,
                    strftime('%d/%m/%Y', c.tanggal_selesai) as tanggal_selesai,
                    c.jumlah_hari,
                    c.perihal_cuti,
                    c.status,
                    u.id as user_id,
                    u.nip,
                    u.username,
                    u.jabatan,
                    u.golongan,
                    u.tempat_lahir,
                    strftime('%d/%m/%Y', u.tanggal_lahir) as tanggal_lahir
                FROM cuti c
                JOIN users u ON c.user_id = u.id
                WHERE c.id = ?
            ''', (cuti_id,)).fetchone()
        except sqlite3.Error as e:
            app.logger.error(f'Database error: {str(e)}')
            flash('Terjadi kesalahan database', 'error')
            return redirect(url_for('status_cuti'))
        finally:
            conn.close()

        if not cuti:
            flash('Data cuti tidak ditemukan', 'error')
            return redirect(url_for('status_cuti'))

        # Konversi ke dictionary dengan nilai default
        cuti_dict = {
            'cuti_id': cuti.get('cuti_id', ''),
            'jenis_cuti': cuti.get('jenis_cuti', ''),
            'tanggal_mulai': cuti.get('tanggal_mulai', ''),
            'tanggal_selesai': cuti.get('tanggal_selesai', ''),
            'jumlah_hari': cuti.get('jumlah_hari', 0),
            'perihal_cuti': cuti.get('perihal_cuti', ''),
            'status': cuti.get('status', 'Pending'),
            'user_info': {
                'nip': cuti.get('nip', ''),
                'username': cuti.get('username', ''),
                'jabatan': cuti.get('jabatan', ''),
                'golongan': cuti.get('golongan', ''),
                'tempat_lahir': cuti.get('tempat_lahir', ''),
                'tanggal_lahir': cuti.get('tanggal_lahir', '')
            }
        }

        # Render template dengan fallback values
        rendered = render_template(
            'admin/surat_cuti_pdf.html',
            cuti=cuti_dict,
            now=datetime.now().strftime('%d/%m/%Y %H:%M'),
            system_name=app.config.get('SYSTEM_NAME', 'Sistem Cuti'),
            organization=app.config.get('ORGANIZATION', 'Instansi')
        )

        # Generate PDF
        try:
            pdf = pdfkit.from_string(
                rendered,
                False,
                options={
                    **PDF_CONFIG,
                    'enable-local-file-access': None,  # Untuk akses file lokal
                    'quiet': ''
                },
                configuration=pdfkit.configuration(
                    wkhtmltopdf=app.config.get('WKHTMLTOPDF_PATH')
                )
            )
        except OSError as e:
            app.logger.error(f'PDF generation OS error: {str(e)}')
            flash('Aplikasi PDF generator tidak ditemukan', 'error')
            return redirect(url_for('cetak_surat', cuti_id=cuti_id))

        # Create response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = \
            f'attachment; filename=surat_cuti_{cuti_dict["user_info"]["nip"]}_{cuti_dict["cuti_id"]}.pdf'
        
        return response

    except Exception as e:
        app.logger.error(f'Unexpected error: {str(e)}', exc_info=True)
        flash('Terjadi kesalahan sistem', 'error')
        return redirect(url_for('status_cuti'))

# --- Route Profil ---
@app.route('/profil')
@login_required
def profil():
    conn = get_db_connection()
    user = conn.execute('''
        SELECT *, 
        strftime('%d/%m/%Y', tanggal_lahir) as tanggal_lahir_formatted,
        CASE WHEN jenis_kelamin = 'L' THEN 'Laki-laki' ELSE 'Perempuan' END as jenis_kelamin_label
        FROM users WHERE id = ?
    ''', (session['user_id'],)).fetchone()
    conn.close()
    
    if not user:
        flash('Data pengguna tidak ditemukan', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('user/profil.html', user=user)

@app.route('/edit-profil', methods=['GET', 'POST'])
@login_required
def edit_profil():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        tempat_lahir = request.form.get('tempat_lahir')
        tanggal_lahir = request.form.get('tanggal_lahir')
        jenis_kelamin = request.form.get('jenis_kelamin')
        golongan = request.form.get('golongan')
        jabatan = request.form.get('jabatan')
        
        try:
            conn.execute('''
                UPDATE users SET 
                    email = ?, 
                    phone = ?, 
                    tempat_lahir = ?, 
                    tanggal_lahir = ?, 
                    jenis_kelamin = ?, 
                    golongan = ?, 
                    jabatan = ? 
                WHERE id = ?
            ''', (email, phone, tempat_lahir, tanggal_lahir, jenis_kelamin, golongan, jabatan, session['user_id']))
            conn.commit()
            flash('Profil berhasil diperbarui', 'success')
            return redirect(url_for('user_dashboard'))
        except sqlite3.IntegrityError:
            flash('Email sudah digunakan oleh user lain', 'error')
        finally:
            conn.close()
    
    conn.close()
    return render_template("edit_profil.html", user=user)

@app.route('/upload-foto-profil', methods=['POST'])
@login_required
def upload_foto_profil():
    if 'foto_profil' not in request.files:
        flash('Tidak ada file yang dipilih', 'error')
        return redirect(url_for('profil'))
    
    file = request.files['foto_profil']
    if file.filename == '':
        flash('Tidak ada file yang dipilih', 'error')
        return redirect(url_for('profil'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"user_{session['user_id']}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        conn = get_db_connection()
        conn.execute('UPDATE users SET foto_profil = ? WHERE id = ?', 
                    (filename, session['user_id']))
        conn.commit()
        conn.close()
        
        flash('Foto profil berhasil diupload', 'success')
    else:
        flash('Format file tidak didukung (hanya .png, .jpg, .jpeg)', 'error')
    
    return redirect(url_for('profil'))

@app.route('/kalender-cuti')
@login_required
def kalender_cuti():
    conn = get_db_connection()
    
    if session['role'] == 'admin':
        cuti_data = conn.execute('''
            SELECT c.id, u.username, c.jenis_cuti, c.tanggal_mulai, c.tanggal_selesai, c.status,
                   u.nip, u.jabatan
            FROM cuti c JOIN users u ON c.user_id = u.id
            ORDER BY c.tanggal_mulai
        ''').fetchall()
    else:
        cuti_data = conn.execute('''
            SELECT id, jenis_cuti, tanggal_mulai, tanggal_selesai, status
            FROM cuti 
            WHERE user_id = ?
            ORDER BY tanggal_mulai
        ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    # Format data untuk kalender
    events = []
    for cuti in cuti_data:
        color = '#28a745' if cuti['status'] == 'Approved' else \
                '#ffc107' if cuti['status'] == 'Pending' else '#dc3545'
        
        events.append({
            'id': cuti['id'],
            'title': f"{cuti['username']} ({cuti['jenis_cuti']})" if 'username' in cuti.keys() else cuti['jenis_cuti'],
            'start': cuti['tanggal_mulai'],
            'end': datetime.strptime(cuti['tanggal_selesai'], '%Y-%m-%d') + timedelta(days=1),
            'color': color,
            'extendedProps': {
                'nip': cuti.get('nip', ''),
                'jabatan': cuti.get('jabatan', ''),
                'status': cuti['status']
            }
        })
    
    return render_template('kalender_cuti.html', events=events)

@app.route('/get_cuti_events')
@login_required
def get_cuti_events():
    user_id = request.args.get('user_id')
    conn = get_db_connection()
    
    if session['role'] == 'admin':
        query = '''
            SELECT c.id, c.jenis_cuti as title, c.tanggal_mulai as start, 
                   c.tanggal_selesai as end, c.status, c.perihal_cuti as keterangan,
                   CASE 
                     WHEN c.status = 'Approved' THEN '#28a745'
                     WHEN c.status = 'Pending' THEN '#ffc107'
                     ELSE '#dc3545'
                   END as color
            FROM cuti c
        '''
        params = ()
    else:
        query = '''
            SELECT id, jenis_cuti as title, tanggal_mulai as start, 
                   tanggal_selesai as end, status, perihal_cuti as keterangan,
                   CASE 
                     WHEN status = 'Approved' THEN '#28a745'
                     WHEN status = 'Pending' THEN '#ffc107'
                     ELSE '#dc3545'
                   END as color
            FROM cuti 
            WHERE user_id = ?
        '''
        params = (user_id,)
    
    cuti = conn.execute(query, params).fetchall()
    conn.close()
    
    events = []
    for c in cuti:
        events.append({
            'id': c['id'],
            'title': c['title'],
            'start': c['start'],
            'end': c['end'],
            'color': c['color'],
            'extendedProps': {
                'status': c['status'],
                'keterangan': c['keterangan']
            }
        })
    
    return jsonify(events)

# --- Admin Routes ---
# API Routes
@app.route('/api/calendar/sync-all', methods=['POST'])
@admin_required
def sync_all_calendar():
    try:
        conn = get_db_connection()
        pending_cuti = conn.execute('''
            SELECT c.*, u.* FROM cuti c
            JOIN users u ON c.user_id = u.id
            WHERE c.status = 'Approved'
        ''').fetchall()
        
        synced = 0
        for cuti in pending_cuti:
            event = {
                'summary': f'Cuti {cuti["jenis_cuti"]} - {cuti["username"]}',
                'start': {'date': cuti['tanggal_mulai']},
                'end': {'date': cuti['tanggal_selesai']},
            }
            calendar_service.create_event('primary', event)
            synced += 1
            
        return jsonify({
            'status': 'success',
            'synced': synced
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/email/reminder', methods=['POST'])
@admin_required
def send_reminder_email():
    data = request.get_json()
    email_service.send(
        to=data['email'],
        subject="Reminder Cuti",
        template=render_template('emails/reminder.html')
    )
    return jsonify({'status': 'success'})
    
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    stats = {
        'total_cuti': conn.execute('SELECT COUNT(*) FROM cuti').fetchone()[0],
        'pending_cuti': conn.execute('SELECT COUNT(*) FROM cuti WHERE status = "Pending"').fetchone()[0],
        'total_users': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    }
    latest_cuti = conn.execute('''
        SELECT c.*, u.nip, u.username, u.jabatan 
        FROM cuti c 
        JOIN users u ON c.user_id = u.id 
        ORDER BY c.created_at DESC LIMIT 5
    ''').fetchall()
    conn.close()
    return render_template('admin/dashboard.html', stats=stats, latest_cuti=latest_cuti)

@app.route('/admin/manage-cuti', methods=['GET', 'POST'])
@admin_required
def manage_cuti():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Items per page
    search = request.args.get('search', '')
    status_filter = request.args.get('status', 'all')

    conn = get_db_connection()
    
    # Base query
    query = "SELECT c.*, u.nip, u.username FROM cuti c JOIN users u ON c.user_id = u.id"
    count_query = "SELECT COUNT(*) FROM cuti c JOIN users u ON c.user_id = u.id"
    conditions = []
    params = []

    # Add filters if needed
    if status_filter != 'all':
        conditions.append("c.status = ?")
        params.append(status_filter)
    
    if search:
        conditions.append("(u.nip LIKE ? OR u.username LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    # Apply conditions
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        count_query += " WHERE " + " AND ".join(conditions)

    # Get total count
    total = conn.execute(count_query, params).fetchone()[0]
    total_pages = (total + per_page - 1) // per_page  # Ceiling division

    # Apply pagination
    query += " ORDER BY c.created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page-1)*per_page])
    
    cuti_list = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('admin/manage_cuti.html',
                         cuti_list=cuti_list,
                         search=search,
                         status_filter=status_filter,
                         page=page,
                         total_pages=total_pages,
                         total=total)

@app.route('/admin/approve-cuti/<int:cuti_id>')
@admin_required
def approve_cuti(cuti_id):
    conn = get_db_connection()
    conn.execute('''
        UPDATE cuti SET 
            status = 'Approved',
            updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (cuti_id,))
    conn.commit()
    conn.close()
    flash('Cuti berhasil disetujui', 'success')
    return redirect(url_for('manage_cuti'))

@app.route('/admin/reject-cuti/<int:cuti_id>', methods=['POST'])
@admin_required
def reject_cuti(cuti_id):
    admin_notes = request.form.get('admin_notes')
    conn = get_db_connection()
    conn.execute('''
        UPDATE cuti SET 
            status = 'Rejected',
            admin_notes = ?,
            updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (admin_notes, cuti_id))
    conn.commit()
    conn.close()
    flash('Cuti berhasil ditolak', 'success')
    return redirect(url_for('manage_cuti'))

# @app.route('/admin/cetak-surat/<int:cuti_id>')
# @admin_required
# def cetak_surat(cuti_id):
#     conn = get_db_connection()
#     cuti = conn.execute('''
#         SELECT c.*, u.* 
#         FROM cuti c 
#         JOIN users u ON c.user_id = u.id 
#         WHERE c.id = ?
#     ''', (cuti_id,)).fetchone()
#     conn.close()
    
#     if not cuti:
#         flash('Data cuti tidak ditemukan', 'error')
#         return redirect(url_for('manage_cuti'))
    
#     return render_template('admin/cetak_surat.html', cuti=cuti)

@app.route('/admin/manage-users')
@admin_required
def manage_users():
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    conn = get_db_connection()
    
    query = 'SELECT id, username, nip, jabatan, golongan, role FROM users'
    count_query = 'SELECT COUNT(*) FROM users'
    params = []
    conditions = []
    
    if search:
        conditions.append('(username LIKE ? OR nip LIKE ?)')
        params.extend([f'%{search}%', f'%{search}%'])
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
        count_query += ' WHERE ' + ' AND '.join(conditions)
    
    total = conn.execute(count_query, params).fetchone()[0]
    total_pages = (total + per_page - 1) // per_page
    
    query += ' ORDER BY username ASC LIMIT ? OFFSET ?'
    params.extend([per_page, (page-1)*per_page])
    
    users = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('admin/manage_users.html', 
                         users=users,
                         search=search,
                         page=page,
                         total_pages=total_pages)

@app.route('/admin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        nip = request.form.get('nip')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        role = request.form.get('role')
        jabatan = request.form.get('jabatan')
        golongan = request.form.get('golongan')
        
        try:
            conn.execute('''
                UPDATE users SET 
                    nip = ?,
                    username = ?,
                    email = ?,
                    phone = ?,
                    role = ?,
                    jabatan = ?,
                    golongan = ?
                WHERE id = ?
            ''', (nip, username, email, phone, role, jabatan, golongan, user_id))
            conn.commit()
            flash('Data user berhasil diperbarui', 'success')
        except sqlite3.IntegrityError:
            flash('Username, email, atau NIP sudah digunakan', 'error')
            conn.close()
            return redirect(url_for('edit_user', user_id=user_id))
        
        conn.close()
        return redirect(url_for('manage_users'))
    
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if not user:
        flash('User tidak ditemukan', 'error')
        return redirect(url_for('manage_users'))
    
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/delete-user/<int:user_id>')
@admin_required
def delete_user(user_id):
    conn = get_db_connection()
    
    cuti_count = conn.execute('SELECT COUNT(*) FROM cuti WHERE user_id = ?', (user_id,)).fetchone()[0]
    
    if cuti_count > 0:
        flash('User tidak dapat dihapus karena memiliki riwayat cuti', 'error')
    else:
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        flash('User berhasil dihapus', 'success')
    
    conn.close()
    return redirect(url_for('manage_users'))

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    init_db()
    app.run(debug=True)
    
@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(e):
    if isinstance(e, HTTPException):
        code = e.code
        description = e.description
    else:
        code = 500
        description = "Internal Server Error"

    # Log error untuk debugging
    app.logger.error(f"Error {code}: {description}")

    return render_template(
        f"errors/{code}.html",
        error=e,
        system_name=app.config['SYSTEM_NAME'],
        organization=app.config['ORGANIZATION']
    ), code

# Tangani semua exception lainnya
@app.errorhandler(Exception)
def handle_unexpected_error(e):
    app.logger.error(f"Unexpected error: {str(e)}")
    return render_template(
        "errors/500.html",
        error=e,
        system_name=app.config['SYSTEM_NAME'],
        organization=app.config['ORGANIZATION']
    ), 500

@app.route('/test/errors')
def test_errors():
    """Route untuk testing error pages (hapus di production)"""
    from werkzeug.exceptions import (
        BadRequest, Unauthorized, 
        Forbidden, NotFound, InternalServerError
    )
    
    errors = {
        '400': BadRequest(),
        '401': Unauthorized(),
        '403': Forbidden(),
        '404': NotFound(),
        '500': InternalServerError()
    }
    
    return render_template('errors/test_errors.html', errors=errors)

@app.route('/force-error')
def force_error():
    """Route untuk memicu error 500 (testing)"""
    raise Exception("Ini adalah error testing yang disengaja")