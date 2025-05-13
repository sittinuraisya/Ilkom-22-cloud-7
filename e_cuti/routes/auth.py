from flask import Blueprint, request, render_template, flash, redirect, url_for, jsonify, current_app, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.exceptions import BadRequest
from werkzeug.security import generate_password_hash
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, timedelta
from markupsafe import Markup
import logging

# Local imports
from models import User, UserRole
from extensions import db
from services.auth import (
    authenticate_user,
    handle_failed_login,
    register_new_user,
    is_account_locked
)
from services.email import send_verification_email, send_password_reset_email
from utils.validators import validate_registration_form
from utils.decorators import logout_required
from utils.security_utils import generate_secure_token, verify_secure_token
from controllers.auth_controller import AuthController

auth_bp = Blueprint('auth', __name__, template_folder='templates/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip().lower()
            password = request.form.get('password', '')
            remember = 'remember' in request.form  # Check if remember me was checked

            # Input validation
            if not username or not password:
                flash('Username/email dan password harus diisi', 'error')
                return render_template('auth/login.html')

            user = User.query.filter(
                (func.lower(User.username) == username) |
                (func.lower(User.email) == username)
            ).first()

            if not user:
                current_app.logger.warning(f"Login attempt failed for non-existent user: {username}")
                flash('Username/email atau password salah', 'error')
                return render_template('auth/login.html')

            # Check email verification
            if not user.email_verified:
                token = user.generate_email_token()
                verify_url = url_for('auth.verify_email', token=token, _external=True)
                
                flash(Markup(
                    f'Email belum diverifikasi. Silakan cek inbox/spam di <a href="https://mail.google.com/mail/u/0/#search/from%3A{current_app.config["MAIL_USERNAME"]}" target="_blank" style="color: #2563eb; text-decoration: underline;">Gmail Anda</a> '
                    f'atau <a href="#" onclick="resendVerification(event, \'{user.email}\')" style="color: #2563eb; text-decoration: underline;">kirim ulang email verifikasi</a>.'
                ), 'error')
                return render_template('auth/login.html')

            # Verify password
            if not user.check_password(password):
                user.increment_login_attempts()
                db.session.commit()
                current_app.logger.warning(f"Failed login attempt for user: {user.username}")
                flash('Username/email atau password salah', 'error')
                return render_template('auth/login.html')

            # Successful login - Tambahkan parameter remember
            login_user(user, remember=remember)  # Ini yang diperbaiki
            user.reset_login_attempts()
            db.session.commit()
            
            current_app.logger.info(f"User logged in: {user.username} (Role: {user.role.name})")
            flash('Login berhasil!', 'success')

            return redirect_based_on_role(user.role)

        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}", exc_info=True)
            flash('Terjadi kesalahan sistem saat login', 'error')
            return render_template('auth/login.html')

    return render_template('auth/login.html')

def redirect_based_on_role(user_role):
    """Handle dashboard redirection based on user role"""
    role_endpoints = {
        UserRole.SUPERADMIN: 'admin.superadmin_dashboard',
        UserRole.ADMIN: 'admin.admin_dashboard',
        UserRole.ATASAN: 'atasan.dashboard',
        UserRole.PEGAWAI: 'pegawai.dashboard'
    }
    return redirect(url_for(role_endpoints.get(user_role, 'auth.login')))

