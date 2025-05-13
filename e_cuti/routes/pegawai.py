from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, current_app, send_from_directory
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os, json
import uuid
from enum import Enum
from sqlalchemy.orm import aliased
from sqlalchemy.exc import SQLAlchemyError
from models import User, Cuti, db, JenisCuti, CutiStatus, AuditLog, Notification, UserRole
from utils.decorators import role_required
from utils.validators import validate_cuti_form, calculate_working_days, allowed_file
from utils.notifications import send_notification
from services.notification import send_notification
from services.email import send_cuti_notification_email
from services.Api_GoogleCalendar import GoogleCalendarService
from services.Api_Slack import SlackService

pegawai_bp = Blueprint('pegawai', __name__, url_prefix='/pegawai')

@pegawai_bp.route('/dashboard')
@login_required
@role_required(UserRole.PEGAWAI)
def dashboard():
    try:
        # Get current year
        tahun_ini = datetime.now().year
        
        # Calculate approved leave days
        cuti_disetujui = db.session.query(
            db.func.sum(Cuti.jumlah_hari).label('total')
        ).filter(
            Cuti.user_id == current_user.id,
            Cuti.status == CutiStatus.APPROVED,
            db.extract('year', Cuti.tanggal_mulai) == tahun_ini,
            Cuti.is_cancelled == False  # Exclude cancelled leaves
        ).scalar() or 0

        # Calculate remaining leave days
        total_cuti = current_user.total_cuti or 12  # Default 12 days if not set
        sisa_cuti = max(0, total_cuti - cuti_disetujui)  # Ensure not negative

        # Get rejected leave count
        cuti_ditolak = db.session.query(Cuti).filter(
            Cuti.user_id == current_user.id,
            Cuti.status == CutiStatus.REJECTED,
            db.extract('year', Cuti.created_at) == tahun_ini
        ).count()

        # Get last 5 leave requests with proper ordering
        cuti_terakhir = db.session.query(Cuti).filter(
            Cuti.user_id == current_user.id
        ).order_by(
            Cuti.created_at.desc()
        ).limit(5).all()

        # Prepare leave policy information
        ketentuan_cuti = {
            JenisCuti.TAHUNAN.value: {
                'max_hari': 12,
                'sisa': sisa_cuti,
                'keterangan': 'Masa kerja minimal 1 tahun'
            },
            JenisCuti.SAKIT.value: {
                'max_hari': 14,
                'keterangan': 'Wajib lampirkan surat dokter'
            },
            JenisCuti.MELAHIRKAN.value: {
                'max_hari': 90,
                'keterangan': 'Khusus karyawan perempuan'
            },
            JenisCuti.PENTING.value: {
                'max_hari': 7,
                'keterangan': 'Untuk keperluan mendesak'
            }
        }

        return render_template('pegawai/dashboard.html',
                            sisa_cuti=sisa_cuti,
                            cuti_disetujui=cuti_disetujui,
                            cuti_ditolak=cuti_ditolak,
                            cuti_terakhir=cuti_terakhir,
                            ketentuan_cuti=ketentuan_cuti,
                            tahun_ini=tahun_ini)

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in dashboard: {str(e)}")
        flash('Terjadi kesalahan sistem', 'error')
        return redirect(url_for('pegawai.dashboard'))
    except Exception as e:
        current_app.logger.error(f"Unexpected error in dashboard: {str(e)}")
        flash('Terjadi kesalahan sistem', 'error')
        return redirect(url_for('pegawai.dashboard'))
    
