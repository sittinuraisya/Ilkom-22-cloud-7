from datetime import datetime
from flask import current_app
from models import Cuti, User, UserRole, CutiStatus
from extensions import db

# Import services hanya jika diperlukan
try:
    from services.Api_GoogleCalendar import GoogleCalendarService
    from services.Api_Slack import SlackService
except ImportError:
    # Fallback untuk development/testing
    # Dummy classes untuk development
    class GoogleCalendarService:
        def __init__(self):
            self.service = type('DummyService', (), {
                'events': lambda: type('DummyEvents', (), {
                    'delete': lambda *args, **kwargs: None
                })
            })()
    class SlackService:
        def send_notification(self, message):
            current_app.logger.info(f"[Slack Simulation] {message}")

def get_cuti_list(user, page, per_page):
    """Mendapatkan daftar cuti berdasarkan role user"""
    query = db.session.query(Cuti, User).join(User, Cuti.user_id == User.id)
    
    if user.role in [UserRole.ADMIN.value, UserRole.SUPERADMIN.value]:
        results = query.order_by(Cuti.created_at.desc()).paginate(page=page, per_page=per_page)
    elif user.role == UserRole.ATASAN.value:
        results = query.filter(User.atasan_id == user.id)\
                      .order_by(Cuti.created_at.desc())\
                      .paginate(page=page, per_page=per_page)
    else:
        results = query.filter(Cuti.user_id == user.id)\
                      .order_by(Cuti.created_at.desc())\
                      .paginate(page=page, per_page=per_page)
    
    return {
        'items': [{'cuti': c, 'user': u} for c, u in results.items],
        'pages': results.pages
    }

def get_cuti_for_print(cuti_id):
    """Mengambil data cuti untuk keperluan cetak"""
    cuti = Cuti.query.get(cuti_id)
    if not cuti:
        return None
    
    return {
        'id': cuti.id,
        'nama': cuti.pemohon.full_name,
        'nip': cuti.pemohon.nip,
        'jenis_cuti': cuti.jenis_cuti.value,
        'tanggal_mulai': cuti.tanggal_mulai.strftime('%d-%m-%Y'),
        'tanggal_selesai': cuti.tanggal_selesai.strftime('%d-%m-%Y'),
        'jumlah_hari': cuti.jumlah_hari,
        'status': cuti.status.value
    }


def delete_cuti(cuti_id, user):
    """Menghapus data cuti dengan validasi permission"""
    cuti = Cuti.query.get_or_404(cuti_id)
    
    # Validasi akses
    if user.role == UserRole.PEGAWAI.value and cuti.user_id != user.id:
        return False, 'Anda tidak memiliki izin untuk menghapus cuti ini'
    
    if user.role == UserRole.ATASAN.value:
        pemohon = User.query.get(cuti.user_id)
        if not pemohon or pemohon.atasan_id != user.id:
            return False, 'Anda hanya dapat menghapus cuti bawahan Anda'
    
    # Validasi status
    if cuti.status not in [CutiStatus.PENDING.value, CutiStatus.CANCELLED.value]:
        return False, 'Hanya cuti berstatus Pending atau Dibatalkan yang dapat dihapus'
    
    try:
        # Handle Google Calendar
        if current_app.config.get('GOOGLE_CALENDAR_ENABLED', False) and cuti.event_id:
            try:
                calendar = GoogleCalendarService()
                calendar.service.events().delete(
                    calendarId='primary',
                    eventId=cuti.event_id
                ).execute()
            except Exception as e:
                current_app.logger.error(f"Gagal menghapus event dari Google Calendar: {str(e)}")
        
        # Handle Slack
        if current_app.config.get('SLACK_WEBHOOK_URL'):
            slack = SlackService()
            slack.send_notification(
                f"Penghapusan Cuti oleh {user.username}\n"
                f"ID Cuti: {cuti_id}\n"
                f"Pemohon: {cuti.pemohon.username}\n"
                f"Status: {cuti.status}"
            )
        
        db.session.delete(cuti)
        db.session.commit()
        return True, 'Cuti berhasil dihapus'
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Gagal menghapus cuti: {str(e)}")
        return False, 'Gagal menghapus cuti'

def format_tanggal(tanggal: str | datetime, format_output: str = '%d-%m-%Y') -> str:
    """
    Format tanggal dari string/datetime ke format yang diinginkan
    Contoh: '2023-12-31' -> '31-12-2023'
    """
    if isinstance(tanggal, str):
        try:
            tanggal = datetime.strptime(tanggal, '%Y-%m-%d')
        except ValueError:
            return tanggal
    
    return tanggal.strftime(format_output) if tanggal else None

def get_cuti_detail(cuti_id, current_user):
    cuti = db.session.query(Cuti).options(
        db.joinedload(Cuti.pemohon),
        db.joinedload(Cuti.penyetuju)
    ).filter_by(id=cuti_id).first()

    if not cuti:
        return None

    # Check access
    if not (current_user.role == UserRole.ADMIN or 
            current_user.id == cuti.user_id or 
            current_user.id == cuti.atasan_id):
        return None

    return cuti