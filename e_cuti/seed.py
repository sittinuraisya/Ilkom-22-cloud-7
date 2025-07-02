import os
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from app import create_app
from models import db, User, UserRole

app = create_app()

def create_initial_users():
    """Seed initial users with compatible password hashing"""
    with app.app_context():
        if User.query.count() > 0:
            print("Users already exist, skipping seeding.")
            return

        # Data user dengan referensi username
        users_data = [
            {
                "username": "superadmin",
                "email": "superadmin@example.com",
                "password": "password123",
                "full_name": "Super Administrator",
                "role": UserRole.SUPERADMIN,
                "jabatan": "Direktur Utama",
                "golongan": "I",
                "nip": "196808171985031001",
                "email_verified": True,
                "is_active": True,
                "atasan_ref": None
            },
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "password123",
                "full_name": "Administrator",
                "role": UserRole.ADMIN,
                "jabatan": "Manajer IT",
                "golongan": "III",
                "nip": "198209152006041002",
                "email_verified": True,
                "is_active": True,
                "atasan_ref": "superadmin"
            },
            {
                "username": "atasan",
                "email": "atasan@example.com",
                "password": "password123",
                "full_name": "Kepala Biro",
                "role": UserRole.ATASAN,
                "jabatan": "Manager",
                "golongan": "IV",
                "nip": "19820915200605003",              
                "email_verified": True,
                "is_active": True,
                "atasan_ref": "superadmin"
            },
            {
                "username": "pegawai",
                "email": "pegawai@example.com",
                "password": "password123",
                "full_name": "Staff Pegawai",
                "role": UserRole.PEGAWAI,
                "jabatan": "Staff",
                "golongan": "II",
                "nip": "196808171985011007",
                "email_verified": True,
                "is_active": True,
                "atasan_ref": "atasan"
            }
        ]

        user_id_map = {}
        created_users = []

        try:
            # Fase 1: Buat semua user dengan password yang di-hash dengan method yang benar
            for user_data in users_data:
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    jabatan=user_data["jabatan"],
                    golongan=user_data["golongan"],
                    nip=user_data["nip"],                   
                    email_verified=user_data["email_verified"],
                    is_active=user_data["is_active"],
                    created_at=datetime.now(timezone.utc)
                )
                
                # Gunakan method hashing yang sama dengan model User
                user.password = generate_password_hash(user_data["password"], method='pbkdf2:sha256')
                
                db.session.add(user)
                db.session.commit()
                
                user_id_map[user_data["username"]] = user.id
                created_users.append(user_data["username"])

            # Fase 2: Update atasan_id
            for user_data in users_data:
                if user_data["atasan_ref"]:
                    user = User.query.filter_by(username=user_data["username"]).first()
                    user.atasan_id = user_id_map[user_data["atasan_ref"]]
                    db.session.commit()

            print("\nUser Hierarchy:")
            print(f"1. {user_id_map['superadmin']}:superadmin (Top Level)")
            print(f"   ├── {user_id_map['admin']}:admin")
            print(f"   └── {user_id_map['atasan']}:atasan")
            print(f"       └── {user_id_map['pegawai']}:pegawai")

            print("\nLogin Credentials (all use 'password123'):")
            for username in created_users:
                print(f"- {username}")

        except Exception as e:
            db.session.rollback()
            print(f"Error during seeding: {str(e)}")
            raise

if __name__ == '__main__':
    create_initial_users()