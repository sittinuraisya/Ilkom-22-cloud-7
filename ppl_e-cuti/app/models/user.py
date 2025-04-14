from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

db = SQLAlchemy()

class UserRole(enum.Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    ATASAN = "atasan"
    PEGAWAI = "pegawai"

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    position = db.Column(db.String(100), nullable=True)
    atasan_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    sisa_cuti = db.Column(db.Integer, default=12)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    force_change_password = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    atasan = db.relationship('User', remote_side=[id], backref='bawahan')
    cuti_requests = db.relationship('CutiRequest', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class CutiStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELED = "canceled"

class CutiType(enum.Enum):
    TAHUNAN = "tahunan"
    SAKIT = "sakit"
    MELAHIRKAN = "melahirkan"
    PENTING = "penting"
    BESAR = "besar"

class CutiRequest(db.Model):
    __tablename__ = 'cuti_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cuti_type = db.Column(db.Enum(CutiType), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    attachment_path = db.Column(db.String(255), nullable=True)
    total_days = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(CutiStatus), default=CutiStatus.PENDING)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    calendar_event_id = db.Column(db.String(255), nullable=True)
    
    # Relationship
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def __repr__(self):
        return f'<CutiRequest {self.id}>'

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    entity = db.Column(db.String(100), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    
    # Relationship
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<AuditLog {self.id}>'

class Holiday(db.Model):
    __tablename__ = 'holidays'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False, unique=True)
    is_recurring = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Holiday {self.name}>'