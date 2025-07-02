from models import db, User, Cuti
from werkzeug.security import generate_password_hash

def create_admin_user(username, email, password):
    """Business logic untuk membuat admin baru"""
    if User.query.filter((User.email == email) | (User.username == username)).first():
        return False, "User sudah ada"
    
    try:
        new_admin = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role='admin'
        )
        db.session.add(new_admin)
        db.session.commit()
        return True, "Admin berhasil dibuat"
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def get_admin_stats():
    """Mengambil data statistik untuk dashboard admin"""
    return {
        'total_pegawai': User.query.filter_by(role='pegawai').count(),
        'total_atasan': User.query.filter_by(role='atasan').count(),
        'cuti_pending': Cuti.query.filter_by(status='Pending').count(),
        'cuti_approved': Cuti.query.filter_by(status='Approved').count()
    }