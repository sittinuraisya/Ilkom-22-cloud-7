from models import db, Notification
from datetime import datetime
from flask import current_app

def send_notification(user_id, title, message, link=None):
    """
    Fungsi untuk mengirim notifikasi ke user
    
    Parameters:
    - user_id: ID user penerima
    - title: Judul notifikasi
    - message: Isi pesan notifikasi
    - link: URL tujuan ketika notifikasi diklik (opsional)
    """
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link if link else '#',
            is_read=False,
            created_at=datetime.now()
        )
        db.session.add(notification)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Gagal mengirim notifikasi: {str(e)}")
        return False