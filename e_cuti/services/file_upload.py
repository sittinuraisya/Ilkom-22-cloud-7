import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from models import db

class FileUploadService:
    # Konfigurasi
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
    PROFILE_UPLOAD_FOLDER = 'uploads/profile'

    def __init__(self):
        self.upload_path = os.path.join(current_app.static_folder, self.PROFILE_UPLOAD_FOLDER)

    def allowed_file(self, filename):
        """Check if the file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def validate_file_size(self, file):
        """Validate file size doesn't exceed limit"""
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        return file_size <= self.MAX_FILE_SIZE

    def generate_filename(self, user_id, original_filename):
        """Generate secure and unique filename"""
        ext = original_filename.rsplit('.', 1)[1].lower()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"profile_{user_id}_{timestamp}.{ext}"

    def remove_old_file(self, old_filename):
        """Remove existing profile picture if exists"""
        if old_filename:
            old_path = os.path.join(current_app.static_folder, old_filename)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError as e:
                    current_app.logger.error(f"Failed to remove old file: {str(e)}")
                    return False
        return True

    def handle_profile_upload(self, file, user):
        """
        Main method to handle profile picture upload
        Returns: (success: bool, message: str)
        """
        # Validasi dasar
        if not file or file.filename == '':
            return False, 'Tidak ada file yang dipilih'

        if not self.allowed_file(file.filename):
            return False, 'Format file tidak didukung. Gunakan: PNG, JPG, JPEG'

        if not self.validate_file_size(file):
            return False, 'Ukuran file terlalu besar. Maksimal 2MB'

        try:
            # Hapus file lama jika ada
            self.remove_old_file(user.foto_profil)

            # Generate nama file baru
            filename = self.generate_filename(user.id, file.filename)
            secure_name = secure_filename(filename)

            # Pastikan folder upload ada
            os.makedirs(self.upload_path, exist_ok=True)

            # Simpan file
            filepath = os.path.join(self.upload_path, secure_name)
            file.save(filepath)

            # Update database dengan path relatif
            relative_path = os.path.join(self.PROFILE_UPLOAD_FOLDER, secure_name)
            user.foto_profil = relative_path
            db.session.commit()

            return True, 'Foto profil berhasil diupload'

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error uploading profile photo: {str(e)}", exc_info=True)
            return False, 'Gagal mengupload foto profil'


# Fungsi utilitas untuk diimpor langsung
def handle_profile_upload(file, user):
    """Utility function to be imported by routes"""
    uploader = FileUploadService()
    return uploader.handle_profile_upload(file, user)