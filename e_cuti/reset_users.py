from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    # 1. Hapus semua user lama
    db.session.query(User).delete()
    
    # 2. Buat user baru dengan password yang di-hash ulang
    users = [
        ("superadmin", "superadmin@example.com", "password123", "SUPERADMIN"),
        ("admin", "admin@example.com", "password123", "ADMIN"),
        ("atasan", "atasan@example.com", "password123", "ATASAN"),
        ("pegawai", "pegawai@example.com", "password123", "PEGAWAI")
    ]
    
    for username, email, password, role in users:
        user = User(
            username=username,
            email=email,
            role=role,
            is_active=True
        )
        user.set_password(password)  # Hash dengan metode baru
        db.session.add(user)
    
    db.session.commit()
    print("✅ User berhasil di-reset!")