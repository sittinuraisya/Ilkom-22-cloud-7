from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Cuti, User, db, UserRole, CutiStatus
from services.cuti_service import (
    get_cuti_for_print,
    get_cuti_list,
    delete_cuti,
    get_cuti_for_print,
    format_tanggal
)
from extensions import db
from services.Api_GoogleCalendar import GoogleCalendarService
from services.Api_Slack import SlackService

cuti_bp = Blueprint('cuti', __name__)

@cuti_bp.route('/status-cuti')
@login_required
def status_cuti():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    results = get_cuti_list(current_user, page, per_page)
    
    return render_template(
        'pegawai/status_cuti.html',
        cuti_list=results['items'],
        page=page,
        total_pages=results['pages'],
        per_page=per_page,
        current_role=current_user.role.value,
        UserRole=UserRole,
        CutiStatus=CutiStatus
    )

@cuti_bp.route('/hapus-cuti/<int:cuti_id>', methods=['POST'])
@login_required
def hapus_cuti(cuti_id):
    success, message = delete_cuti(cuti_id, current_user)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('cuti.status_cuti'))

@cuti_bp.route('/cetak-surat/<int:cuti_id>')
@login_required
def cetak_surat(cuti_id):
    cuti_data = get_cuti_for_print(cuti_id, current_user)
    if not cuti_data:
        flash('Akses ditolak atau data tidak ditemukan', 'error')
        return redirect(url_for('cuti.status_cuti'))
    
    tanggal_format = format_tanggal(cuti_data['cuti'].tanggal_mulai)
    
    return render_template(
        f"{current_user.role.value}/cetak_surat.html",
        cuti=cuti_data['cuti'],
        user=cuti_data['user'],
        tanggal_format=tanggal_format,
        tahun=cuti_data['tahun'],
        current_user=current_user,
        UserRole=UserRole,
        CutiStatus=CutiStatus
    )
    
@cuti_bp.route('/detail-cuti/<int:cuti_id>')
@login_required
def detail_cuti(cuti_id):
    # Get leave data with relationships
    cuti = db.session.query(Cuti).options(
        db.joinedload(Cuti.pemohon),
        db.joinedload(Cuti.penyetuju)
    ).filter_by(id=cuti_id).first()

    if not cuti:
        flash('Data cuti tidak ditemukan', 'error')
        return redirect(url_for('admin.admin_dashboard'))

    # Verify access
    if not (current_user.role == UserRole.ADMIN or 
            current_user.id == cuti.user_id or 
            current_user.id == cuti.atasan_id):
        flash('Anda tidak memiliki akses ke detail ini', 'error')
        return redirect(url_for('admin.admin_dashboard'))

    # Format data for display
    detail_data = {
        'id': cuti.id,
        'jenis_cuti': cuti.jenis_cuti.value,
        'perihal': cuti.perihal_cuti,  # Changed from alasan to perihal_cuti
        'tanggal_mulai': cuti.tanggal_mulai.strftime('%d-%m-%Y'),
        'tanggal_selesai': cuti.tanggal_selesai.strftime('%d-%m-%Y'),
        'lama_cuti': (cuti.tanggal_selesai - cuti.tanggal_mulai).days + 1,
        'alamat': cuti.address_during_leave or '-',  # Changed from alamat_selama_cuti
        'telepon': cuti.contact_number or '-',  # Changed from nomor_telepon
        'status': cuti.status.value,
        'tanggal_pengajuan': cuti.created_at.strftime('%d-%m-%Y %H:%M'),
        'pemohon': {
            'nama': cuti.pemohon.full_name,
            'nip': cuti.pemohon.nip or '-',
            'jabatan': cuti.pemohon.jabatan or '-'
        },
        'penyetuju': {
            'nama': cuti.penyetuju.full_name if cuti.penyetuju else '-',
            'jabatan': cuti.penyetuju.jabatan if cuti.penyetuju else '-'
        } if cuti.atasan_id else None,
        'catatan': cuti.alasan_penolakan or '-'  # Changed from catatan to alasan_penolakan
    }

    return render_template(
        f"{current_user.role.value}/detail_cuti.html",
        cuti=detail_data,
        page_title='Detail Pengajuan Cuti',
        UserRole=UserRole,
        CutiStatus=CutiStatus
    )