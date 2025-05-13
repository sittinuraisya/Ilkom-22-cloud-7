from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from models import db, User, UserRole
from services.file_upload import handle_profile_upload
from datetime import datetime
import os
import re
import time

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profil')
@login_required
def profil():
    try:
        user = db.session.get(User, current_user.id)
        if not user:
            flash('Data pengguna tidak ditemukan', 'error')
            return redirect(url_for('common.dashboard'))
        
        # Format data
        tanggal_lahir = user.tanggal_lahir.strftime('%d-%m-%Y') if user.tanggal_lahir else '-'
        jenis_kelamin = {
            'L': 'Laki-laki',
            'P': 'Perempuan'
        }.get(user.jenis_kelamin, '-')
        
        # Get profile photo URL with fallback
        foto_profil = (url_for('static', filename=f'uploads/profile/{user.foto_profil}') 
                      if user.foto_profil and os.path.exists(os.path.join(current_app.static_folder, 'uploads/profile', user.foto_profil))
                      else url_for('static', filename='images/profile-default.png'))
        
        context = {
            'user': user,
            'profil_data': {
                'tanggal_lahir': tanggal_lahir,
                'jenis_kelamin': jenis_kelamin,
                'golongan': user.golongan or '-',
                'jabatan': user.jabatan or '-',
                'phone': user.phone or '-',
                'tempat_lahir': user.tempat_lahir or '-',
                'foto_profil': foto_profil,
                'email': user.email,
                'nip': user.nip or '-',
                'full_name': user.full_name,
                'alamat': getattr(user, 'alamat', '-')  # Safely get alamat attribute
            },
            'page_title': 'Profil Pengguna'
        }
        
        return render_template('pegawai/profil.html', **context)
            
    except Exception as e:
        current_app.logger.error(f"Error accessing profile: {str(e)}", exc_info=True)
        flash('Terjadi kesalahan saat mengakses profil', 'error')
        return redirect(url_for('common.dashboard'))

@profile_bp.route('/edit-profil', methods=['GET', 'POST'])
@login_required
def edit_profil():
    user = db.session.get(User, current_user.id)
    
    if request.method == 'POST':
        try:
            # Validate and process form data
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            full_name = request.form.get('full_name', '').strip()
            
            # Email validation
            if not email:
                flash('Email tidak boleh kosong', 'error')
                return redirect(url_for('profile.edit_profil'))
            
            if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
                flash('Format email tidak valid', 'error')
                return redirect(url_for('profile.edit_profil'))
            
            # Phone validation
            if phone and not re.match(r'^\+?[\d\s-]{10,15}$', phone):
                flash('Format nomor telepon tidak valid', 'error')
                return redirect(url_for('profile.edit_profil'))
            
            # Update user data
            user.email = email
            user.phone = phone
            user.full_name = request.form.get('full_name', '').strip()
            user.tempat_lahir = request.form.get('tempat_lahir', '').strip()
            
            # Update employment info
            user.nip = request.form.get('nip', '').strip()
            user.jabatan = request.form.get('jabatan', '').strip()
            user.golongan = request.form.get('golongan', '').strip()
            user.alamat = request.form.get('alamat', '').strip()
            
            # Process birth date
            tanggal_lahir = request.form.get('tanggal_lahir')
            if tanggal_lahir:
                try:
                    user.tanggal_lahir = datetime.strptime(tanggal_lahir, '%Y-%m-%d').date()
                except ValueError:
                    flash('Format tanggal lahir tidak valid (YYYY-MM-DD)', 'error')
                    return redirect(url_for('profile.edit_profil'))
            
            # Process gender
            jenis_kelamin = request.form.get('jenis_kelamin')
            if jenis_kelamin in ['L', 'P']:
                user.jenis_kelamin = jenis_kelamin
            
            db.session.commit()
            flash('Profil berhasil diperbarui', 'success')
            return redirect(url_for('profile.profil'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating profile: {str(e)}", exc_info=True)
            flash('Terjadi kesalahan saat memperbarui profil', 'error')
    
    # Format birth date for form input
    tanggal_lahir_form = user.tanggal_lahir.strftime('%Y-%m-%d') if user.tanggal_lahir else ''
    
    # Check if profile photo exists
    foto_exists = False
    if user.foto_profil:
        foto_path = os.path.join(current_app.static_folder, 'uploads', 'profile', user.foto_profil)
        foto_exists = os.path.exists(foto_path)
    
    return render_template('pegawai/edit_profil.html', 
                         user=user,
                         tanggal_lahir_form=tanggal_lahir_form,
                         foto_exists=foto_exists,
                         page_title='Edit Profil')

@profile_bp.route('/upload-foto-profil', methods=['POST'])
@login_required
def upload_foto_profil():
    if 'foto_profil' not in request.files:
        return jsonify({'success': False, 'message': 'Tidak ada file yang dipilih'}), 400

    file = request.files['foto_profil']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Tidak ada file yang dipilih'}), 400

    # Validate file extension
    allowed_extensions = {'jpg', 'jpeg', 'png'}
    if '.' not in file.filename or file.filename.split('.')[-1].lower() not in allowed_extensions:
        return jsonify({'success': False, 'message': 'Format file tidak didukung (hanya JPG/JPEG/PNG)'}), 400

    try:
        # Ensure upload directory exists
        upload_dir = os.path.join(current_app.static_folder, 'uploads', 'profile')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate secure filename
        ext = file.filename.split('.')[-1].lower()
        filename = f"profile_{current_user.id}_{int(time.time())}.{ext}"
        filepath = os.path.join(upload_dir, filename)
        
        # Save file
        file.save(filepath)
        
        # Delete old photo if exists
        if current_user.foto_profil:
            old_path = os.path.join(upload_dir, current_user.foto_profil)
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # Update database
        current_user.foto_profil = filename
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Foto profil berhasil diperbarui',
            'photo_url': url_for('static', filename=f'uploads/profile/{filename}')
        })
        
    except Exception as e:
        current_app.logger.error(f"Error uploading profile photo: {str(e)}")
        return jsonify({'success': False, 'message': 'Gagal mengunggah foto profil'}), 500