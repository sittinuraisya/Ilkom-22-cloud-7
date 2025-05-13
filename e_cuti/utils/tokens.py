# app/utils/tokens.py
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app
from datetime import datetime

def generate_email_token(user):
    """Generate email verification token for a user object"""
    s = URLSafeTimedSerializer(
        secret_key=current_app.config['SECRET_KEY'],
        salt='email-verify-' + current_app.config['SECURITY_PASSWORD_SALT']
    )
    return s.dumps({
        'user_id': user.id,
        'email': user.email,
        'timestamp': datetime.utcnow().isoformat()
    })

def verify_email_token(token):
    """Verify email token with enhanced security"""
    if not token:
        return None

    try:
        s = URLSafeTimedSerializer(
            secret_key=current_app.config['SECRET_KEY'],
            salt='email-verify-' + current_app.config['SECURITY_PASSWORD_SALT']
        )
        
        # Verify token with 24 hour timeout
        data = s.loads(token, max_age=86400)  # 24 hours in seconds
        
        # Validate data structure
        required_fields = ['user_id', 'email', 'timestamp']
        if not all(field in data for field in required_fields):
            current_app.logger.warning("Token missing required fields")
            return None

        return data

    except SignatureExpired:
        current_app.logger.warning("Token verification expired")
        return None
    except BadSignature:
        current_app.logger.warning("Invalid token signature")
        return None
    except Exception as e:
        current_app.logger.error(f"Token verification error: {str(e)}")
        return None