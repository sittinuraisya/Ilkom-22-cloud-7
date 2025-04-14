import os
import pdfkit
from datetime import datetime
from flask import render_template, current_app

def generate_cuti_pdf(cuti_request, user, approver):
    """Generate PDF for approved cuti request"""
    html = render_template('pdf/cuti_approval.html',
                          cuti=cuti_request,
                          user=user,
                          approver=approver,
                          current_date=datetime.now().strftime('%d %B %Y'))
    
    # Make sure upload dir exists
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # File path for PDF
    filename = f"cuti_{cuti_request.id}_{user.username}_{datetime.now().strftime('%Y%m%d')}.pdf"
    pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    # Generate PDF using wkhtmltopdf
    pdfkit.from_string(html, pdf_path, options={
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': 'UTF-8',
        'no-outline': None
    })
    
    return pdf_path