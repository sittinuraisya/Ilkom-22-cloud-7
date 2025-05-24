import os
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import current_app
import string

def generate_secure_password(length=12):
    """Generate random secure password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))

def generate_secure_token(extra_data=None):
    """Generate a cryptographically secure token"""
    if extra_data is None:
        extra_data = {}
    
    random_part = secrets.token_urlsafe(32)
    timestamp = str(int(datetime.utcnow().timestamp()))
    data_hash = hashlib.sha256(
        (random_part + timestamp + current_app.config['SECRET_KEY']).encode()
    ).hexdigest()
    
    return f"{random_part}:{timestamp}:{data_hash}"

def verify_secure_token(token, max_age=3600):
    """Verify a secure token with timestamp checking"""
    try:
        parts = token.split(':')
        if len(parts) != 3:
            return False
            
        random_part, timestamp, data_hash = parts
        timestamp = int(timestamp)
        
        # Check token age
        if (datetime.utcnow() - datetime.fromtimestamp(timestamp)) > timedelta(seconds=max_age):
            return False
            
        # Verify hash
        expected_hash = hashlib.sha256(
            (random_part + str(timestamp) + current_app.config['SECRET_KEY']).encode()
        ).hexdigest()
        
        return secrets.compare_digest(data_hash, expected_hash)
    except:
        return False