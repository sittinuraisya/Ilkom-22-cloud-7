from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import func

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True} 

    id = db.Column(db.Integer, primary_key=True)
    nip = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(255))
    reset_token = db.Column(db.String(255))
    reset_token_expiry = db.Column(db.String(255))
    must_change_password = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(50))
    tempat_lahir = db.Column(db.String(100))
    tanggal_lahir = db.Column(db.String(100))
    jenis_kelamin = db.Column(db.String(20))
    golongan = db.Column(db.String(50))
    jabatan = db.Column(db.String(100))
    foto_profil = db.Column(db.String(255))
    total_cuti = db.Column(db.Integer, default=12)
    role = db.Column(db.String(50), default='pegawai')
    atasan_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Relasi atasan
    atasan = db.relationship('User', remote_side=[id], backref='subordinates')  # Menghubungkan dengan atasan
    created_at = db.Column(db.String(100), default='CURRENT_TIMESTAMP')

class Cuti(db.Model):
    __tablename__ = 'cuti'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    jenis_cuti = db.Column(db.String(100), nullable=False)
    tanggal_mulai = db.Column(db.Date, nullable=False)
    tanggal_selesai = db.Column(db.Date, nullable=False)
    jumlah_hari = db.Column(db.Integer)
    perihal_cuti = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    admin_notes = db.Column(db.Text)
    is_cancelled = db.Column(db.Boolean, default=False)
    cancel_reason = db.Column(db.String(255))
    cancelled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())
    lampiran = db.Column(db.String(255))
    user = db.relationship('User', backref='cuti')

    def __init__(self, **kwargs):
        # Convert string dates to date objects
        if 'tanggal_mulai' in kwargs:
            kwargs['tanggal_mulai'] = datetime.strptime(kwargs['tanggal_mulai'], '%Y-%m-%d').date()
        if 'tanggal_selesai' in kwargs:
            kwargs['tanggal_selesai'] = datetime.strptime(kwargs['tanggal_selesai'], '%Y-%m-%d').date()
        
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Cuti {self.jenis_cuti} - {self.user_id}>"

class LoginLog(db.Model):
    __tablename__ = 'login_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    username = db.Column(db.String(100))
    ip_address = db.Column(db.String(100))
    success = db.Column(db.Boolean)
    timestamp = db.Column(db.String(100), default='CURRENT_TIMESTAMP')

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    seen = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)