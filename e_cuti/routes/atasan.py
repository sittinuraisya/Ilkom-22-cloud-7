import sqlalchemy, json
from sqlalchemy import exc as sqlalchemy_exc
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, current_app, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import Cuti, User, UserRole, CutiStatus, JenisCuti, db
from services.Api_GoogleCalendar import GoogleCalendarService
from services.Api_Slack import SlackService
from services.email import send_cuti_notification_email, send_leave_status_email
from sqlalchemy.orm import aliased, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import extract, func
from utils.decorators import role_required
from utils.notifications import send_notification
import logging

atasan_bp = Blueprint('atasan', __name__, url_prefix='/atasan')

# Helper functions
def validate_cuti_ownership(cuti):
    """Validasi kepemilikan cuti oleh atasan"""
    if cuti.user.atasan_id != current_user.id:
        current_app.logger.warning(
            f"Unauthorized access attempt by {current_user.id} for cuti {cuti.id}"
        )
        abort(403, 'Anda tidak memiliki akses untuk memproses cuti ini')

def validate_cuti_status(cuti, allowed_statuses):
    """Validasi status cuti"""
    if cuti.status not in allowed_statuses:
        current_app.logger.warning(
            f"Invalid status {cuti.status} for cuti {cuti.id}"
        )
        flash('Cuti ini sudah diproses sebelumnya', 'warning')
        return False
    return True

def send_approval_notifications(cuti, user):
    """Handle semua notifikasi persetujuan"""
    # Google Calendar
    if current_app.config.get('GOOGLE_CALENDAR_ENABLED', False):
        try:
            calendar = GoogleCalendarService()
            if not cuti.event_id:
                event_data = {
                    'user_id': user.id,
                    'jenis_cuti': cuti.jenis_cuti.value,
                    'tanggal_mulai': cuti.tanggal_mulai,
                    'tanggal_selesai': cuti.tanggal_selesai,
                    'perihal_cuti': cuti.perihal_cuti,
                    'user_name': user.full_name,
                    'user_email': user.email
                }
                result = calendar.create_cuti_event(event_data)
                if result['success']:
                    cuti.event_id = result['event_id']
        except Exception as e:
            current_app.logger.error(f"Google Calendar error: {str(e)}")

    # Slack Notification
    if current_app.config.get('SLACK_ENABLED', False):
        try:
            slack = SlackService()
            slack.send_cuti_notification({
                'user_id': user.id,
                'user_name': user.full_name,
                'jenis_cuti': cuti.jenis_cuti.value,
                'tanggal_mulai': cuti.tanggal_mulai.strftime('%d/%m/%Y'),
                'tanggal_selesai': cuti.tanggal_selesai.strftime('%d/%m/%Y'),
                'status': 'APPROVED',
                'approver_name': current_user.full_name
            })
        except Exception as e:
            current_app.logger.error(f"Slack notification error: {str(e)}")

    # Email Notification
    try:
        send_cuti_notification_email(
            recipient=user.email,
            subject=f'[Disetujui] Pengajuan Cuti {cuti.jenis_cuti.value}',
            template='email/cuti_approved.html',
            context={
                'user': user,
                'cuti': cuti,
                'approver': current_user
            }
        )
    except Exception as e:
        current_app.logger.error(f"Email notification error: {str(e)}")

@atasan_bp.route('/dashboard')
@login_required
@role_required(UserRole.ATASAN)
def dashboard():
    """Dashboard atasan dengan statistik cuti"""
    try:
        bawahan_ids = [pegawai.id for pegawai in current_user.subordinates]
        
        if not bawahan_ids:
            return render_template('atasan/dashboard.html',
                               cuti_menunggu=0,
                               cuti_disetujui=0,
                               cuti_ditolak=0)

        # Hitung statistik dengan query yang lebih efisien
        stats = db.session.query(
            db.func.sum(db.case((Cuti.status == CutiStatus.PENDING.value, 1), else_=0)).label('pending'),
            db.func.sum(db.case((Cuti.status == CutiStatus.APPROVED.value, 1), else_=0)).label('approved'),
            db.func.sum(db.case((Cuti.status == CutiStatus.REJECTED.value, 1), else_=0)).label('rejected')
        ).filter(
            Cuti.user_id.in_(bawahan_ids),
            db.extract('month', Cuti.tanggal_mulai) == datetime.now().month,
            db.extract('year', Cuti.tanggal_mulai) == datetime.now().year
        ).first()

        return render_template(
            'atasan/dashboard.html',
            cuti_menunggu=stats.pending or 0,
            cuti_disetujui=stats.approved or 0,
            cuti_ditolak=stats.rejected or 0
        )

    except Exception as e:
        current_app.logger.error(f"Error in dashboard: {str(e)}", exc_info=True)
        flash('Terjadi kesalahan saat memuat dashboard', 'danger')
        return render_template('atasan/dashboard.html',
                           cuti_menunggu=0,
                           cuti_disetujui=0,
                           cuti_ditolak=0)

