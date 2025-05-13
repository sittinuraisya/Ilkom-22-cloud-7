import re
from flask import current_app, request
from models import User, JenisCuti, UserRole
from sqlalchemy import func, or_, and_
from datetime import datetime, timedelta
from models import Cuti, CutiStatus

def validate_email(email):
    """Validasi format email dan kekhasan"""
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        return "Format email tidak valid"
    
    if User.query.filter(func.lower(User.email) == func.lower(email)).first():
        return "Email sudah terdaftar"
    
    return None

def validate_username(username):
    """Validasi username"""
    if len(username) < 4:
        return "Username minimal 4 karakter"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return "Username hanya boleh mengandung huruf, angka, dan underscore"
    
    if User.query.filter(func.lower(User.username) == func.lower(username)).first():
        return "Username sudah digunakan"
    
    return None

def validate_password(password, confirm_password):
    """Validasi kekuatan password"""
    if len(password) < 8:
        return "Password minimal 8 karakter"
    
    if not any(char.isdigit() for char in password):
        return "Password harus mengandung angka"
    
    if not any(char.isupper() for char in password):
        return "Password harus mengandung huruf kapital"
    
    if password != confirm_password:
        return "Password dan konfirmasi tidak cocok"
    
    return None

def validate_registration(form_data):
    """Validasi komprehensif form registrasi"""
    errors = {}
    
    # Validasi email
    email_error = validate_email(form_data.get('email', ''))
    if email_error:
        errors['email'] = email_error
    
    # Validasi username
    username_error = validate_username(form_data.get('username', ''))
    if username_error:
        errors['username'] = username_error
    
    # Validasi password
    password_error = validate_password(
        form_data.get('password', ''),
        form_data.get('confirm_password', '')
    )
    if password_error:
        errors['password'] = password_error
    
    # Validasi nama lengkap
    full_name = form_data.get('full_name', '').strip()
    if len(full_name.split()) < 2:
        errors['full_name'] = "Nama lengkap minimal 2 kata"
    
    # Validasi tanggal lahir (jika ada)
    if 'tanggal_lahir' in form_data:
        try:
            dob = datetime.strptime(form_data['tanggal_lahir'], '%Y-%m-%d')
            if dob.year > datetime.now().year - 10:
                errors['tanggal_lahir'] = "Usia minimal 10 tahun"
        except ValueError:
            errors['tanggal_lahir'] = "Format tanggal tidak valid"
    
    return errors

# Di file validasi (misal: utils/validators.py), ubah menjadi:

def validate_registration_form(form_data):
    """
    Validasi form registrasi dengan menerima dictionary
    Return list of error messages
    """
    errors = []
    
    # Validasi email
    if not form_data.get('email'):
        errors.append('Email harus diisi')
    elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', form_data['email']):
        errors.append('Format email tidak valid')
    
    # Validasi password
    if not form_data.get('password'):
        errors.append('Password harus diisi')
    elif len(form_data['password']) < 8:
        errors.append('Password minimal 8 karakter')
    
    # Validasi konfirmasi password
    if form_data['password'] != form_data.get('confirm_password'):
        errors.append('Password dan konfirmasi password tidak sama')
    
    # Validasi username
    if not form_data.get('username'):
        errors.append('Username harus diisi')
    elif len(form_data['username']) < 3:
        errors.append('Username minimal 3 karakter')
    
    # Tambahkan validasi untuk memastikan ada atasan
    if User.query.filter_by(role=UserRole.ATASAN).count() == 0:
        errors.append("Sistem belum memiliki atasan. Hubungi administrator.")
    
    return errors

def validate_login(form_data):
    """Validasi form login"""
    errors = {}
    
    if not form_data.get('username'):
        errors['username'] = "Username/Email harus diisi"
    
    if not form_data.get('password'):
        errors['password'] = "Password harus diisi"
    
    return errors

def validate_reset_password(form_data):
    """Validasi form reset password"""
    errors = {}
    
    password_error = validate_password(
        form_data.get('new_password', ''),
        form_data.get('confirm_password', '')
    )
    if password_error:
        errors['new_password'] = password_error
    
    return errors

