# --- Built-in Modules ---
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import re
import time
import sqlite3
import smtplib
import secrets
import string
import csv
from datetime import datetime, timedelta

# --- Flask Core & Extensions ---
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify, abort, current_app
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from sqlalchemy import text
from flask_migrate import Migrate
from flask_mail import Message, Mail

# --- Configuration & Local Modules ---
from config import Config
from models import db, User, LoginLog, Cuti, AuditLog, Notification
from services.email_service import EmailService
from services.calendar_service import GoogleCalendarService

# --- Utilities ---
from functools import wraps
from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from io import StringIO

# --- Third-party Libraries ---
import pdfkit
import numpy as np
import requests
from dotenv import load_dotenv
from email.mime.text import MIMEText
from sqlalchemy import text

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
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx'}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
mail = Mail(app)

# Inisialisasi SQLAlchemy & Migrate
db.init_app(app)
migrate = Migrate(app, db)

# Inisialisasi LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
email_service = EmailService()


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


# --- Middleware dan Dekorator ---

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role != role:
                flash('Anda tidak punya akses ke halaman ini.', 'error')
                return redirect(url_for('unauthorized'))  # Buat route ini
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Silakan login terlebih dahulu', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Akses terbatas untuk admin', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def atasan_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'atasan':
            flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def verified_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Gunakan SQLAlchemy untuk mendapatkan status email_verified
        user = User.query.get(current_user.id)
        if not user or not user.email_verified:
            flash(
                'Email Anda belum diverifikasi. Silakan cek email Anda.',
                'warning')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def redirect_to_dashboard(role, must_change_password=False):
    if role == 'superadmin':
        return redirect(url_for('superadmin_dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'atasan':
        if must_change_password:
            return redirect(url_for('ganti_password'))
        return redirect(url_for('atasan_dashboard'))
    elif role == 'user':
        return redirect(url_for('user_dashboard'))
    else:
        flash('Peran tidak dikenali', 'error')
        return redirect(url_for('login'))


def generate_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_password(password):
    return generate_password_hash(password)

# --- Fungsi Utility ---


def calculate_working_days(start_date, end_date):
    delta = end_date - start_date
    working_days = sum(
        1 for i in range(
            delta.days +
            1) if (
            start_date +
            timedelta(
                days=i)).weekday() < 5)
    return working_days


def get_user_by_id(user_id):
    conn = sqlite3.connect('your_database.db')
    c = conn.cursor()
    c.execute(
       "SELECT id, username, password, role, email_verified " \
        "FROM users WHERE id = ?",
        (user_id,
         ))
    row = c.fetchone()
    conn.close()
    return User(*row) if row else None


def send_verification_email(email, token):
    verification_url = url_for('verify_email', token=token, _external=True)
    body = f"""
    <h2>Verifikasi Email Sistem Cuti</h2>
    <p>Klik link berikut untuk verifikasi akun Anda:</p>
    <a href="{verification_url}">{verification_url}</a>
    <p>Link ini berlaku selama 24 jam.</p>
    """
    msg = MIMEText(body, 'html')
    msg['Subject'] = "Verifikasi Email Anda"
    msg['From'] = app.config['MAIL_USERNAME']
    msg['To'] = email

    try:
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(
                app.config['MAIL_USERNAME'],
                app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def send_password_reset_email(user_email):
    token = serializer.dumps(user_email,
                             salt=app.config['SECURITY_PASSWORD_SALT'])
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
            server.login(
                app.config['MAIL_USERNAME'],
                app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        app.logger.error(f"Error sending email: {str(e)}")
        return False


def log_login_attempt(user_id, username, success):
    # Buat objek LoginLog baru
    login_log = LoginLog(
        user_id=user_id,
        username=username,
        ip_address=request.remote_addr,
        success=success
    )

    # Tambahkan objek ke session dan commit untuk menyimpan ke database
    db.session.add(login_log)
    db.session.commit()


def validate_password(password):
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
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def format_date(value, format='%d-%m-%Y'):
    if value is None:
        return ''
    if isinstance(value, str):
        value = datetime.strptime(value, '%Y-%m-%d')
    return value.strftime(format)


def get_cuti_by_id(cuti_id):
    cuti = Cuti.query.join(User).filter(Cuti.id == cuti_id).first()

    if not cuti:
        raise ValueError(f"Data cuti dengan ID {cuti_id} tidak ditemukan")

    # Mengembalikan data cuti dalam bentuk dictionary
    return {
        'id': cuti.id,
        'user_id': cuti.user_id,
        'jenis_cuti': cuti.jenis_cuti,
        'tanggal_mulai': cuti.tanggal_mulai,
        'tanggal_selesai': cuti.tanggal_selesai,
        'jumlah_hari': cuti.jumlah_hari,
        'perihal_cuti': cuti.perihal_cuti,
        'status': cuti.status,
        'admin_notes': cuti.admin_notes,
        'is_cancelled': cuti.is_cancelled,
        'cancel_reason': cuti.cancel_reason,
        'cancelled_at': cuti.cancelled_at,
        'created_at': cuti.created_at,
        'updated_at': cuti.updated_at,
        'username': cuti.user.username  # Menambahkan username dari tabel users
    }


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


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {
        'png', 'jpg', 'jpeg', 'gif'}


# --- Pastikan Folder Upload Ada ---
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --------------------------------      GOOGLE CALENDAR API      ---------


# --- SCOPES global untuk Google API ---
SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarService:
    def __init__(self):
        """
        Inisialisasi kelas dengan autentikasi dan mendapatkan service Google Calendar.
        """
        self.credentials = self.authenticate_google()
        self.service = self.get_calendar_service()

    def authenticate_google(self):
        """
        Mengotentikasi user dengan Google OAuth 2.0 dan mendapatkan kredensial akses.
        """
        creds = None

        # Cek apakah file token sudah ada
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        # Jika tidak ada kredensial yang valid, lakukan autentikasi ulang
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials/client_secrets.json', SCOPES)
                creds = flow.run_local_server(port=0)

            # Simpan kredensial baru ke file token.json
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        return creds

    def get_calendar_service(self):
        """
        Mengembalikan service Google Calendar yang siap digunakan untuk melakukan operasi API.
        """
        service = build('calendar', 'v3', credentials=self.credentials)
        return service


def create_event(self, event_data):
    """
    Membuat event baru di Google Calendar.
    """
    try:
        # Parse the start and end date, and set the time to the appropriate
        # hour (09:00 for start, 17:00 for end)
        start_datetime = datetime.strptime(
            event_data['start_date'], '%Y-%m-%d').replace(hour=9, minute=0, second=0)
        end_datetime = datetime.strptime(
            event_data['end_date'], '%Y-%m-%d').replace(hour=17, minute=0, second=0)

        event = {
            'summary': f"{event_data['event_type']} - {event_data['user_name']}",
            'description': event_data['event_description'],
            'start': {
                # Automatically converted to the correct ISO format
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'Asia/Jakarta',
            },
            'end': {
                # Automatically converted to the correct ISO format
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Asia/Jakarta',
            },
            'attendees': [
                {'email': event_data['user_email']},
            ],
            'reminders': {
                'useDefault': True,
            },
        }

        created_event = self.service.events().insert(
            calendarId='primary', body=event).execute()

        return {'success': True, 'event': created_event}
    except Exception as e:
        print(f"Error creating Google Calendar event: {e}")
        return {'success': False, 'error': str(e)}

    def list_events(self):
        """
        Mendapatkan daftar event di Google Calendar.
        """
        try:
            events_result = self.service.events().list(
                calendarId='primary', maxResults=10,
                singleEvents=True, orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            # Menampilkan summary acara dari daftar event
            return [event['summary'] for event in events]
        except Exception as e:
            print(f"Error fetching events: {e}")
            return {'success': False, 'error': str(e)}

# Endpoint untuk callback autentikasi


@app.route('/google_callback')
def google_callback():
    try:
        GoogleCalendarService()
        flash('Autentikasi Google Calendar berhasil!', 'success')
    except Exception as e:
        flash(f'Gagal autentikasi: {str(e)}', 'error')
    return redirect(url_for('dashboard'))

# Endpoint untuk menyinkronkan event ke Google Calendar


@app.route('/sync-calendar', methods=['POST'])
def sync_calendar_event():
    # Ambil data dari form
    event_data = {
        'event_type': request.form.get('event_type'),
        'user_name': current_user.username,
        'user_email': current_user.email,
        'event_description': request.form.get('event_description'),
        'start_date': request.form.get('start_date'),
        'end_date': request.form.get('end_date')
    }

    try:
        # Buat instance dari GoogleCalendarService
        calendar_service = GoogleCalendarService()

        # Panggil fungsi untuk membuat event
        result = calendar_service.create_event(event_data)

        if result['success']:
            flash('Berhasil menyinkronkan dengan Google Calendar!', 'success')
            return redirect(url_for('cuti.index'))
        else:
            flash('Gagal menyinkronkan dengan Google Calendar', 'error')
            return redirect(url_for('cuti.create'))

    except Exception as e:
        flash(f'Gagal menyinkronkan dengan Google Calendar: {str(e)}', 'error')
        return redirect(url_for('cuti.create'))

# Endpoint untuk menampilkan kalender


@app.route('/kalender-cuti', endpoint='kalender_cuti_view')
@login_required
def kalender_cuti():
    # Ambil data cuti berdasarkan role pengguna
    if current_user.role == 'admin':
        cuti_data = Cuti.query.join(User).add_columns(
            User.username,
            User.nip,
            User.jabatan,
            Cuti.jenis_cuti,
            Cuti.tanggal_mulai,
            Cuti.tanggal_selesai,
            Cuti.status).order_by(
            Cuti.tanggal_mulai).all()
    else:
        cuti_data = Cuti.query.filter(
            Cuti.user_id == current_user.id).order_by(
            Cuti.tanggal_mulai).all()

    # Ambil event dari Google Calendar
    calendar_service = GoogleCalendarService()
    google_events = calendar_service.list_events()

    # Gabungkan data event dari database dan Google Calendar
    events = []
    for cuti in cuti_data:
        color = '#28a745' if cuti.status == 'Approved' else '#ffc107' if cuti.status == 'Pending' else '#dc3545'
        events.append({
            'id': cuti.id,
            'title': f"{cuti.username} ({cuti.jenis_cuti})",
            'start': cuti.tanggal_mulai,
            'end': datetime.strptime(cuti.tanggal_selesai, '%Y-%m-%d') + timedelta(days=1),
            'color': color,
            'extendedProps': {
                'nip': cuti.nip,
                'jabatan': cuti.jabatan,
                'status': cuti.status
            }
        })

    # Gabungkan event dari Google Calendar
    for google_event in google_events:
        events.append({
            'title': google_event,
            'start': datetime.now(),  # Dapatkan waktu sesuai kebutuhan
            'end': datetime.now() + timedelta(hours=1),  # Sesuaikan dengan durasi
            'color': '#007bff',  # Sesuaikan dengan kebutuhan
            'extendedProps': {'status': 'Google Calendar'}
        })

    return render_template('kalender_cuti.html', events=events)


# ===================== ROUTES =====================

@app.route('/callback')
def callback():
    try:
        GoogleCalendarService()
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

    try:
        calendar_service = GoogleCalendarService()
        result = calendar_service.create_cuti_event(cuti_data)

        if result['success']:
            flash('Berhasil menyinkronkan dengan Google Calendar!', 'success')
            return redirect(url_for('cuti.index'))
        else:
            flash('Gagal menyinkronkan dengan Google Calendar', 'error')
            return redirect(url_for('cuti.create'))

    except Exception as e:
        flash(f'Gagal menyinkronkan dengan Google Calendar: {str(e)}', 'error')
        return redirect(url_for('cuti.create'))


@app.route('/test-calendar')
def test_calendar():
    calendar_service = GoogleCalendarService()
    calendar_service.get_credentials()
    events = calendar_service.list_events()
    events_display = "<br>".join(events)
    return f"Berhasil mendapatkan kredensial!<br><br>Acara Kalender:<br>{events_display}"


@app.route('/kalender-cuti')
@login_required
def kalender_cuti():
    if current_user.role == 'admin':
        cuti_data = Cuti.query.join(User).add_columns(
            User.username, User.nip, User.jabatan, Cuti.jenis_cuti,
            Cuti.tanggal_mulai, Cuti.tanggal_selesai, Cuti.status
        ).order_by(Cuti.tanggal_mulai).all()
    else:
        cuti_data = Cuti.query.filter(
            Cuti.user_id == current_user.id).order_by(Cuti.tanggal_mulai).all()

    service = GoogleCalendarService().service
    google_events = service.events().list(
        calendarId='primary',
        maxResults=10,
        singleEvents=True,
        orderBy='startTime').execute()
    google_event_list = google_events.get('items', [])

    events = []
    for cuti in cuti_data:
        color = '#28a745' if cuti.status == 'Approved' else '#ffc107' if cuti.status == 'Pending' else '#dc3545'
        events.append({
            'id': cuti.id,
            'title': f"{cuti.username} ({cuti.jenis_cuti})",
            'start': cuti.tanggal_mulai,
            'end': datetime.strptime(cuti.tanggal_selesai, '%Y-%m-%d') + timedelta(days=1),
            'color': color,
            'extendedProps': {
                'nip': cuti.nip,
                'jabatan': cuti.jabatan,
                'status': cuti.status
            }
        })

    for google_event in google_event_list:
        events.append({
            'title': google_event['summary'],
            'start': google_event['start'].get('dateTime', google_event['start'].get('date')),
            'end': google_event['end'].get('dateTime', google_event['end'].get('date')),
            'color': '#007bff',
            'extendedProps': {
                'status': 'Google Calendar',
                'keterangan': google_event.get('description', '')
            }
        })

    return render_template('kalender_cuti.html', events=events)

# --- Routes ---


@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))
    return render_template('index.html')


@app.context_processor
def inject_system_info():
    return {
        'system_name': app.config['SYSTEM_NAME'],
        'organization': app.config['ORGANIZATION'],
        'now': datetime.now()
    }

#  ---------------------   AUTENTIKASI   --------------------------------


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Jika pengguna sudah terautentikasi, arahkan ke dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = True if 'remember' in request.form else False

        if not username or not password:
            flash('Username dan password wajib diisi.', 'danger')
            return redirect(url_for('login'))

        # Gunakan SQLAlchemy untuk mengambil user berdasarkan username
        try:
            user = User.query.filter_by(username=username).first()

            if not user:
                flash('Username tidak ditemukan.', 'danger')
                return redirect(url_for('login'))

            # Cek password menggunakan check_password_hash
            if not check_password_hash(user.password, password):
                flash('Password salah.', 'danger')
                return redirect(url_for('login'))

            # Cek apakah email sudah diverifikasi
            if not user.email_verified:
                flash('Email belum diverifikasi.', 'warning')
                return redirect(url_for('login'))

            # Inisialisasi login_user
            login_user(user, remember=remember, duration=timedelta(days=30))
            flash('Berhasil login.', 'success')

            # Arahkan berdasarkan role pengguna
            if user.role == 'superadmin':
                return redirect(url_for('superadmin_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'atasan':
                if user.must_change_password:
                    return redirect(url_for('ganti_password'))
                return redirect(url_for('atasan_dashboard'))
            elif user.role == 'pegawai':
                return redirect(url_for('user_dashboard'))
            else:
                flash('Peran tidak dikenal.', 'danger')
                return redirect(url_for('login'))

        except Exception as e:
            app.logger.error(f"Login error: {e}")
            flash('Terjadi kesalahan saat login.', 'danger')
            return redirect(url_for('login'))

    return render_template('auth/login.html')

# Untuk logout


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Berhasil logout', 'success')
    return redirect(url_for('login'))

# Rute untuk registrasi pengguna


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Ambil data form
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'pegawai')  # Role default pegawai

        # Validasi input
        if not all([username, email, password, confirm_password]):
            flash('Semua field harus diisi', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Password dan konfirmasi password tidak cocok', 'error')
            return redirect(url_for('register'))

        if not is_valid_email(email):
            flash('Format email tidak valid', 'error')
            return redirect(url_for('register'))

        # Hash password
        hashed_password = generate_password_hash(password)

        try:
            # Masukkan user baru ke database
            new_user = User(
                username=username,
                email=email,
                password=hashed_password,
                role=role,
                email_verified=False  # Email tidak terverifikasi
            )

            db.session.add(new_user)
            db.session.commit()

            # Verifikasi email berdasarkan environment
            if app.config['ENV'] == 'development':
                flash(
                    'Registrasi berhasil! (Development mode - verifikasi email dilewati)',
                    'success')
            else:
                try:
                    send_verification_email(email)
                    flash(
                        """
                        Registrasi berhasil! Silakan cek email untuk verifikasi
                        """,  # Menggunakan tanda kutip tiga agar baris lebih pendek dan mudah dibaca
                        'success')
                except Exception as e:
                    print(f"Error sending verification email: {e}")
                    flash(
                        """
                        Registrasi berhasil tetapi gagal mengirim email verifikasi. 
                        Silakan hubungi admin.
                        """,  # Menggunakan tanda kutip tiga untuk menghindari baris panjang
                        'warning')


            # Login user setelah registrasi berhasil
            login_user(new_user)

            return redirect(url_for('dashboard'))

        except Exception as e:
            print(f"Error during registration: {e}")
            flash('Terjadi kesalahan saat registrasi', 'error')
            return redirect(url_for('register'))

    return render_template('auth/register.html')


@app.route('/verify-email/<token>')
def verify_email(token):
    try:
        # Mendekodekan token untuk mendapatkan email
        email = serializer.loads(
            token,
            salt='email-verification',
            max_age=86400)  # 24 jam

        # Mencari user berdasarkan email
        user = User.query.filter_by(email=email).first()

        if user and user.verification_token == token:
            # Verifikasi email dan hapus token verifikasi
            user.email_verified = True
            user.verification_token = None
            db.session.commit()

            # Mengirimkan pesan sukses
            flash('Email berhasil diverifikasi! Silakan login.', 'success')

            # Jika login otomatis diinginkan setelah verifikasi, aktifkan
            # berikut:
            login_user(user)
        else:
            flash('Link verifikasi tidak valid.', 'error')

    except Exception as e:
        print(f"[Verifikasi Gagal] {str(e)}")
        flash('Link verifikasi tidak valid atau kadaluarsa.', 'error')

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


@app.route('/lupa-password', methods=['GET', 'POST'])
def lupa_password():
    if request.method == 'POST':
        email = request.form.get('email')

        # Menggunakan SQLAlchemy untuk mengambil user berdasarkan email
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate token untuk reset password
            token = generate_reset_token(user.email)

            # Kirim email reset password
            if send_password_reset_email(user.email, token):
                flash(
                    'Link reset password telah dikirim ke email Anda',
                    'success')
            else:
                flash('Gagal mengirim email reset password', 'error')
        else:
            flash('Email tidak terdaftar', 'error')

        return redirect(url_for('lupa_password'))

    return render_template('auth/lupa_password.html')


def generate_reset_token(email):
    serializer = Serializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='reset-password')


def send_password_reset_email(email, token):
    # Ganti dengan logika pengiriman email, misalnya menggunakan Flask-Mail
    try:
        msg = Message('Reset Password',
                      sender='noreply@example.com',
                      recipients=[email])
        reset_url = url_for('reset_password', token=token, _external=True)
        msg.body = f'Klik link berikut untuk reset password: {reset_url}'
        mail.send(msg)
        return True
    except Exception as e:
        print(f'Error sending email: {e}')
        return False


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    try:
        # Memverifikasi token dan mendapatkan email
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=3600  # Token expired after 1 hour
        )
    except BaseException:
        flash('Link reset password tidak valid atau sudah kadaluarsa', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Mengambil password baru dan konfirmasi password
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Memastikan password dan konfirmasi password cocok
        if password != confirm_password:
            flash('Password tidak cocok', 'error')
            return redirect(url_for('reset_password_token', token=token))

        # Meng-hash password dan update di database menggunakan SQLAlchemy
        hashed_password = generate_password_hash(password)

        # Menemukan pengguna berdasarkan email
        user = User.query.filter_by(email=email).first()

        if user:
            user.password = hashed_password
            db.session.commit()  # Menyimpan perubahan ke database
            flash(
                'Password berhasil direset. Silakan login dengan password baru.',
                'success')
            return redirect(url_for('login'))
        else:
            flash('Pengguna tidak ditemukan.', 'error')
            return redirect(url_for('login'))

    return render_template('auth/reset_password.html', token=token)


@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    email = request.form.get('email')

    # Menggunakan SQLAlchemy untuk mengambil user berdasarkan email
    user = User.query.filter_by(email=email).first()

    if not user:
        flash('Email tidak terdaftar', 'error')
    elif user.email_verified:
        flash('Email sudah terverifikasi', 'info')
    else:
        try:
            # Gunakan token yang sudah ada atau buat token baru jika tidak ada
            token = user.verification_token or serializer.dumps(
                email, salt='email-verification')
            send_verification_email(email, token)
            flash('Email verifikasi telah dikirim ulang', 'success')
        except Exception as e:
            print(f"Gagal mengirim ulang: {str(e)}")
            flash('Gagal mengirim email. Hubungi admin.', 'error')

# --- User Routes ---


@app.route('/dashboard')
@login_required
def dashboard():
    # Mengambil data user menggunakan SQLAlchemy
    user = db.session.get(User, current_user.id)

    # Pastikan user ditemukan dan total_cuti ada (default 12 jika None)
    total_cuti = user.total_cuti if user.total_cuti is not None else 12

    # Mengambil jumlah cuti yang disetujui di tahun berjalan menggunakan
    # SQLAlchemy
    cuti_disetujui = db.session.query(
        db.func.sum(
            Cuti.jumlah_hari)) .filter(
        Cuti.user_id == current_user.id,
        Cuti.status == 'Approved') .filter(
                db.func.strftime(
                    '%Y',
                    Cuti.tanggal_mulai) == db.func.strftime(
                        '%Y',
                    db.func.current_timestamp())) .scalar() or 0  # Jika None, set ke 0

    # Mengambil jumlah cuti yang ditolak di tahun berjalan menggunakan
    # SQLAlchemy
    cuti_ditolak = db.session.query(
        db.func.sum(
            Cuti.jumlah_hari)) .filter(
        Cuti.user_id == current_user.id,
        Cuti.status == 'Rejected') .filter(
                db.func.strftime(
                    '%Y',
                    Cuti.tanggal_mulai) == db.func.strftime(
                        '%Y',
                    db.func.current_timestamp())) .scalar() or 0  # Jika None, set ke 0

    # Menghitung sisa cuti
    # Menghindari masalah jika cuti_disetujui None
    sisa_cuti = total_cuti - cuti_disetujui

    # Mengambil 5 cuti terakhir
    cuti_terakhir = Cuti.query.filter(Cuti.user_id == current_user.id) \
        .order_by(Cuti.tanggal_mulai.desc()) \
        .limit(5) \
        .all()

    # Ketentuan cuti
    ketentuan_cuti = {
        'tahunan': {
            'max_hari': 12,
            'persyaratan': 'Minimal bekerja 1 tahun',
            'keterangan': f"Kuota tahunan: {total_cuti} hari (Tersisa: {sisa_cuti} hari)"},
        'sakit': {
            'max_hari': 14,
            'persyaratan': 'Wajib lampirkan surat dokter',
            'keterangan': 'Lebih dari 3 hari butuh persetujuan atasan'},
        'melahirkan': {
            'max_hari': 90,
            'persyaratan': 'Untuk karyawan wanita',
            'keterangan': 'Wajib surat dokter kandungan'},
        'penting': {
            'max_hari': 30,
            'persyaratan': 'Untuk keperluan mendesak',
            'keterangan': 'Maksimal 5 hari berturut-turut'}}

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
    except BaseException:
        return value

#  --------------------  PERCUTIAN  ----------------------


@app.route('/ajukan-cuti', methods=['GET', 'POST'])
@login_required
def ajukan_cuti():
    if request.method == 'POST':
        try:
            # Ambil dan validasi data input
            jenis_cuti = request.form.get('jenis_cuti')
            tanggal_mulai = request.form.get('tanggal_mulai')
            tanggal_selesai = request.form.get('tanggal_selesai')
            perihal_cuti = request.form.get('perihal_cuti')

            # Validasi field wajib
            if not all([jenis_cuti, tanggal_mulai,
                       tanggal_selesai, perihal_cuti]):
                missing_fields = [k for k, v in {
                    'jenis_cuti': jenis_cuti,
                    'tanggal_mulai': tanggal_mulai,
                    'tanggal_selesai': tanggal_selesai,
                    'perihal_cuti': perihal_cuti
                }.items() if not v]
                flash(
                    f'Field wajib diisi: {", ".join(missing_fields)}',
                    'error'
                )
                return redirect(url_for('ajukan_cuti'))


            # Validasi tanggal
            try:
                start_date = datetime.strptime(tanggal_mulai, '%Y-%m-%d')
                end_date = datetime.strptime(tanggal_selesai, '%Y-%m-%d')
            except ValueError:
                flash('Format tanggal tidak valid', 'error')
                return redirect(url_for('ajukan_cuti'))

            if start_date < datetime.now():
                flash('Tanggal mulai tidak boleh di masa lalu', 'error')
                return redirect(url_for('ajukan_cuti'))

            if end_date < start_date:
                flash('Tanggal selesai harus setelah tanggal mulai', 'error')
                return redirect(url_for('ajukan_cuti'))

            # Hitung hari kerja
            try:
                # Pastikan menggunakan format date
                jumlah_hari = int(
                    np.busday_count(
                        start_date.date(),
                        (end_date +
                         timedelta(
                             days=1)).date()))
            except Exception as e:
                flash('Gagal menghitung hari kerja', 'error')
                current_app.logger.error(
                f'Business day calculation error: {str(e)}')
                return redirect(url_for('ajukan_cuti'))

            if jumlah_hari <= 0:
                flash('Durasi cuti harus minimal 1 hari kerja', 'error')
                return redirect(url_for('ajukan_cuti'))

            # Penanganan lampiran
            lampiran_path = None
            lampiran = request.files.get('lampiran')
            if lampiran and lampiran.filename:
                if not allowed_file(lampiran.filename):
                    flash(
                        'Format file tidak didukung. Gunakan PDF, JPG, atau PNG',
                        'error')
                    return redirect(url_for('ajukan_cuti'))

                filename = secure_filename(
                    f"cuti_{current_user.id}_{int(time.time())}_{lampiran.filename}")
                lampiran_path = os.path.join(
                    app.config['UPLOAD_FOLDER'], filename)

                try:
                    lampiran.save(lampiran_path)
                except Exception as e:
                    current_app.logger.error(f'File save error: {str(e)}')
                    flash('Gagal menyimpan lampiran', 'error')
                    return redirect(url_for('ajukan_cuti'))

            # Simpan pengajuan cuti ke database menggunakan SQLAlchemy
            try:
                new_cuti = Cuti(
                    user_id=current_user.id,
                    jenis_cuti=jenis_cuti,
                    tanggal_mulai=start_date,
                    tanggal_selesai=end_date,
                    jumlah_hari=jumlah_hari,
                    perihal_cuti=perihal_cuti,
                    lampiran=lampiran_path,
                    status='Pending'
                )

                db.session.add(new_cuti)
                db.session.commit()

                # Sinkronisasi Google Calendar jika aktif
                if current_app.config.get('GOOGLE_CALENDAR_ENABLED', False):
                    try:
                        calendar_service = GoogleCalendarService()
                        event_result = calendar_service.create_cuti_event({
                            'jenis_cuti': jenis_cuti,
                            'tanggal_mulai': tanggal_mulai,
                            'tanggal_selesai': tanggal_selesai,
                            'perihal_cuti': perihal_cuti,
                            'user_name': current_user.username,
                            'user_email': current_user.email
                        })

                        if event_result.get('success'):
                            new_cuti.calendar_event = event_result.get(
                                'event_link')
                            db.session.commit()
                    except Exception as e:
                        current_app.logger.error(
                            f'Google Calendar error: {str(e)}')

                # Kirim notifikasi ke Slack
                slack_webhook = current_app.config.get('SLACK_WEBHOOK_URL')
                if slack_webhook:
                    try:
                        slack_data = {
                            "text": f"Pengajuan Cuti Baru - {current_user.username}",
                            "blocks": [
                                {"type": "section", "text": {"type": "mrkdwn",
                                                             "text": f"*{current_user.username}* mengajukan cuti *{jenis_cuti}*"}},
                                {"type": "section", "fields": [
                                    {"type": "mrkdwn", "text": f"*Periode:*\n{start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}"},
                                    {"type": "mrkdwn", "text": f"*Durasi:*\n{jumlah_hari} hari kerja"}
                                ]}
                            ]
                        }
                        requests.post(
                            slack_webhook, json=slack_data, timeout=5)
                    except Exception as e:
                        current_app.logger.error(f'Slack error: {str(e)}')

                # Kirim notifikasi email via Mailgun
                try:
                    html_content = render_template(
                        'email_cuti.html',
                        nama=current_user.username,
                        email=current_user.email,
                        jenis_cuti=jenis_cuti,
                        tanggal_mulai=start_date.strftime('%d %B %Y'),
                        tanggal_selesai=end_date.strftime('%d %B %Y'),
                        jumlah_hari=jumlah_hari,
                        perihal=perihal_cuti)

                    send_email(
                        to=current_user.email,
                        subject='Pengajuan Cuti Berhasil Dikirim',
                        html=html_content
                    )
                except Exception as e:
                    current_app.logger.error(f'Mail error: {str(e)}')

                flash('Pengajuan cuti berhasil dikirim!', 'success')
                return redirect(url_for('status_cuti'))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Unexpected error: {str(e)}')
                flash('Terjadi kesalahan saat menyimpan data', 'error')

        except Exception as e:
            current_app.logger.error(f'Unexpected error: {str(e)}')
            flash('Terjadi kesalahan sistem', 'error')
            return redirect(url_for('ajukan_cuti'))

    # Jika GET request
    today = datetime.now().strftime('%Y-%m-%d')
    max_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')

    return render_template(
        'user/ajukan_cuti.html',
        min_date=today,
        max_date=max_date,
        jenis_cuti_options=[
            'Tahunan',
            'Sakit',
            'Melahirkan',
            'Penting'],
        form_data=request.form if request.method == 'POST' else None)


@app.route('/batalkan-cuti/<int:cuti_id>', methods=['POST'])
@login_required
def batalkan_cuti(cuti_id):
    cuti = Cuti.query.get(cuti_id)

    if not cuti:
        flash('Data cuti tidak ditemukan', 'error')
        return redirect(url_for('status_cuti'))

    # Hanya admin atau pemilik cuti yang boleh membatalkan
    if cuti.user_id != current_user.id and current_user.role != 'admin':
        flash('Anda tidak memiliki izin untuk membatalkan cuti ini', 'error')
        return redirect(url_for('status_cuti'))

    # Update status cuti
    cuti.status = "Dibatalkan"
    db.session.commit()

    flash('Cuti berhasil dibatalkan', 'success')
    return redirect(url_for('status_cuti'))


@app.route('/status_cuti')
@login_required
def status_cuti():
    # Ambil parameter halaman dari query string (?page=2)
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Jumlah data per halaman

    if current_user.role == 'admin':
        # Query cuti semua user, gabung dengan user info
        query = db.session.query(
            Cuti, User).join(
            User, Cuti.user_id == User.id)
        query.count()
        results = query.order_by(
            Cuti.created_at.desc()).paginate(
            page=page,
            per_page=per_page)

        cuti_list = [{
            'cuti': cuti,
            'username': user.username,
            'nip': user.nip
        } for cuti, user in results.items]

    else:
        # Query cuti milik user login
        query = Cuti.query.filter_by(user_id=current_user.id)
        query.count()
        results = query.order_by(
            Cuti.created_at.desc()).paginate(
            page=page,
            per_page=per_page)

        cuti_list = [{
            'cuti': cuti,
            'username': current_user.username,
            'nip': current_user.nip
        } for cuti in results.items]

    total_pages = results.pages

    return render_template(
        'user/status_cuti.html',
        cuti_list=cuti_list,
        page=page,
        total_pages=total_pages,
        per_page=per_page
    )


@app.route('/hapus-cuti/<int:cuti_id>', methods=['POST'])
@login_required
def hapus_cuti(cuti_id):
    cuti = Cuti.query.get(cuti_id)

    if not cuti:
        flash('Data cuti tidak ditemukan', 'error')
        return redirect(url_for('status_cuti'))

    if cuti.user_id != current_user.id and current_user.role != 'admin':
        flash('Anda tidak punya izin untuk menghapus cuti ini', 'error')
        return redirect(url_for('status_cuti'))

    if cuti.status not in ('Pending', 'Dibatalkan'):
        flash('Cuti yang sudah diproses tidak bisa dihapus', 'error')
        return redirect(url_for('status_cuti'))

    # Hapus dari database
    db.session.delete(cuti)
    db.session.commit()

    flash('Pengajuan cuti berhasil dihapus', 'success')
    return redirect(url_for('status_cuti'))


@app.route('/cetak-surat/<int:cuti_id>')
@login_required
def cetak_surat(cuti_id):
    # Ambil data cuti berdasarkan role
    if current_user.role == 'admin':
        cuti = db.session.query(Cuti).join(
            User).filter(Cuti.id == cuti_id).first()
    else:
        cuti = db.session.query(Cuti).join(User).filter(
            Cuti.id == cuti_id,
            Cuti.user_id == current_user.id
        ).first()

    # Jika data tidak ditemukan atau tidak berhak mengakses
    if not cuti:
        abort(403)

    # Format tanggal
    bulan = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }

    try:
        tgl = datetime.strptime(cuti.tanggal_mulai, '%Y-%m-%d').date()
    except BaseException:
        tgl = datetime.today().date()

    tanggal_format = f"{tgl.day} {bulan[tgl.month]} {tgl.year}"
    tahun = tgl.year

    # Pilih template berdasarkan role
    template = 'admin/cetak_surat.html' if current_user.role == 'admin' else 'user/cetak_surat.html'

    return render_template(
        template,
        cuti=cuti,
        tanggal_format=tanggal_format,
        tahun=tahun)

# Rute untuk cetak surat cuti dalam format PDF


@app.route('/cetak-surat/<int:cuti_id>/pdf')
@login_required
def cetak_pdf(cuti_id):
    try:
        # Validasi ID cuti
        if not isinstance(cuti_id, int) or cuti_id <= 0:
            flash('ID cuti tidak valid', 'error')
            return redirect(url_for('status_cuti'))

        # Ambil data cuti dari database
        cuti = Cuti.query.filter_by(id=cuti_id).join(User).first()

        if not cuti:
            flash('Data cuti tidak ditemukan.', 'error')
            return redirect(url_for('status_cuti'))

        # Data untuk template
        cuti_dict = {
            'cuti_id': cuti.id,
            'jenis_cuti': cuti.jenis_cuti,
            'tanggal_mulai': cuti.tanggal_mulai.strftime('%d/%m/%Y'),
            'tanggal_selesai': cuti.tanggal_selesai.strftime('%d/%m/%Y'),
            'jumlah_hari': cuti.jumlah_hari,
            'perihal_cuti': cuti.perihal_cuti,
            'status': cuti.status,
            'user_info': {
                'nip': cuti.user.nip,
                'username': cuti.user.username,
                'jabatan': cuti.user.jabatan,
                'golongan': cuti.user.golongan,
                'tempat_lahir': cuti.user.tempat_lahir,
                'tanggal_lahir': cuti.user.tanggal_lahir.strftime('%d/%m/%Y')
            }
        }

        # Render HTML dari template surat
        rendered = render_template(
            'admin/surat_cuti_pdf.html',
            cuti=cuti_dict,
            now=datetime.now().strftime('%d/%m/%Y %H:%M'),
            system_name=app.config.get('SYSTEM_NAME', 'Sistem Cuti'),
            organization=app.config.get('ORGANIZATION', 'Instansi')
        )

        # Generate PDF dari HTML
        try:
            pdf = pdfkit.from_string(
                rendered,
                False,
                options={
                    'enable-local-file-access': None,
                    'quiet': '',
                    'page-size': 'A4',
                    'encoding': 'UTF-8',
                    'margin-top': '20mm',
                    'margin-bottom': '20mm',
                    'margin-left': '15mm',
                    'margin-right': '15mm'
                },
                configuration=pdfkit.configuration(
                    wkhtmltopdf=app.config.get('WKHTMLTOPDF_PATH')
                )
            )
        except OSError as e:
            app.logger.error(f'Gagal membuat PDF: {e}')
            flash(
                'Aplikasi wkhtmltopdf tidak ditemukan atau gagal digunakan.',
                'error')
            return redirect(url_for('status_cuti'))

        # Kirim PDF ke browser
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = (
            f'attachment; filename=surat_cuti_{cuti.user.nip}_{cuti.id}.pdf'
        )
        return response

    except Exception as e:
        app.logger.error(f'Unexpected error: {e}', exc_info=True)
        flash('Terjadi kesalahan sistem yang tidak terduga.', 'error')
        return redirect(url_for('status_cuti'))


@app.route('/get_cuti_events')
@login_required
def get_cuti_events():
    user_id = request.args.get('user_id')

    # Cek apakah pengguna adalah admin
    if current_user.role == 'admin':
        cuti = Cuti.query.all()  # Ambil semua data cuti jika role = admin
    else:
        # Ambil data cuti untuk pengguna tertentu jika bukan admin
        if user_id:
            cuti = Cuti.query.filter_by(user_id=user_id).all()
        else:
            cuti = Cuti.query.filter_by(user_id=current_user.id).all()

    events = []
    for c in cuti:
        # Periksa apakah tanggal_mulai dan tanggal_selesai bukan None
        start_date = c.tanggal_mulai.isoformat() if c.tanggal_mulai else None
        end_date = c.tanggal_selesai.isoformat() if c.tanggal_selesai else None

        events.append({
            'id': c.id,
            'title': c.jenis_cuti,
            'start': start_date,  # Formatkan tanggal menjadi string ISO, jika tidak None
            'end': end_date,
            'color': '#28a745' if c.status == 'Approved' else '#ffc107' if c.status == 'Pending' else '#dc3545',
            'extendedProps': {
                'status': c.status,
                'keterangan': c.perihal_cuti
            }
        })

    return jsonify(events)


# ------------------------    Route Profil     ---------------------------

@app.route('/profil')
@login_required
def profil():
    user = User.query.get(current_user.id)

    if not user:
        flash('Data pengguna tidak ditemukan', 'error')
        return redirect(url_for('dashboard'))

    # Format tanggal_lahir dan jenis_kelamin dalam template
    tanggal_lahir_formatted = user.tanggal_lahir.strftime(
        '%d/%m/%Y') if user.tanggal_lahir else ''
    jenis_kelamin_label = 'Laki-laki' if user.jenis_kelamin == 'L' else 'Perempuan'

    return render_template('user/profil.html', user=user,
                           tanggal_lahir_formatted=tanggal_lahir_formatted,
                           jenis_kelamin_label=jenis_kelamin_label)


@app.route('/edit-profil', methods=['GET', 'POST'])
@login_required
def edit_profil():
    user = User.query.get(current_user.id)

    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        tempat_lahir = request.form.get('tempat_lahir')
        tanggal_lahir = request.form.get('tanggal_lahir')
        jenis_kelamin = request.form.get('jenis_kelamin')
        golongan = request.form.get('golongan')
        jabatan = request.form.get('jabatan')

        try:
            # Update user data using SQLAlchemy
            user.email = email
            user.phone = phone
            user.tempat_lahir = tempat_lahir
            user.tanggal_lahir = tanggal_lahir
            user.jenis_kelamin = jenis_kelamin
            user.golongan = golongan
            user.jabatan = jabatan

            db.session.commit()  # Save changes to the database

            flash('Profil berhasil diperbarui', 'success')
            return redirect(url_for('profil'))  # Redirect to the profil page
        except Exception as e:
            flash('Terjadi kesalahan saat memperbarui profil', 'error')
            db.session.rollback()

    return render_template("user/edit_profil.html", user=user)


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
        # Membuat nama file yang aman
        filename = secure_filename(f"user_{current_user.id}_{file.filename}")

        # Tentukan path folder untuk menyimpan foto profil
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profile')
        # Membuat folder jika belum ada
        os.makedirs(folder_path, exist_ok=True)

        # Simpan file ke folder 'static/uploads/profile/'
        filepath = os.path.join(folder_path, filename)
        file.save(filepath)

        # Simpan path relatif file ke database
        saved_path = f"uploads/profile/{filename}"

        # Update foto profil di database menggunakan SQLAlchemy
        current_user.foto_profil = saved_path
        db.session.commit()

        flash('Foto profil berhasil diupload', 'success')
    else:
        flash('Format file tidak didukung (hanya .png, .jpg, .jpeg)', 'error')

    return redirect(url_for('profil'))

# --- Admin Routes ---
# API Routes

@app.route('/api/email/reminder', methods=['POST'])
@admin_required
def send_reminder_email():
    try:
        data = request.get_json()
        to_email = data['email']
        subject = "Reminder Cuti"

        # Menggunakan template HTML untuk email reminder
        body = render_template('emails/reminder.html', user_email=to_email)

        # Pastikan email_service sudah terintegrasi dengan benar
        email_service.send(to=to_email, subject=subject, body=body)

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# -------- SUPERADMIN ROUTES ---------------

# Rute untuk dashboard superadmin


@app.route('/superadmin/dashboard')
@role_required('superadmin')
@login_required
def superadmin_dashboard():
    total_admin = User.query.filter_by(role='admin').count()
    total_atasan = User.query.filter_by(role='atasan').count()
    total_pegawai = User.query.filter_by(role='pegawai').count()
    users = User.query.all()
    return render_template('superadmin/dashboard.html',
                           total_admin=total_admin,
                           total_atasan=total_atasan,
                           total_pegawai=total_pegawai,
                           users=users)


@app.route('/superadmin/tambah-admin', methods=['GET', 'POST'])
@role_required('superadmin')  # Pastikan hanya superadmin yang dapat mengakses
@login_required  # Pastikan pengguna sudah login
def tambah_admin():
    if request.method == 'POST':
        # Ambil data dari form
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = 'admin'  # Role sebagai admin

        # Menambahkan admin baru ke database
        new_user = User(
            username=username,
            email=email,
            password=password,
            role=role,
            email_verified=True)
        db.session.add(new_user)
        db.session.commit()

        flash('Admin berhasil ditambahkan', 'success')
        return redirect(url_for('superadmin_dashboard'))

    return render_template('superadmin/tambah_admin.html')


@app.route('/superadmin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@role_required('superadmin')
@login_required
def superadmin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.role = request.form['role']

        db.session.commit()
        flash('Pengguna berhasil diupdate', 'success')
        return redirect(url_for('superadmin_dashboard'))

    return render_template('superadmin/edit_user.html', user=user)


@app.route('/superadmin/delete-user/<int:user_id>', methods=['POST', 'GET'])
@role_required('superadmin')
@login_required
def superadmin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Pengguna berhasil dihapus', 'success')
    return redirect(url_for('superadmin_dashboard'))

# Rute untuk melihat log audit


@app.route('/superadmin/audit-log')
@role_required('superadmin')
@login_required
def audit_log():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).all()
    return render_template('superadmin/audit_log.html', logs=logs)

# Rute untuk mengubah role pengguna


@app.route('/superadmin/change-role/<int:user_id>', methods=['POST'])
@role_required('superadmin')
@login_required
def change_role(user_id):
    new_role = request.form['role']
    user = User.query.get_or_404(user_id)
    user.role = new_role
    db.session.commit()
    flash('Role pengguna berhasil diubah', 'success')
    return redirect(url_for('superadmin_dashboard'))

# Rute untuk mengekspor data pengguna


@app.route('/superadmin/export-users')
@role_required('superadmin')
@login_required
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

# Rute untuk melihat notifikasi


@app.route('/superadmin/notifications')
@role_required('superadmin')
@login_required
def notifications():
    notifications = Notification.query.filter_by(seen=0).all()
    return render_template(
        'superadmin/notifications.html',
        notifications=notifications)

# ------- ADMIN ROUTES -------------


# Rute untuk dashboard admin


@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    try:
        # Get basic statistics
        stats = {
            'total_cuti': Cuti.query.count(),
            'pending_cuti': Cuti.query.filter_by(status='Pending').count(),
            'total_users': User.query.count()
        }

        # Get latest leave requests with safe date handling
        latest_cuti_query = db.session.query(
            Cuti.id,
            Cuti.jenis_cuti,
            db.func.strftime(
                '%Y-%m-%d',
                Cuti.tanggal_mulai).label('tanggal_mulai'),
            db.func.strftime(
                '%Y-%m-%d',
                Cuti.tanggal_selesai).label('tanggal_selesai'),
            Cuti.perihal_cuti,
            Cuti.status,
            User.nip,
            User.username,
            User.jabatan).join(User).order_by(
                Cuti.created_at.desc()).limit(5)

        # Execute query and format results
        latest_cuti = []
        for cuti in latest_cuti_query:
            latest_cuti.append({
                'id': cuti.id,
                'jenis_cuti': cuti.jenis_cuti,
                'tanggal_mulai': cuti.tanggal_mulai,
                'tanggal_selesai': cuti.tanggal_selesai,
                'perihal_cuti': cuti.perihal_cuti,
                'status': cuti.status,
                'nip': cuti.nip,
                'username': cuti.username,
                'jabatan': cuti.jabatan
            })

        # Get leave statistics by status
        rekap_per_status = db.session.query(
            Cuti.status,
            db.func.count().label('jumlah')
        ).group_by(Cuti.status).all()

        # Get monthly leave statistics with proper date formatting
        rekap_per_bulan = db.session.query(
            db.func.strftime('%Y-%m', Cuti.created_at).label('bulan'),
            db.func.count().label('jumlah')
        ).group_by('bulan').order_by(text('bulan desc')).limit(6).all()

        return render_template('admin/dashboard.html',
                               stats=stats,
                               latest_cuti=latest_cuti,
                               rekap_per_status=rekap_per_status,
                               rekap_per_bulan=rekap_per_bulan)

    except SQLAlchemyError as e:
        current_app.logger.error(
            f"Database error in admin_dashboard: {str(e)}", exc_info=True)
        return render_template(
            'error.html', error_message="Terjadi kesalahan database. Silakan coba lagi nanti."), 500

    except Exception:
        current_app.logger.error(
            "Unexpected error in admin_dashboard", exc_info=True)
        return render_template(
            'error.html', error_message="Terjadi kesalahan sistem. Tim kami telah diberitahu."), 500

# Rute untuk mengelola pengguna


@app.route('/admin/manage-users')
@login_required
@role_required('admin')
def manage_users():
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = User.query
    if search:
        query = query.filter(
            db.or_(
                User.username.like(
                    f'%{search}%'),
                User.nip.like(
                    f'%{search}%')))

    total = query.count()
    total_pages = (total + per_page - 1) // per_page

    users = query.order_by(User.username.asc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    ).items

    return render_template('admin/manage_users.html',
                           users=users,
                           search=search,
                           page=page,
                           total_pages=total_pages)

# Rute untuk mengedit data pengguna


@app.route('/admin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')  # pastikan decorator role_required berfungsi
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    atasan_list = User.query.filter_by(role='atasan').all()

    if request.method == 'POST':
        nip = request.form.get('nip')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        role = request.form.get('role')
        jabatan = request.form.get('jabatan')
        golongan = request.form.get('golongan')
        atasan_id = request.form.get('atasan')

        # Validasi unik email
        if User.query.filter(User.email == email, User.id != user_id).first():
            flash('Email sudah digunakan oleh pengguna lain.', 'error')
            return redirect(url_for('admin_edit_user', user_id=user_id))

        # Validasi unik username (opsional)
        if User.query.filter(
                User.username == username,
                User.id != user_id).first():
            flash('Username sudah digunakan oleh pengguna lain.', 'error')
            return redirect(url_for('admin_edit_user', user_id=user_id))

        try:
            user.nip = nip
            user.username = username
            user.email = email
            user.phone = phone
            user.role = role
            user.jabatan = jabatan
            user.golongan = golongan
            user.atasan_id = int(atasan_id) if atasan_id else None

            db.session.commit()
            flash('Data user berhasil diperbarui.', 'success')
            return redirect(url_for('manage_users'))

        except Exception as e:
            db.session.rollback()
            flash(
                f'Terjadi kesalahan saat memperbarui data: {str(e)}', 'error')
            return redirect(url_for('admin_edit_user', user_id=user_id))

    return render_template(
        'admin/edit_user.html',
        user=user,
        atasan_list=atasan_list)

# Rute untuk menghapus pengguna


@app.route('/admin/delete-user/<int:user_id>')
@login_required
@role_required('admin')
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('User tidak ditemukan', 'error')
        return redirect(url_for('manage_users'))

    # Mengecek apakah user memiliki riwayat cuti
    cuti_count = Cuti.query.filter_by(user_id=user_id).count()

    if cuti_count > 0:
        flash('User tidak dapat dihapus karena memiliki riwayat cuti', 'error')
    else:
        db.session.delete(user)  # Menghapus user
        db.session.commit()
        flash('User berhasil dihapus', 'success')

    return redirect(url_for('manage_users'))

# Rute untuk verifikasi email secara manual


@app.route('/admin/verifikasi', methods=['GET'])
@login_required
@role_required('admin')
def manual_verification():
    unverified_users = User.query.filter_by(email_verified=False).all()
    return render_template(
        'admin/verifikasi.html',
        unverified_users=unverified_users)


@app.route('/admin/tambah-atasan', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def tambah_atasan():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Password dan konfirmasi password tidak cocok.", "danger")
            return redirect(url_for('tambah_atasan'))

        hashed = hash_password(password)
        role = 'atasan'
        must_change_password = True
        email_verified = True

        new_user = User(
            username=name,
            email=email,
            password=hashed,
            role=role,
            must_change_password=must_change_password,
            email_verified=email_verified
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Atasan berhasil ditambahkan.", "success")
        return redirect(url_for('manage_users'))

    return render_template('admin/tambah_atasan.html')


#  ----------- ATASAN ROUTE -----------------

# Route untuk dashboard atasan
@app.route('/atasan/dashboard')
@login_required  # Pastikan pengguna sudah login
@role_required('atasan')  # Pastikan pengguna adalah atasan
def atasan_dashboard():
    current_user_id = current_user.id  # Ambil ID user yang sedang login

    # Menggunakan SQLAlchemy untuk menghitung status cuti
    total_pending = Cuti.query.join(User).filter(
        User.atasan_id == current_user_id,
        Cuti.status == 'Pending'
    ).count()

    total_approved = Cuti.query.join(User).filter(
        User.atasan_id == current_user_id,
        Cuti.status == 'Approved'
    ).count()

    total_rejected = Cuti.query.join(User).filter(
        User.atasan_id == current_user_id,
        Cuti.status == 'Rejected'
    ).count()

    return render_template('atasan/dashboard.html',
                           total_pending=total_pending,
                           total_approved=total_approved,
                           total_rejected=total_rejected)


# Route untuk manajemen cuti
@app.route('/atasan/manage-cuti', methods=['GET', 'POST'])
@login_required
@role_required('atasan')
def manage_cuti():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        search = request.args.get('search', '')
        status_filter = request.args.get('status', 'all')

        # Base query - explicitly join with User model using the correct
        # foreign key
        query = db.session.query(Cuti).join(
            User, Cuti.user_id == User.id  # Explicit join condition
        ).filter(
            # Only show cuti where current user is the atasan
            Cuti.atasan_id == current_user.id
        ).options(
            db.joinedload(Cuti.user),  # Eager load user relationship
            db.joinedload(Cuti.atasan)  # Eager load atasan relationship
        )

        # Filter status
        if status_filter != 'all':
            query = query.filter(Cuti.status == status_filter)

        # Search filter
        if search:
            query = query.filter(
                (User.nip.ilike(f"%{search}%")) |  # Case-insensitive search
                (User.username.ilike(f"%{search}%"))
            )

        # Count total records
        total = query.count()
        total_pages = (total + per_page - 1) // per_page

        # Apply pagination
        cuti_list = query.order_by(
            Cuti.created_at.desc()
        ).limit(per_page).offset(
            (page - 1) * per_page
        ).all()

        return render_template('atasan/manage_cuti.html',
                               cuti_list=cuti_list,
                               search=search,
                               status_filter=status_filter,
                               page=page,
                               total_pages=total_pages,
                               total=total)

    except Exception as e:
        current_app.logger.error(
            f"Error in manage_cuti: {str(e)}", exc_info=True)
        return render_template(
            'error.html', error_message="Terjadi kesalahan saat memuat data cuti"), 500
# Route untuk menyetujui cuti


@app.route('/atasan/approve-cuti/<int:cuti_id>')
@login_required  # Pastikan pengguna sudah login
@role_required('atasan')  # Pastikan pengguna adalah atasan
def approve_cuti(cuti_id):
    # Mencari data cuti berdasarkan ID
    cuti = Cuti.query.filter_by(id=cuti_id).first()

    if cuti and cuti.user.atasan_id == current_user.id:  # Memastikan hanya atasan yang dapat approve
        # Update status cuti menjadi 'Approved'
        cuti.status = 'Approved'
        # Menggunakan fungsi timestamp dari SQLAlchemy
        cuti.updated_at = db.func.current_timestamp()

        db.session.commit()  # Commit perubahan ke database
        flash('Cuti berhasil disetujui', 'success')
    else:
        flash('Cuti tidak ditemukan atau Anda tidak memiliki akses', 'danger')

    return redirect(url_for('manage_cuti'))


# Route untuk menolak cuti
@app.route('/atasan/reject-cuti/<int:cuti_id>', methods=['POST'])
@login_required  # Pastikan pengguna sudah login
@role_required('atasan')  # Pastikan pengguna adalah atasan
def reject_cuti(cuti_id):
    admin_notes = request.form.get('admin_notes')

    # Mencari data cuti berdasarkan ID
    cuti = Cuti.query.filter_by(id=cuti_id).first()

    if cuti and cuti.user.atasan_id == current_user.id:  # Memastikan hanya atasan yang dapat menolak
        # Update status cuti menjadi 'Rejected' dan menambahkan catatan admin
        cuti.status = 'Rejected'
        cuti.admin_notes = admin_notes
        # Menggunakan fungsi timestamp dari SQLAlchemy
        cuti.updated_at = db.func.current_timestamp()

        db.session.commit()  # Commit perubahan ke database
        flash('Cuti berhasil ditolak', 'success')
    else:
        flash('Cuti tidak ditemukan atau Anda tidak memiliki akses', 'danger')

    return redirect(url_for('manage_cuti'))

# # Mulai aplikasi
# if __name__ == '__main__':
#     app.run(debug=True)

# ----  ERROR HANDLERS --------


@app.route('/unauthorized')
@login_required
def unauthorized():
    return render_template('unauthorized.html')


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


if __name__ == '__main__':
    app.run(debug=True)