@atasan_bp.route('/manage-cuti')
@login_required
def manage_cuti():
    try:
        current_app.logger.info(f"Atasan {current_user.id} mengakses manage_cuti")

        # Dapatkan parameter filter
        status_filter = request.args.get('status')
        tahun = request.args.get('tahun', type=int)
        bulan = request.args.get('bulan', type=int)

        # Query dasar untuk data cuti
        base_query = db.session.query(Cuti, User).join(
            User, Cuti.user_id == User.id
        ).filter(
            Cuti.atasan_id == current_user.id,
            Cuti.is_cancelled == False
        )

        # Query terpisah untuk statistik (tanpa filter)
        stats_query = db.session.query(
            Cuti.status,
            func.count(Cuti.id).label('count')
        ).filter(
            Cuti.atasan_id == current_user.id,
            Cuti.is_cancelled == False
        ).group_by(Cuti.status)

        # Terapkan filter untuk data cuti
        if status_filter:
            base_query = base_query.filter(Cuti.status == status_filter)
        else:
            # Default: tampilkan yang PENDING dan IN_REVIEW
            base_query = base_query.filter(Cuti.status.in_([CutiStatus.PENDING, CutiStatus.IN_REVIEW]))

        # Filter tanggal
        if tahun and bulan:
            base_query = base_query.filter(
                extract('year', Cuti.tanggal_mulai) == tahun,
                extract('month', Cuti.tanggal_mulai) == bulan
            )
            stats_query = stats_query.filter(
                extract('year', Cuti.tanggal_mulai) == tahun,
                extract('month', Cuti.tanggal_mulai) == bulan
            )
        elif tahun:
            base_query = base_query.filter(extract('year', Cuti.tanggal_mulai) == tahun)
            stats_query = stats_query.filter(extract('year', Cuti.tanggal_mulai) == tahun)

        # Eksekusi query data cuti
        cuti_data = base_query.order_by(Cuti.created_at.desc()).all()

        # Eksekusi query statistik
        stats_result = stats_query.all()

        # Format data cuti
        formatted_cuti = []
        for cuti, pemohon in cuti_data:
            status_value = cuti.status.value if cuti.status else 'PENDING'
            
            lampiran = None
            if cuti.lampiran:
                lampiran = cuti.lampiran.split('uploads/')[-1] if 'uploads/' in cuti.lampiran else cuti.lampiran

            formatted_cuti.append({
                'id': cuti.id,
                'pemohon': {
                    'nama': pemohon.full_name or pemohon.username,
                    'nip': pemohon.nip or "-",
                    'jabatan': pemohon.jabatan or "-",
                    'foto': pemohon.foto_profil or url_for('static', filename='images/default-profile.png'),
                },
                'detail': {
                    'jenis': cuti.jenis_cuti.value if hasattr(cuti.jenis_cuti, 'value') else str(cuti.jenis_cuti),
                    'mulai': cuti.tanggal_mulai.strftime('%d/%m/%Y'),
                    'selesai': cuti.tanggal_selesai.strftime('%d/%m/%Y'),
                    'hari': cuti.jumlah_hari,
                    'alasan': cuti.perihal_cuti or "-",
                    'status': status_value,
                    'status_display': CutiStatus.get_display_name(status_value),
                    'status_icon': CutiStatus.get_icon(status_value),
                    'lampiran': url_for('static', filename=f'uploads/{lampiran}') if lampiran else None
                },
                'waktu': {
                    'diajukan': cuti.created_at.strftime('%d/%m/%Y %H:%M'),
                    'diperbarui': cuti.updated_at.strftime('%d/%m/%Y %H:%M') if cuti.updated_at else "-"
                }
            })

        # Hitung statistik
        status_count = {status.value: count for status, count in stats_result}
        stats = {
            'total': sum(count for count in status_count.values()),
            'menunggu': status_count.get(CutiStatus.PENDING.value, 0),
            'review': status_count.get(CutiStatus.IN_REVIEW.value, 0),
            'disetujui': status_count.get(CutiStatus.APPROVED.value, 0),
            'ditolak': status_count.get(CutiStatus.REJECTED.value, 0)
        }

        return render_template(
            'atasan/manage_cuti.html',
            cuti_list=formatted_cuti,
            summary=stats,
            tahun_sekarang=datetime.now().year,
            bulan_sekarang=datetime.now().month,
            current_time=datetime.now().strftime('%d/%m/%Y %H:%M')
        )

    except Exception as e:
        current_app.logger.error(f"Error in manage_cuti: {str(e)}", exc_info=True)
        flash('Terjadi kesalahan sistem saat memuat data cuti', 'danger')
        return redirect(url_for('atasan.dashboard'))
    
