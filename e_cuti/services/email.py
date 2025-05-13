from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, current_app
from flask_mail import Message
from extensions import mail
from models import User, db
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
import logging
from config import Config
from utils.security_utils import generate_secure_token

logger = logging.getLogger(__name__)

serializer = URLSafeTimedSerializer(Config.SECRET_KEY)

def generate_token(email, salt=None):
    """Generate timed token untuk email"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=salt)

def verify_token(token, salt=None, max_age=3600):
    """Verifikasi token dengan expiry"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=salt, max_age=max_age)
        return email
    except Exception as e:
        logging.error(f"Token verification failed: {str(e)}")
        return None

def send_email(to, subject, template, **kwargs):
    """
    Base email sending function
    
    Args:
        to: Email recipient or list of recipients
        subject: Email subject
        template: Base template name (without .html/.txt)
        **kwargs: Template variables
    """
    try:
        # Ensure recipients is always a list
        recipients = [to] if isinstance(to, str) else to
        
        msg = Message(
            subject=subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=recipients
        )
        
        # Render both HTML and plaintext versions
        msg.html = render_template(f'emails/{template}.html', **kwargs)
        msg.body = render_template(f'emails/{template}.txt', **kwargs)
        
        if current_app.config['MAIL_SUPPRESS_SEND']:
            logging.info("Email suppressed (would send to %s): %s", recipients, msg.html)
            return True
            
        mail.send(msg)
        logging.info("Email sent to %s - Subject: %s", recipients, subject)
        return True
        
    except Exception as e:
        logging.error("Failed to send email to %s: %s", recipients, str(e), exc_info=True)
        raise EmailSendError(f"Failed to send email: {str(e)}")



def send_verification_email(user):
    """Send email verification with proper error handling"""
    try:
        token = user.generate_email_token()
        verify_url = url_for(
            'auth.verify_email', 
            token=token,
            _external=True
        )
        
        msg = Message(
            "Verifikasi Email Anda",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email]
        )
        
        msg.html = render_template(
            "emails/verify_email.html",
            user=user,
            verify_url=verify_url,
            expiry_hours=24  # Match token expiration
        )
        
        mail.send(msg)
        
        current_app.logger.info(f"Verification email sent to {user.email}")
        
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        raise EmailSendError(f"Failed to send verification email: {str(e)}")


class EmailSendError(Exception):
    """Custom exception for email sending failures"""
    pass


def send_admin_verification_email(user):
    """Send verification email specifically for admin"""
    token = user.generate_email_token()
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    
    return send_email(
        to=user.email,
        subject="Verifikasi Akun Admin E-Cuti",
        template='admin_verification',
        user=user,
        verify_url=verify_url,
        current_year=datetime.now().year
    )

def send_welcome_email(user, plain_password):
    """Send welcome email specifically for admin"""
    login_url = url_for('auth.login', _external=True)
    
    return send_email(
        to=user.email,
        subject="Selamat Datang Admin E-Cuti",
        template='admin_welcome',
        user=user,
        password=plain_password,
        login_url=login_url,
        current_year=datetime.now().year
    )

def send_admin_status_email(user, action_by, is_active):
    """Kirim email notifikasi status akun"""
    subject = "Akun Admin {} Dinonaktifkan".format("Telah" if not is_active else "Diaktifkan Kembali")
    
    msg = Message(
        subject=subject,
        recipients=[user.email],
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    
    msg.html = render_template(
        "emails/admin_status_change.html",
        user=user,
        action_by=action_by,
        is_active=is_active
    )
    
    try:
        mail.send(msg)
        current_app.logger.info(f"Status email sent to {user.email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send status email: {str(e)}")

def send_admin_password_reset_email(user, new_password):
    """Kirim email reset password"""
    msg = Message(
        subject="Password Admin Direset",
        recipients=[user.email],
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    
    msg.html = render_template(
        "emails/admin_password_reset.html",
        user=user,
        new_password=new_password,
        login_url=url_for('auth.login', _external=True)
    )
    
    try:
        mail.send(msg)
        current_app.logger.info(f"Password reset email sent to {user.email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {str(e)}")

def send_password_reset_email(email, reset_url):
    user = User.query.filter_by(email=email).first()
    if not user:
        current_app.logger.warning(f"Password reset requested for non-existent email: {email}")
        return False

    expiration_hours = current_app.config.get('RESET_PASSWORD_EXPIRATION', 24)
    
    msg = Message(
        subject="Permintaan Reset Password - Sistem e-Cuti",
        recipients=[email],
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    
    # Render HTML version
    msg.html = render_template(
        "emails/password_reset.html",
        user=user,
        reset_url=reset_url,
        expiration_hours=expiration_hours,
        current_year=datetime.now().year
    )
    
    # Plain text version
    msg.body = f"""
    Halo {user.full_name},
    
    Kami menerima permintaan reset password untuk akun Anda.
    Silakan kunjungi link berikut untuk melanjutkan:
    
    {reset_url}
    
    Link ini akan kadaluarsa dalam {expiration_hours} jam.
    
    Jika Anda tidak meminta reset password, abaikan email ini.
    """
    
    try:
        mail.send(msg)
        current_app.logger.info(f"Password reset email sent to {email}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {str(e)}")
        return False

def send_cuti_notification_email(subject, recipients, template, **kwargs):
    try:
        msg = Message(
            subject=subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=recipients
        )
        msg.html = render_template(template, **kwargs)
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {str(e)}")
        return False
    
def send_leave_approval_notification(user, leave_request):
    """Kirim notifikasi approval cuti"""
    return send_email(
        to=user.email,
        subject=f"Status Cuti Anda: {leave_request.status}",
        template='leave_approval',
        user=user,
        leave=leave_request,
        approval_date=datetime.now().strftime('%d %B %Y')
    )

def send_otp_email(user, otp_code):
    """Kirim OTP untuk 2FA"""
    return send_email(
        to=user.email,
        subject="Kode OTP Anda",
        template='otp_code',
        username=user.username,
        otp_code=otp_code,
        expiry_minutes=5
    )

def generate_verification_token(email):
    """Generate email verification token"""
    return serializer.dumps(email, salt='email-verify')

def verify_email_token(token, max_age=86400):
    """Verify email token and return email if valid"""
    try:
        email = serializer.loads(token, salt='email-verify', max_age=max_age)
        return email
    except:
        return None
    
def send_email(to, subject, template, **kwargs):
    """Send email using Flask-Mail with error handling"""
    try:
        msg = Message(
            subject=subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[to]
        )
        
        # Render both HTML and plain text versions
        msg.html = render_template(f"emails/{template}.html", **kwargs)
        msg.body = render_template(f"emails/{template}.txt", **kwargs)
        
        # Add attachments if any
        if 'attachments' in kwargs:
            for attachment in kwargs['attachments']:
                with current_app.open_resource(attachment['path']) as fp:
                    msg.attach(
                        filename=attachment['filename'],
                        content_type=attachment['content_type'],
                        data=fp.read()
                    )
        
        mail.send(msg)
        current_app.logger.info(f"Email sent to {to} with subject '{subject}'")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {to}: {str(e)}")
        return False

def send_leave_status_email(user, status, approver, leave_details, rejection_reason=None):
    """Send leave status notification email"""
    context = {
        'user': user,
        'status': status,
        'approver': approver,
        'leave': leave_details,
        'rejection_reason': rejection_reason,
        'current_year': datetime.now().year
    }
    
    subject = f"Status Pengajuan Cuti: {status}"
    return send_email(
        to=user.email,
        subject=subject,
        template='leave_status',
        **context
    )
        