@auth_bp.route('/register', methods=['GET', 'POST'])
@logout_required
def register():
    """Handle new user registration with immediate redirect if user exists"""
    if request.method == 'POST':
        form_data = {
            'username': request.form.get('username', '').strip(),
            'email': request.form.get('email', '').lower().strip(),
            'password': request.form.get('password', ''),
            'confirm_password': request.form.get('confirm_password', ''),
            'full_name': request.form.get('full_name', '').strip(),
            'phone': request.form.get('phone', '').strip()
        }

        # Validasi form dasar
        errors = validate_registration_form(form_data)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html', form_data=form_data)

        # Cek duplikat username/email SEBELUM membuat user
        existing_user = User.query.filter(
            (func.lower(User.username) == form_data['username'].lower()) | 
            (func.lower(User.email) == form_data['email'].lower())
        ).first()

        if existing_user:
            if existing_user.username.lower() == form_data['username'].lower():
                flash('Username sudah terdaftar', 'error')
            else:
                flash('Email sudah terdaftar', 'error')
            return redirect(url_for('auth.login'))  # Langsung redirect ke login

        try:
            # Buat user baru
            user = User(
                username=form_data['username'],
                email=form_data['email'],
                password=form_data['password'],
                full_name=form_data['full_name'],
                phone=form_data['phone'],
                role=UserRole.PEGAWAI,
                atasan_id=User.get_default_atasan()
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Kirim email verifikasi
            send_verification_email(user)
            
            flash('Registrasi berhasil! Silakan cek email untuk verifikasi.', 'success')
            return redirect(url_for('auth.login'))

        except IntegrityError:
            db.session.rollback()
            flash('Terjadi kesalahan, username/email mungkin sudah terdaftar', 'error')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {str(e)}")
            flash('Terjadi kesalahan sistem saat registrasi', 'error')
            return redirect(url_for('auth.login'))

    # GET request - tampilkan form
    return render_template('auth/register.html')

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    try:
        user = User.verify_email_token(token)
        
        if not user:
            flash('Link verifikasi tidak valid atau kadaluarsa', 'error')
            return redirect(url_for('auth.login'))
        
        if user.email_verified:
            flash('Email sudah diverifikasi sebelumnya', 'info')
        else:
            user.email_verified = True
            user.email_verified_at = datetime.utcnow()
            user.is_active = True  # Ensure account is activated
            db.session.commit()
            
            if user.role == UserRole.ADMIN:
                flash('Verifikasi admin berhasil! Akun Anda sekarang aktif.', 'success')
            else:
                flash('Email berhasil diverifikasi!', 'success')

        return redirect(url_for('auth.login'))

    except Exception as e:
        current_app.logger.error(f"Email verification error for token {token}: {str(e)}")
        flash('Terjadi kesalahan saat verifikasi email', 'error')
        return redirect(url_for('auth.register'))

@auth_bp.route('/logout')
@login_required
def logout():
    """Secure user logout with session cleanup"""
    try:
        username = current_user.username
        
        # 1. Logout user through Flask-Login
        logout_user()
        
        # 2. Clear all session data
        session.clear()
        
        # 3. Create new empty session
        session.new = True
        
        # 4. Invalidate session cookie
        response = redirect(url_for('auth.login'))
        response.delete_cookie('session')
        response.delete_cookie('remember_token')
        
        # 5. Clear client-side cache headers
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        
        current_app.logger.info(f"User logged out: {username}")
        flash('Anda telah logout.', 'info')
        return response
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}", exc_info=True)
        flash('Terjadi kesalahan saat logout', 'error')
        return redirect(url_for('main.index'))

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    # Get data from form instead of JSON
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        flash('Semua field harus diisi', 'error')
        return redirect(url_for('profile.edit_profil'))
    
    if new_password != confirm_password:
        flash('Password baru dan konfirmasi password tidak cocok', 'error')
        return redirect(url_for('profile.edit_profil'))
    
    if not current_user.check_password(current_password):
        flash('Password saat ini salah', 'error')
        return redirect(url_for('profile.edit_profil'))
    
    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password berhasil diubah', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password change error: {str(e)}")
        flash('Gagal mengubah password', 'error')
    
    return redirect(url_for('profile.edit_profil'))

# Rate limiting implementation
def check_rate_limit(request):
    """Basic rate limiting implementation"""
    if not hasattr(current_app, 'rate_limit_data'):
        current_app.rate_limit_data = {}
    
    ip = request.remote_addr
    now = datetime.now()
    
    if ip not in current_app.rate_limit_data:
        current_app.rate_limit_data[ip] = {
            'count': 1,
            'last_request': now
        }
        return True
    
    time_since_last = now - current_app.rate_limit_data[ip]['last_request']
    
    # Reset count if more than 1 minute since last request
    if time_since_last > timedelta(minutes=1):
        current_app.rate_limit_data[ip] = {
            'count': 1,
            'last_request': now
        }
        return True
    
    # Allow up to 5 requests per minute
    if current_app.rate_limit_data[ip]['count'] < 5:
        current_app.rate_limit_data[ip]['count'] += 1
        current_app.rate_limit_data[ip]['last_request'] = now
        return True
    
    return False

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@logout_required
def forgot_password():
    """Secure password reset request with rate limiting"""
    if request.method == 'POST':
        # Rate limiting check
        if not check_rate_limit(request):
            flash('Terlalu banyak permintaan. Silakan coba lagi nanti.', 'error')
            return render_template('auth/forgot_password.html')

        email = request.form.get('email', '').lower().strip()
        user = User.query.filter_by(email=email).first()

        if user:
            try:
                # Generate and send reset token
                token = user.generate_reset_token()
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                
                # Log the reset request
                current_app.logger.info(f"Password reset requested for: {email}")
                
                send_password_reset_email(user.email, reset_url)
                flash('Instruksi reset password telah dikirim ke email Anda', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                current_app.logger.error(f"Password reset error: {str(e)}", exc_info=True)
                flash('Gagal mengirim email reset password', 'error')
        else:
            # Don't reveal whether email exists
            current_app.logger.info(f"Password reset attempt for unknown email: {email}")
            flash('Jika email terdaftar, instruksi reset akan dikirim', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@logout_required
def reset_password(token):
    """Handle password reset with token validation"""
    user = User.verify_reset_token(token)
    if not user:
        flash('Token reset password tidak valid atau kadaluarsa', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Password dan konfirmasi tidak cocok', 'error')
            return redirect(url_for('auth.reset_password', token=token))

        try:
            user.set_password(password)
            db.session.commit()
            flash('Password berhasil direset. Silakan login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Password reset error: {str(e)}")
            flash('Gagal mereset password', 'error')

    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email tidak valid'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'Email tidak terdaftar'}), 404

    if user.email_verified:
        return jsonify({'success': False, 'message': 'Email sudah diverifikasi'}), 400

    try:
        send_verification_email(user)
        return jsonify({'success': True, 'message': 'Email verifikasi dikirim ulang'})
    except Exception as e:
        current_app.logger.error(f"Resend verification error: {str(e)}")
        return jsonify({'success': False, 'message': 'Gagal mengirim email'}), 500