@pegawai_bp.route('/ajukan-cuti', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.PEGAWAI)
def ajukan_cuti():
    form_data = {}
    jenis_cuti_options = [jc.value for jc in JenisCuti]
    
    # Validate supervisor assignment
    if current_user.atasan_id is None:
        flash('Anda belum memiliki atasan yang ditentukan. Silakan hubungi admin.', 'error')
        return redirect(url_for('pegawai.dashboard'))
    
    if request.method == 'POST':
        form_data = request.form.to_dict()
        lampiran = request.files.get('lampiran')
        
        # Validate form data
        errors = validate_cuti_form(form_data, current_user)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('pegawai/ajukan_cuti.html',
                                form_data=form_data,
                                jenis_cuti_options=jenis_cuti_options)
        
        try:
            # Parse dates and calculate working days
            start_date = datetime.strptime(form_data['tanggal_mulai'], '%Y-%m-%d').date()
            end_date = datetime.strptime(form_data['tanggal_selesai'], '%Y-%m-%d').date()
            
            # Ensure end date is after start date
            if end_date <= start_date:
                raise ValueError("Tanggal selesai harus setelah tanggal mulai")
            
            jumlah_hari = calculate_working_days(start_date, end_date)
            
            # Validate positive working days
            if jumlah_hari <= 0:
                raise ValueError("Jumlah hari cuti harus lebih dari 0")
            
            # Handle file upload
            lampiran_path = None
            if lampiran and allowed_file(lampiran.filename):
                filename = secure_filename(f"{uuid.uuid4().hex}_{lampiran.filename}")
                upload_folder = os.path.join(current_app.static_folder, 'uploads')
                
                # Ensure upload directory exists
                os.makedirs(upload_folder, exist_ok=True)
                
                # Save file
                save_path = os.path.join(upload_folder, filename)
                lampiran.save(save_path)
                
                # Verify file was saved
                if not os.path.exists(save_path):
                    raise IOError("Gagal menyimpan lampiran")
                
                lampiran_path = f"uploads/{filename}"
            
            # Verify supervisor exists
            atasan = User.query.get(current_user.atasan_id)
            if not atasan:
                raise ValueError("Atasan tidak valid")
            
            # Create leave request
            cuti = Cuti(
                user_id=current_user.id,
                atasan_id=current_user.atasan_id,
                jenis_cuti=JenisCuti(form_data['jenis_cuti']),
                tanggal_mulai=start_date,
                tanggal_selesai=end_date,
                jumlah_hari=jumlah_hari,
                perihal_cuti=form_data['perihal_cuti'].strip(),
                lampiran=lampiran_path,
                status=CutiStatus.PENDING,
                status_history=json.dumps([{
                    'status': 'PENDING',
                    'timestamp': datetime.now().isoformat(),
                    'note': 'Pengajuan awal'
                }])
            )
            
            db.session.add(cuti)
            db.session.commit()
            
            # Send notification to supervisor
            try:
                send_notification(
                    user_id=current_user.atasan_id,
                    title=f'Pengajuan Cuti Baru - {current_user.full_name}',
                    message=f'{current_user.full_name} mengajukan cuti {cuti.jenis_cuti.value} selama {jumlah_hari} hari',
                    link=url_for('atasan.manage_cuti', _external=True)
                )
                
                # Send email notification
                send_cuti_notification_email(
                    atasan=atasan,
                    pemohon=current_user,
                    cuti=cuti
                )
                
            except Exception as e:
                current_app.logger.error(f"Notification error: {str(e)}")
            
            flash('Pengajuan cuti berhasil dikirim!', 'success')
            return redirect(url_for('pegawai.status_cuti'))
            
        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'error')
        except IOError:
            db.session.rollback()
            flash('Gagal mengunggah lampiran', 'error')
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Terjadi kesalahan database', 'error')
            current_app.logger.error(f"Database error: {str(e)}")
        except Exception as e:
            db.session.rollback()
            flash('Terjadi kesalahan sistem', 'error')
            current_app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    
    return render_template('pegawai/ajukan_cuti.html',
                        form_data=form_data,
                        jenis_cuti_options=jenis_cuti_options)

@pegawai_bp.route('/status-cuti')
@login_required
@role_required(UserRole.PEGAWAI)
def status_cuti():
    # Gunakan aliased untuk join yang jelas
    Atasan = aliased(User)
    
    # Query dasar dengan pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Jumlah item per halaman
    
    # Buat query dasar
    query = db.session.query(Cuti, Atasan.full_name) \
        .join(Atasan, Cuti.atasan_id == Atasan.id) \
        .filter(Cuti.user_id == current_user.id) \
        .order_by(Cuti.created_at.desc())
    
    # Eksekusi query dengan pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    daftar_cuti = pagination.items
    
    # Format data untuk template
    formatted_cuti = [{
        'cuti': cuti,
        'atasan_full_name': atasan_name,
        'jenis_cuti_display': cuti.jenis_cuti.value if isinstance(cuti.jenis_cuti, Enum) else cuti.jenis_cuti,
        'status_display': cuti.status.value if isinstance(cuti.status, Enum) else cuti.status
    } for cuti, atasan_name in daftar_cuti]
    
    return render_template('pegawai/status_cuti.html',
                         cuti_list=formatted_cuti,
                         page=page,
                         per_page=per_page,
                         total_pages=pagination.pages,
                         total=pagination.total)

