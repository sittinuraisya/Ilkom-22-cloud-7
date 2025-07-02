from models import User
from extensions import db

class AuthController:
    @staticmethod
    def create_user(username, email, password, **kwargs):
        """Endpoint-safe user creation"""
        user = User(
            username=username,
            email=email,
            # Password akan di-hash otomatis oleh event listener
            password=password,  
            **kwargs
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update_password(user, new_password):
        """Update password dengan validasi"""
        if len(new_password) < 8:
            raise ValueError("Password minimal 8 karakter")
        
        user.password = new_password  # Memicu event listener
        db.session.commit()
    
        