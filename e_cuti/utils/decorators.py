from functools import wraps
from flask import abort, redirect, url_for, flash, current_app, request
from flask_login import current_user
from models import User, UserRole

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))

            # Convert all roles to enum for comparison
            allowed_roles = set()
            for role in roles:
                if isinstance(role, str):
                    try:
                        allowed_roles.add(UserRole[role.upper()])
                    except KeyError:
                        continue
                elif isinstance(role, UserRole):
                    allowed_roles.add(role)

            # Convert user role if it's a string
            user_role = current_user.role
            if isinstance(user_role, str):
                try:
                    user_role = UserRole[user_role.upper()]
                except KeyError:
                    flash('Role tidak valid', 'error')
                    return redirect(url_for('common.home'))

            if not allowed_roles or user_role not in allowed_roles:
                flash('Akses ditolak: Anda tidak memiliki izin', 'error')
                current_app.logger.warning(
                    f"Unauthorized access attempt by {current_user.username} (role: {current_user.role})"
                )
                return redirect(url_for('common.home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def logout_required(func):
    """Decorator untuk memastikan user sudah logout sebelum mengakses route"""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('common.dashboard'))
        return func(*args, **kwargs)
    return decorated_function

def maintenance_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_app.config['MAINTENANCE_MODE']:
            return redirect(url_for('common.maintenance'))
        return f(*args, **kwargs)
    return decorated_function