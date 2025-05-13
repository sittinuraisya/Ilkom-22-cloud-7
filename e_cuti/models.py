from enum import Enum
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flask import current_app, url_for
from flask_login import UserMixin
from extensions import db
from sqlalchemy import event, Index, CheckConstraint, func
from sqlalchemy.orm import validates
import re, hashlib, binascii, secrets

# In config.py add:
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance/app.db')
        
class UserRole(Enum):
    PEGAWAI = 'pegawai'
    ADMIN = 'admin'
    ATASAN = 'atasan'
    SUPERADMIN = 'superadmin'

    @classmethod
    def get_values(cls):
        return [member.value for member in cls]

    @classmethod
    def from_string(cls, value):
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid role. Must be one of: {cls.get_values()}")

class JenisCuti(Enum):
    TAHUNAN = 'Cuti Tahunan'
    SAKIT = 'Cuti Sakit'
    MELAHIRKAN = 'Cuti Melahirkan'
    BESAR = 'Cuti Besar'
    PENTING = 'Cuti Karena Alasan Penting'
    TANPA_GAJI = 'Cuti Tanpa Gaji'
    ISTIMEWA = 'Cuti Istimewa'


class CutiStatus(Enum):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    CANCELLED = 'CANCELLED'
    IN_REVIEW = 'IN_REVIEW'

    @classmethod
    def get_display_name(cls, status):
        display_names = {
            'PENDING': 'Menunggu Persetujuan',
            'APPROVED': 'Disetujui',
            'REJECTED': 'Ditolak',
            'CANCELLED': 'Dibatalkan',
            'IN_REVIEW': 'Dalam Peninjauan'
        }
        return display_names.get(status, status)

    @classmethod
    def get_icon(cls, status):
        icons = {
            'PENDING': 'fa-clock',
            'APPROVED': 'fa-check-circle',
            'REJECTED': 'fa-times-circle',
            'CANCELLED': 'fa-ban',
            'IN_REVIEW': 'fa-search'
        }
        return icons.get(status, 'fa-question')


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    # Core Fields
    id = db.Column(db.Integer, primary_key=True)
    nip = db.Column(db.String(20), unique=True, nullable=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    email_verified = db.Column(db.Boolean, default=False)
    email_verified_at = db.Column(db.DateTime)
    verification_token = db.Column(db.String(100))
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)
    
    # Security Fields
    must_change_password = db.Column(db.Boolean, default=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    last_password_change = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    deactivated_at = db.Column(db.DateTime)
    deactivated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    deleted_at = db.Column(db.DateTime)
    deleted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Profile Fields
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    tempat_lahir = db.Column(db.String(50))
    tanggal_lahir = db.Column(db.Date)
    jenis_kelamin = db.Column(db.String(1))  # 'L' or 'P'
    jabatan = db.Column(db.String(80), nullable=True)
    golongan = db.Column(db.String(10), nullable=True)
    alamat = db.Column(db.String(200), nullable=True)
    foto_profil = db.Column(db.String(120))
    
    # Leave Fields
    total_cuti = db.Column(db.Integer, default=12)
    sisa_cuti = db.Column(db.Integer, default=12)
    
    # System Fields
    role = db.Column(db.Enum(UserRole), default=UserRole.PEGAWAI, nullable=False)
    atasan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    atasan = db.relationship('User', remote_side=[id], foreign_keys=[atasan_id], backref=db.backref('subordinates', lazy='dynamic'))
    creator = db.relationship('User', remote_side=[id], foreign_keys=[created_by], backref=db.backref('created_users', lazy='dynamic'))
    deactivator = db.relationship('User', remote_side=[id], foreign_keys=[deactivated_by])
    deleter = db.relationship('User', remote_side=[id], foreign_keys=[deleted_by])
    cuti_diajukan = db.relationship('Cuti', foreign_keys='Cuti.user_id', back_populates='pemohon', cascade='all, delete-orphan', lazy='dynamic')
    cuti_disetujui = db.relationship('Cuti', foreign_keys='Cuti.atasan_id',  back_populates='penyetuju', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', back_populates='user', lazy='dynamic')

    __table_args__ = (
        Index('idx_user_role', 'role'),
        Index('idx_user_atasan', 'atasan_id'),
        CheckConstraint('total_cuti >= 0', name='ck_user_total_cuti'),
        CheckConstraint('sisa_cuti >= 0', name='ck_user_sisa_cuti'),
        CheckConstraint('email_verified IN (0, 1)', name='ck_user_email_verified'),
        CheckConstraint('is_active IN (0, 1)', name='ck_user_is_active'),
        CheckConstraint('LENGTH(username) >= 3', name='ck_user_username_length'),
        CheckConstraint("email LIKE '%@%.%'", name='ck_user_email_format'),
    )

    # Validation methods
    role = db.Column(db.Enum(UserRole), default=UserRole.PEGAWAI, nullable=False)

    @classmethod
    def get_default_atasan(cls):
        """Get default superior based on role hierarchy"""
        # First try to find an ATASAN
        atasan = cls.query.filter_by(role=UserRole.ATASAN).first()
        
        # If no ATASAN, try ADMIN
        if not atasan:
            atasan = cls.query.filter_by(role=UserRole.ADMIN).first()
            
        # If still no superior, try SUPERADMIN
        if not atasan:
            atasan = cls.query.filter_by(role=UserRole.SUPERADMIN).first()
            
        return atasan.id if atasan else None
    
    @property
    def profile_picture_url(self):
        if self.foto_profil:
            profile_path = os.path.join(current_app.static_folder, 'uploads', 'profile', self.foto_profil)
            if os.path.exists(profile_path):
                return url_for('static', filename=f'uploads/profile/{self.foto_profil}')
        return url_for('static', filename='images/profile-default.png')
    
    @property
    def foto_profil_url(self):
        if not self.foto_profil:
            return url_for('static', filename='images/profile-default.png')
        
        # Check if file exists in either old or new path
        possible_paths = [
            os.path.join(current_app.static_folder, 'uploads', 'profile', self.foto_profil),
            os.path.join(current_app.static_folder, 'uploads', self.foto_profil),
            os.path.join(current_app.static_folder, self.foto_profil)
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                # Return the correct relative path
                if 'uploads/profile/' in path:
                    return url_for('static', filename=f'uploads/profile/{self.foto_profil}')
                elif 'uploads/' in path:
                    return url_for('static', filename=f'uploads/{self.foto_profil}')
                return url_for('static', filename=self.foto_profil)
        
        return url_for('static', filename='images/profile-default.png')
    
    @validates('role')
    def validate_role(self, key, role):
        if isinstance(role, str):
            return UserRole.from_string(role)
        return role

    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise ValueError("Invalid email format")
        return email.lower()

    @validates('jenis_kelamin')
    def validate_gender(self, key, gender):
        if gender and gender.upper() not in ['L', 'P']:
            raise ValueError("Gender must be 'L' or 'P'")
        return gender.upper()

    def set_password(self, password):
        """Set password with secure hashing"""
        self.password = generate_password_hash(password, method='pbkdf2:sha256')
        self.last_password_change = datetime.utcnow()

    def check_password(self, password):
        """Check password against stored hash"""
        return check_password_hash(self.password, password)

    def update_login_info(self):
        """Update login timestamps and reset attempts"""
        self.last_login = datetime.now(timezone.utc)
        self.reset_login_attempts()
        db.session.commit()

    def increment_login_attempts(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
        db.session.commit()

    def reset_login_attempts(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()

    @staticmethod
    def generate_salt(length=16):
        """Generate a cryptographically secure random salt"""
        return secrets.token_urlsafe(length)

    def generate_email_token(self):
        """Generate secure email verification token"""
        s = URLSafeTimedSerializer(
            secret_key=current_app.config['SECRET_KEY'],
            salt='email-verify-' + current_app.config['SECURITY_PASSWORD_SALT']
        )
        return s.dumps({
            'user_id': self.id,
            'email': self.email,  # Tambahkan email untuk verifikasi tambahan
            'timestamp': datetime.utcnow().timestamp()
        })

    def generate_email_verification_token(self):
        """Generate email verification token"""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id, 'email': self.email})


    @staticmethod
    def verify_email_token(token):
        """Verify email token and return user if valid"""
        from utils.tokens import verify_email_token
        
        token_data = verify_email_token(token)
        if not token_data:
            return None

        # Find user with security filters
        user = User.query.filter(
            User.id == token_data['user_id'],
            User.email == token_data['email'],  # Verify email matches
            User.is_active == True
        ).first()

        if not user:
            current_app.logger.warning(f"User not found or inactive: {token_data.get('user_id')}")
            
        return user
    
    def generate_password_reset_token(self):
        """Generate secure password reset token"""
        s = URLSafeTimedSerializer(
            secret_key=current_app.config['SECRET_KEY'],
            salt=current_app.config['SECURITY_PASSWORD_SALT'] + '-password-reset'
        )
        return s.dumps(
            {'user_id': self.id, 'salt': self.generate_salt()},
            salt=current_app.config['SECURITY_PASSWORD_SALT']
        )

    @staticmethod
    def verify_password_reset_token(token):
        """Verify password reset token with additional security checks"""
        s = URLSafeTimedSerializer(
            secret_key=current_app.config['SECRET_KEY'],
            salt=current_app.config['SECURITY_PASSWORD_SALT'] + '-password-reset'
        )
        
        try:
            data = s.loads(
                token,
                max_age=current_app.config['PASSWORD_RESET_TOKEN_EXPIRATION'].total_seconds(),
                salt=current_app.config['SECURITY_PASSWORD_SALT']
            )
            
            # Additional security checks
            if 'user_id' not in data or 'salt' not in data:
                return None
                
            return User.query.get(data['user_id'])
        except:
            return None


    def is_account_locked(self):
        """Check if account is temporarily locked"""
        return self.locked_until and self.locked_until > datetime.utcnow()

    def password_expired(self):
        """Check if password needs to be changed"""
        if not self.last_password_change:
            return False
        return (datetime.utcnow() - self.last_password_change) > timedelta(days=90)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # Set default values
        self.nip = kwargs.get('nip', '')
        self.jabatan = kwargs.get('jabatan', '')
        self.golongan = kwargs.get('golongan', '')
        self.alamat = kwargs.get('alamat', '')

    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role.value,
            'jabatan': self.jabatan,
            'sisa_cuti': self.sisa_cuti,
            'foto_profil': self.foto_profil,
            'email_verified': self.email_verified,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<User {self.username} ({self.role.value})>'


class Cuti(db.Model):
    __tablename__ = 'cuti'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    atasan_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Leave details
    jenis_cuti = db.Column(db.Enum(JenisCuti), nullable=False)
    tanggal_mulai = db.Column(db.Date, nullable=False)
    tanggal_selesai = db.Column(db.Date, nullable=False)
    jumlah_hari = db.Column(db.Integer, nullable=False)
    perihal_cuti = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum(CutiStatus), default=CutiStatus.PENDING, nullable=False, index=True)
    
    # Additional info
    alasan_penolakan = db.Column(db.Text)
    is_cancelled = db.Column(db.Boolean, default=False)
    cancel_reason = db.Column(db.String(255))
    emergency_contact = db.Column(db.String(100))
    contact_number = db.Column(db.String(20))
    address_during_leave = db.Column(db.Text)
    lampiran = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    
    # Tracking
    status_history = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at = db.Column(db.DateTime)

    # Relationships
    pemohon = db.relationship('User', foreign_keys=[user_id], back_populates='cuti_diajukan')
    penyetuju = db.relationship('User', foreign_keys=[atasan_id], back_populates='cuti_disetujui')

    __table_args__ = (
        Index('idx_cuti_user', 'user_id'),
        Index('idx_cuti_atasan', 'atasan_id'),
        Index('idx_cuti_status', 'status'),
        Index('idx_cuti_tanggal', 'tanggal_mulai', 'tanggal_selesai'),
        CheckConstraint('tanggal_mulai <= tanggal_selesai', name='check_dates'),
        CheckConstraint('jumlah_hari > 0', name='check_positive_days'),
    )

    # Business logic methods
    @property
    def lampiran_url(self):
        if not self.lampiran:
            return None
        
        # Handle different path formats
        filename = self.lampiran.split('uploads/')[-1] if 'uploads/' in self.lampiran else self.lampiran
        file_path = os.path.join(current_app.static_folder, 'uploads', filename)
        
        if os.path.exists(file_path):
            return url_for('static', filename=f'uploads/{filename}')
        return None

    @property 
    def lampiran_exists(self):
        if not self.lampiran:
            return False
        filename = self.lampiran.split('uploads/')[-1] if 'uploads/' in self.lampiran else self.lampiran
        file_path = os.path.join(current_app.static_folder, 'uploads', filename)
        return os.path.exists(file_path)
        
    @validates('jumlah_hari')
    def validate_jumlah_hari(self, key, value):
        if value <= 0:
            raise ValueError("Jumlah hari cuti harus lebih dari 0")
        return value
    
    def calculate_days(self):
        """Calculate working days between dates (excluding weekends)"""
        if self.tanggal_mulai and self.tanggal_selesai:
            delta = self.tanggal_selesai - self.tanggal_mulai
            days = delta.days + 1  # Inclusive
            
            # Subtract weekends
            full_weeks, remainder = divmod(days, 7)
            weekend_days = full_weeks * 2
            if remainder:
                start_day = self.tanggal_mulai.weekday()
                weekend_days += sum(1 for day in range(start_day, start_day + remainder)
                                  if day % 7 in (5, 6))  # 5=Saturday, 6=Sunday
            
            self.jumlah_hari = days - weekend_days

    def approve(self, approved_by: int, notes: str = None):
        self.status = CutiStatus.APPROVED
        self.add_status_history(CutiStatus.APPROVED, approved_by, notes)
        
    def reject(self, rejected_by: int, reason: str, notes: str = None):
        self.status = CutiStatus.REJECTED
        self.alasan_penolakan = reason
        self.add_status_history(CutiStatus.REJECTED, rejected_by, notes)
        
    def cancel(self, cancelled_by: int, reason: str):
        self.status = CutiStatus.CANCELLED
        self.is_cancelled = True
        self.cancel_reason = reason
        self.cancelled_at = datetime.utcnow()
        self.add_status_history(CutiStatus.CANCELLED, cancelled_by, reason)
    
    def add_status_history(self, status: CutiStatus, by_user: int, notes: str = None):
        if not self.status_history:
            self.status_history = []
            
        self.status_history.append({
            'status': status.value,
            'by': by_user,
            'at': datetime.utcnow().isoformat(),
            'notes': notes
        })

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.pemohon.to_dict(),
            'atasan': self.penyetuju.to_dict() if self.penyetuju else None,
            'jenis_cuti': self.jenis_cuti.value,
            'tanggal_mulai': self.tanggal_mulai.isoformat(),
            'tanggal_selesai': self.tanggal_selesai.isoformat(),
            'jumlah_hari': self.jumlah_hari,
            'perihal_cuti': self.perihal_cuti,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'status_history': self.status_history,
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    notification_type = db.Column(db.String(20), default='INFO')  # INFO, WARNING, ALERT
    is_read = db.Column(db.Boolean, default=False)
    priority = db.Column(db.Integer, default=0)  # 0=normal, 1=important, 2=critical
    link = db.Column(db.String(255))
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=func.now())
    
    user = db.relationship('User', back_populates='notifications')


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=True)
    model_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    
    user = db.relationship('User', back_populates='audit_logs')
    
    @classmethod
    def log(cls, user_id, action, model=None, model_id=None, description=None, ip_address=None):
        """Create a new audit log entry"""
        log_entry = cls(
            user_id=user_id,
            action=action,
            model=model,
            model_id=model_id,
            description=description,
            ip_address=ip_address
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry


class LoginLog(db.Model):
    __tablename__ = 'login_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    success = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    
    user = db.relationship('User', backref='login_logs')

# Event listeners
@event.listens_for(User.password, 'set', retval=True)
def hash_password(target, value, oldvalue, initiator):
    """
    Auto-hash password saat di-set, dengan proteksi rekursi
    Return value yang sudah di-hash
    """
    if (value and  # Pastikan tidak None/empty
        value != oldvalue and  # Hanya jika berubah
        not value.startswith('pbkdf2:sha256:') and  # Skip jika sudah di-hash
        isinstance(value, str)):  # Hanya proses string
        
        hashed = generate_password_hash(value)
        target.last_password_change = datetime.utcnow()
        return hashed
    
    return value


@event.listens_for(Cuti, 'before_insert')
@event.listens_for(Cuti, 'before_update')
def calculate_leave_days(mapper, connection, target):
    target.calculate_days()