def validate_cuti_form(form_data, user):
    errors = []
    
    if not form_data.get('jenis_cuti') or form_data['jenis_cuti'] not in [jc.value for jc in JenisCuti]:
        errors.append('Jenis cuti tidak valid')
    
    try:
        start_date = datetime.strptime(form_data['tanggal_mulai'], '%Y-%m-%d').date()
        end_date = datetime.strptime(form_data['tanggal_selesai'], '%Y-%m-%d').date()
        
        if start_date < datetime.now().date():
            errors.append('Tanggal tidak boleh di masa lalu')
        if end_date < start_date:
            errors.append('Tanggal selesai harus setelah tanggal mulai')
    except:
        errors.append('Format tanggal tidak valid')
    
    if len(form_data.get('perihal_cuti', '').strip()) < 10:
        errors.append('Perihal cuti minimal 10 karakter')
    
    return errors

def calculate_working_days(start_date, end_date):
    """Calculate working days excluding weekends"""
    delta = end_date - start_date
    working_days = 0
    for day in range(delta.days + 1):
        current_date = start_date + timedelta(days=day)
        if current_date.weekday() < 5:  # Monday-Friday
            working_days += 1
    return working_days

def allowed_file(filename):
    """Validate file extensions with enhanced security checks"""
    if not filename:
        return False
    
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
    MAX_FILENAME_LENGTH = 120  # Prevent long filename attacks
    
    try:
        # Security checks
        if len(filename) > MAX_FILENAME_LENGTH:
            return False
            
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
            
        # Extension validation
        if '.' not in filename:
            return False
            
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in ALLOWED_EXTENSIONS
        
    except Exception:
        return False


def validate_cuti_form(form_data, user):
    """Comprehensive leave request validation"""
    errors = []
    
    # Validate leave type
    valid_jenis_cuti = [jc.value for jc in JenisCuti]
    if not form_data.get('jenis_cuti') or form_data['jenis_cuti'] not in valid_jenis_cuti:
        errors.append('Jenis cuti tidak valid')
    
    # Date validation
    today = datetime.now().date()
    try:
        start_date = datetime.strptime(form_data['tanggal_mulai'], '%Y-%m-%d').date()
        end_date = datetime.strptime(form_data['tanggal_selesai'], '%Y-%m-%d').date()
        
        if start_date < today:
            errors.append('Tanggal mulai tidak boleh di masa lalu')
            
        if end_date < start_date:
            errors.append('Tanggal selesai harus setelah tanggal mulai')
            
        # Maximum leave duration (e.g., 30 days)
        max_duration = timedelta(days=30)
        if (end_date - start_date) > max_duration:
            errors.append('Durasi cuti tidak boleh lebih dari 30 hari')
            
        # Check for overlapping leave requests
        existing_cuti = Cuti.query.filter(
            Cuti.user_id == user.id,
            Cuti.status.notin_([CutiStatus.REJECTED, CutiStatus.CANCELLED]),
            or_(
                and_(
                    Cuti.tanggal_mulai <= end_date,
                    Cuti.tanggal_selesai >= start_date
                ),
                and_(
                    Cuti.tanggal_mulai >= start_date,
                    Cuti.tanggal_mulai <= end_date
                )
            )
        ).first()
        
        if existing_cuti:
            errors.append('Anda sudah memiliki cuti yang tumpang tindih dengan tanggal ini')
            
    except ValueError:
        errors.append('Format tanggal tidak valid (gunakan format YYYY-MM-DD)')
    except Exception as e:
        current_app.logger.error(f"Date validation error: {str(e)}")
        errors.append('Terjadi kesalahan validasi tanggal')
    
    # Validate purpose
    perihal = form_data.get('perihal_cuti', '').strip()
    if len(perihal) < 10:
        errors.append('Perihal cuti minimal 10 karakter')
    elif len(perihal) > 500:
        errors.append('Perihal cuti maksimal 500 karakter')
    
    # Special validation for sick leave
    if form_data.get('jenis_cuti') == JenisCuti.SAKIT.value and not request.files.get('lampiran'):
        errors.append('Cuti sakit memerlukan lampiran dokumen')
    
    return errors