@pegawai_bp.route('/cetak-surat/<int:cuti_id>')
@login_required
@role_required(UserRole.PEGAWAI)
def cetak_surat(cuti_id):
    # Query with all necessary joins
    cuti = db.session.query(
        Cuti,
        User.full_name,
        User.nip,
        User.jabatan,
        User.jenis_kelamin
    ).join(
        User, Cuti.user_id == User.id
    ).filter(
        Cuti.id == cuti_id,
        Cuti.user_id == current_user.id
    ).first_or_404()

    # Format dates
    tanggal_format = datetime.now().strftime("%d %B %Y")
    tahun = datetime.now().year
    
    return render_template('pegawai/cetak_surat.html',
        cuti={
            'id': cuti[0].id,
            'jenis_cuti': cuti[0].jenis_cuti.value if isinstance(cuti[0].jenis_cuti, Enum) else cuti[0].jenis_cuti,
            'tanggal_mulai': cuti[0].tanggal_mulai.strftime("%d %B %Y"),
            'tanggal_selesai': cuti[0].tanggal_selesai.strftime("%d %B %Y"),
            'jumlah_hari': cuti[0].jumlah_hari,
            'username': cuti.full_name,
            'nip': cuti.nip or '-',
            'jabatan': cuti.jabatan or '-',
            'jenis_kelamin': cuti.jenis_kelamin,
            'tahun': tahun,
            'tanggal_format': tanggal_format,
            'perihal_cuti': cuti[0].perihal_cuti
        })

@pegawai_bp.route('/batalkan-cuti/<int:cuti_id>', methods=['POST'])
@login_required
@role_required(UserRole.PEGAWAI)
def batalkan_cuti(cuti_id):
    # Get cuti with ownership check in single query
    cuti = Cuti.query.filter(
        Cuti.id == cuti_id,
        Cuti.user_id == current_user.id,
        Cuti.status == CutiStatus.PENDING
    ).first_or_404()
    
    alasan = request.form.get('alasan_pembatalan', '').strip()
    if not alasan:
        flash('Alasan pembatalan wajib diisi', 'error')
        return redirect(url_for('pegawai.detail_cuti', cuti_id=cuti_id))
    
    try:
        # Update status and history
        cuti.status = CutiStatus.CANCELLED
        cuti.cancel_reason = alasan
        
        # Update status history
        history = json.loads(cuti.status_history) if cuti.status_history else []
        history.append({
            'status': 'CANCELLED',
            'timestamp': datetime.now().isoformat(),
            'note': f'Dibatalkan oleh pegawai: {alasan}'
        })
        cuti.status_history = json.dumps(history)
        
        # Create notification
        send_notification(
            user_id=cuti.atasan_id,
            title=f'Pembatalan Cuti - {current_user.full_name}',
            message=f'{current_user.full_name} membatalkan pengajuan cuti dengan alasan: {alasan}',
            link=url_for('atasan.manage_cuti', _external=True)
        )
        
        # Send email notification
        atasan = User.query.get(cuti.atasan_id)
        if atasan:
            send_cuti_notification_email(
                atasan=atasan,
                pemohon=current_user,
                cuti=cuti,
                action='pembatalan'
            )
        
        db.session.commit()
        flash('Cuti berhasil dibatalkan', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error canceling leave: {str(e)}", exc_info=True)
        flash('Gagal membatalkan cuti', 'error')
    
    return redirect(url_for('pegawai.status_cuti'))

@pegawai_bp.route('/hapus-cuti/<int:cuti_id>', methods=['POST'])
@login_required
@role_required(UserRole.PEGAWAI)
def hapus_cuti(cuti_id):
    # Get cuti with all conditions in single query
    cuti = Cuti.query.filter(
        Cuti.id == cuti_id,
        Cuti.user_id == current_user.id,
        Cuti.status == CutiStatus.PENDING,
        Cuti.deleted_at.is_(None)  # Soft delete check
    ).first_or_404()
    
    try:
        # Delete attachment if exists
        if cuti.lampiran:
            try:
                file_path = os.path.join(current_app.static_folder, cuti.lampiran)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as file_error:
                current_app.logger.error(f"Error deleting attachment: {str(file_error)}")
        
        # Soft delete implementation
        cuti.deleted_at = datetime.now()
        db.session.commit()
        
        flash('Pengajuan cuti berhasil dihapus', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting leave: {str(e)}", exc_info=True)
        flash('Gagal menghapus pengajuan cuti', 'error')
    
    return redirect(url_for('pegawai.status_cuti'))

@pegawai_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        return filename
    
@pegawai_bp.route('/download-lampiran/<int:cuti_id>')
@login_required
@role_required(UserRole.PEGAWAI)
def download_lampiran(cuti_id):
    cuti = Cuti.query.filter(
        Cuti.id == cuti_id,
        Cuti.user_id == current_user.id
    ).first_or_404()
    
    if not cuti.lampiran:
        abort(404)
    
    return send_from_directory(
        directory=os.path.dirname(cuti.lampiran),
        path=os.path.basename(cuti.lampiran),
        as_attachment=True
    )