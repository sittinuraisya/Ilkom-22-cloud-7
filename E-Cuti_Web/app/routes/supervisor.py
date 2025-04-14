from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import LeaveRequest, db
import requests, os
from flask_mail import Message
from app import mail
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

bp = Blueprint('supervisor', __name__, url_prefix='/supervisor')

@bp.route('/verifikasi')
@login_required
def verify_requests():
    if current_user.role != 'supervisor':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('leave.request_leave'))
    requests_list = LeaveRequest.query.filter_by(status='pending').all()
    return render_template('verify_requests.html', requests=requests_list)

@bp.route('/verifikasi/<int:id>/<action>')
@login_required
def verify_action(id, action):
    if current_user.role != 'supervisor':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('leave.request_leave'))

    req = LeaveRequest.query.get_or_404(id)
    if action == 'approve':
        req.status = 'approved'
    elif action == 'reject':
        req.status = 'rejected'
    db.session.commit()

    # Slack Notification
    slack_data = {
        "text": f"[Verifikasi Cuti] Pengajuan cuti oleh {req.user.username} telah *{req.status.upper()}* oleh {current_user.username}"
    }
    requests.post(url=os.getenv("SLACK_WEBHOOK_URL"), json=slack_data)

    # Email Notification
    msg = Message(f'Pengajuan Cuti {req.status.title()}', recipients=[req.user.email])
    msg.body = f"Halo {req.user.username}, pengajuan cuti kamu telah {req.status}."
    mail.send(msg)

    # Google Calendar Sync jika disetujui
    if req.status == 'approved':
        creds = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_CALENDAR_CREDENTIALS"),
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        service = build('calendar', 'v3', credentials=creds)

        event = {
            'summary': f'Cuti: {req.user.username}',
            'description': req.note,
            'start': {
                'date': req.start_date.isoformat(),
                'timeZone': 'Asia/Jakarta',
            },
            'end': {
                'date': (req.end_date + timedelta(days=1)).isoformat(),
                'timeZone': 'Asia/Jakarta',
            },
        }
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        service.events().insert(calendarId=calendar_id, body=event).execute()

    flash(f'Pengajuan cuti berhasil di-{req.status}.', 'success')
    return redirect(url_for('supervisor.verify_requests'))