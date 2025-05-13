import re
from werkzeug.security import check_password_hash

class PasswordValidator:
    @staticmethod
    def validate_strength(password):
        """Validasi kekuatan password"""
        if len(password) < 8:
            return False, "Minimal 8 karakter"
        if not re.search(r"[A-Z]", password):
            return False, "Harus mengandung huruf besar"
        if not re.search(r"[0-9]", password):
            return False, "Harus mengandung angka"
        return True, "OK"

    @staticmethod
    def is_already_hashed(password):
        """Cek apakah string sudah di-hash"""
        return password.startswith('pbkdf2:sha256:')