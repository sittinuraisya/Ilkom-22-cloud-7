from flask import Blueprint, render_template, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import UserRole, db

common_bp = Blueprint('common', __name__)

# Tambahkan route untuk home
@common_bp.route('/')
def home():
    return render_template('common/home.html')

@common_bp.route('/dashboard')
@login_required
def dashboard():
    """Redirect langsung ke dashboard role masing-masing"""
    if current_user.role == UserRole.SUPERADMIN:
        return redirect(url_for('admin.super_dashboard'))
    elif current_user.role == UserRole.ADMIN:
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == UserRole.ATASAN:
        return redirect(url_for('atasan.dashboard'))
    else:
        return redirect(url_for('pegawai.dashboard'))

# Error handlers
@common_bp.app_errorhandler(400)
def bad_request(error):
    return render_template('errors/400.html'), 400

@common_bp.app_errorhandler(401)
def unauthorized(error):
    return render_template('errors/401.html'), 401

@common_bp.app_errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403

@common_bp.app_errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@common_bp.app_errorhandler(405)
def method_not_allowed(error):
    return render_template('errors/405.html'), 405

@common_bp.app_errorhandler(500)
def internal_server_error(error):
    return render_template('errors/500.html'), 500

@common_bp.route('/maintenance')
def maintenance():
    return render_template('errors/maintenance.html'), 503

@common_bp.app_errorhandler(503)
def service_unavailable(error):
    return render_template('errors/maintenance.html'), 503