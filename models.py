from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role
        self.email = f"{username}@example.com"  # Sesuaikan dengan struktur database Anda
        
    def get_id(self):
        return str(self.id)