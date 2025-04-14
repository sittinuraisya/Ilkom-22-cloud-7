from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import LeaveRequest, db
from datetime import datetime
import requests
import os
import pdfkit


bp = Blueprint('leave', __name__, url_prefix='/leave')

@bp.route('/request', methods=['GET', 'POST'])
@login_required
def request_leave():
    if request.method == 'POST':
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        note = request.form['note']

        leave = LeaveRequest(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            note=note
        )
        db.session.add(leave)
        db.session.commit()

        # Send Slack Notification
        slack_data = {
            "text": f"[Pengajuan Cuti] {current_user.username} mengajukan cuti dari {start_date.date()} hingga {end_date.date()}"
        }
        requests.post(url=os.getenv("SLACK_WEBHOOK_URL"), json=slack_data)

        # Send Email Notification
        from flask_mail import Message
        from app import mail

        msg = Message('Pengajuan Cuti Baru', recipients=[current_user.email])
        msg.body = f"Halo {current_user.username}, pengajuan cuti kamu telah diterima dan sedang diproses."
        mail.send(msg)

        flash('Pengajuan cuti berhasil diajukan.', 'success')
        return redirect(url_for('leave.request_leave'))

    return render_template('leave_request.html')

@bp.route('/calendar')
@login_required
def leave_calendar():
    approved_requests = LeaveRequest.query.filter_by(status='approved').all()
    return render_template('leave_calendar.html', requests=approved_requests)

@bp.route('/rekap')
@login_required
def leave_recap():
    all_requests = LeaveRequest.query.all()
    return render_template('leave_recap.html', requests=all_requests)

@bp.route('/rekap/pdf')
@login_required
def leave_recap_pdf():
    all_requests = LeaveRequest.query.all()
    rendered = render_template('leave_recap.html', requests=all_requests)
    pdf = pdfkit.from_string(rendered, False)
    from flask import Response
    return Response(pdf, mimetype='application/pdf', headers={
        'Content-Disposition': 'attachment; filename=rekap_cuti.pdf'
    })