@atasan_bp.route('/approve-cuti/<int:cuti_id>', methods=['POST'])
@login_required
@role_required(UserRole.ATASAN)
def approve_cuti(cuti_id):
    try:
        # Validasi cuti
        cuti = Cuti.query.filter_by(
            id=cuti_id,
            atasan_id=current_user.id,
            status=CutiStatus.PENDING
        ).first()

        if not cuti:
            flash('Cuti tidak ditemukan atau sudah diproses', 'error')
            return redirect(url_for('atasan.manage_cuti'))

        # Use pemohon instead of user
        pemohon = cuti.pemohon

        # Validasi sisa cuti pegawai
        if cuti.jenis_cuti == JenisCuti.TAHUNAN:
            if pemohon.sisa_cuti < cuti.jumlah_hari:
                flash('Sisa cuti pegawai tidak mencukupi', 'error')
                return redirect(url_for('atasan.manage_cuti'))

        # Update status cuti
        cuti.status = CutiStatus.APPROVED
        cuti.alasan_penolakan = None
        
        # Update status history
        history = json.loads(cuti.status_history) if cuti.status_history else []
        history.append({
            'status': 'APPROVED',
            'timestamp': datetime.now().isoformat(),
            'by': current_user.full_name,
            'note': request.form.get('catatan', '')
        })
        cuti.status_history = json.dumps(history)

        # Kurangi sisa cuti jika cuti tahunan
        if cuti.jenis_cuti == JenisCuti.TAHUNAN:
            pemohon.sisa_cuti -= cuti.jumlah_hari

        db.session.commit()

        # Kirim notifikasi ke pegawai
        send_notification(
            user_id=cuti.user_id,
            title='Pengajuan Cuti Disetujui',
            message=f'Cuti Anda telah disetujui oleh {current_user.full_name}',
            link=url_for('pegawai.status_cuti')
        )

        flash('Cuti berhasil disetujui', 'success')
        return redirect(url_for('atasan.manage_cuti'))

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error approving leave: {str(e)}")
        flash('Terjadi kesalahan database', 'error')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving leave: {str(e)}")
        flash('Terjadi kesalahan sistem', 'error')
    
    return redirect(url_for('atasan.manage_cuti'))

@atasan_bp.route('/reject-cuti/<int:cuti_id>', methods=['POST'])
@login_required
@role_required(UserRole.ATASAN)
def reject_cuti(cuti_id):
    # Verify the leave request exists and belongs to this supervisor
    cuti = Cuti.query.filter_by(
        id=cuti_id,
        atasan_id=current_user.id,
        status=CutiStatus.PENDING
    ).first_or_404()

    # Validate reason
    alasan = request.form.get('alasan_penolakan', '').strip()
    if len(alasan) < 10:
        flash('Alasan penolakan harus minimal 10 karakter', 'error')
        return redirect(url_for('atasan.manage_cuti'))

    # Process rejection
    cuti.status = CutiStatus.REJECTED
    cuti.alasan_penolakan = alasan
    db.session.commit()

    # Send notification
    send_notification(
        user_id=cuti.user_id,
        title='Pengajuan Cuti Ditolak',
        message=f'Cuti Anda ditolak oleh {current_user.full_name}. Alasan: {alasan}'
    )

    flash('Pengajuan cuti berhasil ditolak', 'success')
    return redirect(url_for('atasan.manage_cuti'))

@atasan_bp.route('/api/check-new-cuti')
@login_required
@role_required(UserRole.ATASAN)
def check_new_cuti():
    try:
        # Count only unread pending leave requests
        count = Cuti.query.filter_by(
            atasan_id=current_user.id,
            status=CutiStatus.PENDING
        ).filter(
            ~Cuti.status_history.contains('"status": "READ"')
        ).count()
        
        return jsonify({
            'success': True,
            'new_requests': count,
            'notification_sound': url_for('static', filename='sounds/notification.mp3', _external=True)
        })
    except Exception as e:
        current_app.logger.error(f"Error in check_new_cuti: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500