from flask import Blueprint, request, render_template, flash, redirect, url_for
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from extensions import db
from models import User
from services.email import send_verification_email, send_password_reset_email
import logging

logger = logging.getLogger(__name__)

def authenticate_user(username, password):
    """
    Authenticate user with username/email and password
    Returns (user, error_message) tuple
    """
    user = User.query.filter(
        (func.lower(User.username) == func.lower(username)) | 
        (func.lower(User.email) == func.lower(username))
    ).first()
    
    if not user:
        logger.warning(f"Login attempt for non-existent user: {username}")
        return None, "Username/email atau password salah"
    
    if not check_password_hash(user.password, password):
        logger.warning(f"Failed login for user: {user.username}")
        return None, "Username/email atau password salah"
    
    if is_account_locked(user):
        remaining_time = user.locked_until - datetime.utcnow()
        logger.warning(f"Locked account attempt: {user.username}")
        return None, f"Akun terkunci. Coba lagi dalam {int(remaining_time.total_seconds() / 60)} menit"
    
    if not user.email_verified:
        logger.warning(f"Unverified email attempt: {user.username}")
        return None, "Email belum diverifikasi. Silakan cek email Anda"
    
    return user, None

def is_account_locked(user):
    """Check if user account is temporarily locked"""
    return user.locked_until and user.locked_until > datetime.utcnow()

def handle_failed_login(user):
    """Handle failed login attempts and lock account if necessary"""
    user.failed_login_attempts += 1
    
    if user.failed_login_attempts >= 5:
        user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        logger.warning(f"Account locked: {user.username}")
    
    db.session.commit()

def register_new_user(username, email, password, full_name, phone, role):
    """
    Create and register new user
    Returns User object
    """
    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        full_name=full_name,
        phone=phone,
        role=role,
        email_verified=False,
        created_at=datetime.utcnow(),
        last_password_change=datetime.utcnow()
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Send verification email
    try:
        send_verification_email(user)
        logger.info(f"New user registered: {username}")
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
    
    return user

def initiate_password_reset(email):
    """
    Initiate password reset process
    Returns (success, message)
    """
    user = User.query.filter_by(email=email.lower()).first()
    if not user:
        logger.warning(f"Password reset attempt for non-existent email: {email}")
        return False, "Email tidak terdaftar"
    
    try:
        token = user.generate_reset_token()
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        send_password_reset_email(user.email, reset_url)
        logger.info(f"Password reset initiated for: {user.email}")
        return True, "Instruksi reset password telah dikirim ke email Anda"
    except Exception as e:
        logger.error(f"Password reset error for {email}: {str(e)}")
        return False, "Gagal mengirim email reset password"

def reset_user_password(token, new_password):
    """
    Reset user password with valid token
    Returns (success, message, user)
    """
    user = User.verify_reset_token(token)
    if not user:
        logger.warning("Invalid password reset token used")
        return False, "Token reset password tidak valid atau kadaluarsa", None
    
    try:
        user.set_password(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        db.session.commit()
        logger.info(f"Password reset successful for: {user.username}")
        return True, "Password berhasil direset", user
    except Exception as e:
        db.session.rollback()
        logger.error(f"Password reset failed for {user.username}: {str(e)}")
        return False, "Gagal mereset password", None