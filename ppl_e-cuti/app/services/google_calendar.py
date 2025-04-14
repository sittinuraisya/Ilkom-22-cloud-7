# app/services/google_calendar.py
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import pickle
from datetime import datetime

# Define scope for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarService:
    def __init__(self, app=None):
        self.app = app
        self.credentials = None
        self.service = None
        self.calendar_id = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.calendar_id = app.config['GOOGLE_CALENDAR_ID']
        token_path = os.path.join(app.root_path, 'token.pickle')
        credentials_path = os.path.join(app.root_path, 'credentials.json')
        
        # Load credentials
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                self.credentials = pickle.load(token)
        
        # If credentials not valid, refresh or create new ones
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                self.credentials = flow.run_local_server(port=0)
            
            # Save credentials
            with open(token_path, 'wb') as token:
                pickle.dump(self.credentials, token)
        
        self.service = build('calendar', 'v3', credentials=self.credentials)
    
    def add_cuti_event(self, cuti_request, user):
        """Add cuti event to Google Calendar"""
        event = {
            'summary': f'Cuti: {user.first_name} {user.last_name}',
            'description': f'Jenis Cuti: {cuti_request.cuti_type.value}\nAlasan: {cuti_request.reason}',
            'start': {
                'date': cuti_request.start_date.strftime('%Y-%m-%d'),
                'timeZone': 'Asia/Jakarta',
            },
            'end': {
                'date': cuti_request.end_date.strftime('%Y-%m-%d'),
                'timeZone': 'Asia/Jakarta',
            },
            'colorId': '5',  # Color: Yellow
            'attendees': [
                {'email': user.email},
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 60},  # 1 hour before
                ],
            },
        }
        
        # Add atasan as attendee if exists
        if user.atasan and user.atasan.email:
            event['attendees'].append({'email': user.atasan.email})
        
        created_event = self.service.events().insert(
            calendarId=self.calendar_id,
            body=event
        ).execute()
        
        return created_event['id']
    
    def update_cuti_event(self, event_id, cuti_request, user):
        """Update existing cuti event"""
        # First get the existing event
        event = self.service.events().get(
            calendarId=self.calendar_id,
            eventId=event_id
        ).execute()
        
        # Update event details
        event['summary'] = f'Cuti: {user.first_name} {user.last_name}'
        event['description'] = f'Jenis Cuti: {cuti_request.cuti_type.value}\nAlasan: {cuti_request.reason}'
        event['start'] = {
            'date': cuti_request.start_date.strftime('%Y-%m-%d'),
            'timeZone': 'Asia/Jakarta',
        }
        event['end'] = {
            'date': cuti_request.end_date.strftime('%Y-%m-%d'),
            'timeZone': 'Asia/Jakarta',
        }
        
        # Update status color based on approval status
        if cuti_request.status.value == 'approved':
            event['colorId'] = '10'  # Green
        elif cuti_request.status.value == 'rejected':
            event['colorId'] = '11'  # Red
        else:
            event['colorId'] = '5'   # Yellow (pending)
        
        updated_event = self.service.events().update(
            calendarId=self.calendar_id,
            eventId=event_id,
            body=event
        ).execute()
        
        return updated_event
    
    def delete_cuti_event(self, event_id):
        """Delete a cuti event"""
        self.service.events().delete(
            calendarId=self.calendar_id,
            eventId=event_id
        ).execute()
    
    def get_all_events(self, start_date, end_date):
        """Get all events in a date range"""
        events_result = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=start_date.isoformat() + 'Z',
            timeMax=end_date.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])

# app/services/slack_service.py
import slack
import json

class SlackService:
    def __init__(self, app=None):
        self.app = app
        self.client = None
        self.channel = None
        
        if app:
            self.init_app(app)
            
    def init_app(self, app):
        self.client = slack.WebClient(token=app.config['SLACK_API_TOKEN'])
        self.channel = app.config['SLACK_CHANNEL']
    
    def send_notification(self, message, blocks=None):
        """Send a notification to Slack channel"""
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=message,
                blocks=blocks
            )
            return response
        except Exception as e:
            print(f"Error sending Slack notification: {e}")
            return None
    
    def notify_new_cuti_request(self, cuti_request, user, approver):
        """Notify approver about new cuti request"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📝 Permintaan Cuti Baru",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Pegawai:*\n{user.first_name} {user.last_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Jenis Cuti:*\n{cuti_request.cuti_type.value}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Tanggal:*\n{cuti_request.start_date.strftime('%d/%m/%Y')} - {cuti_request.end_date.strftime('%d/%m/%Y')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Hari:*\n{cuti_request.total_days} hari"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Alasan:*\n{cuti_request.reason}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Lihat Detail",
                            "emoji": True
                        },
                        "url": f"https://ecuti.example.com/atasan/verifikasi/{cuti_request.id}",
                        "style": "primary"
                    }
                ]
            }
        ]
        
        message = f"Permintaan cuti baru dari {user.first_name} {user.last_name}"
        return self.send_notification(message, json.dumps(blocks))
    
    def notify_cuti_status_update(self, cuti_request, user, action_by):
        """Notify employee about cuti request status update"""
        status_emoji = "✅" if cuti_request.status.value == "approved" else "❌"
        status_text = "disetujui" if cuti_request.status.value == "approved" else "ditolak"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{status_emoji} Status Permintaan Cuti",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{status_text.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*ID Permintaan:*\n#{cuti_request.id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Tanggal:*\n{cuti_request.start_date.strftime('%d/%m/%Y')} - {cuti_request.end_date.strftime('%d/%m/%Y')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Diproses oleh:*\n{action_by.first_name} {action_by.last_name}"
                    }
                ]
            }
        ]
        
        if cuti_request.approval_notes:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Catatan:*\n{cuti_request.approval_notes}"
                }
            })
            
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Lihat Detail",
                        "emoji": True
                    },
                    "url": f"https://ecuti.example.com/cuti/{cuti_request.id}",
                    "style": "primary"
                }
            ]
        })
        
        message = f"Permintaan cuti Anda telah {status_text}"
        return self.send_notification(message, json.dumps(blocks))

# app/services/email_service.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
import os

class EmailService:
    def __init__(self, app=None):
        self.app = app
        self.client = None
        self.sender = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.client = SendGridAPIClient(app.config['SENDGRID_API_KEY'])
        self.sender = app.config['MAIL_DEFAULT_SENDER']
    
    def send_email(self, to_email, subject, html_content, attachments=None):
        """Send email using SendGrid"""
        message = Mail(
            from_email=self.sender,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        # Add attachments if any
        if attachments:
            for attachment_path in attachments:
                with open(attachment_path, 'rb') as f:
                    file_content = base64.b64encode(f.read()).decode()
                    
                attachment = Attachment()
                attachment.file_content = FileContent(file_content)
                attachment.file_type = FileType(f'application/{os.path.splitext(attachment_path)[1][1:]}')
                attachment.file_name = FileName(os.path.basename(attachment_path))
                attachment.disposition = Disposition('attachment')
                
                message.add_attachment(attachment)
        
        try:
            response = self.client.send(message)
            return response
        except Exception as e:
            print(f"Error sending email: {e}")
            return None
    
    def send_cuti_approval_email(self, cuti_request, user, pdf_path=None):
        """Send cuti approval email to employee"""
        status = "disetujui" if cuti_request.status.value == "approved" else "ditolak"
        
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; }}
                    .header {{ background-color: #f5f5f5; padding: 10px; text-align: center; }}
                    .content {{ padding: 15px; }}
                    .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
                    .approved {{ color: green; }}
                    .rejected {{ color: red; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>E-Cuti: Notifikasi Status Permintaan Cuti</h2>
                    </div>
                    <div class="content">
                        <p>Halo <b>{user.first_name} {user.last_name}</b>,</p>
                        <p>Permintaan cuti Anda dengan detail berikut telah <span class="{'approved' if status == 'disetujui' else 'rejected'}">{status}</span>:</p>
                        <ul>
                            <li><b>Jenis Cuti:</b> {cuti_request.cuti_type.value}</li>
                            <li><b>Tanggal:</b> {cuti_request.start_date.strftime('%d-%m-%Y')} s/d {cuti_request.end_date.strftime('%d-%m-%Y')}</li>
                            <li><b>Total Hari:</b> {cuti_request.total_days} hari kerja</li>
                            <li><b>Alasan:</b> {cuti_request.reason}</li>
                        </ul>
                        <p>Sisa cuti tahunan Anda: <b>{user.sisa_cuti} hari</b></p>
                        
                        {"<p>Catatan atasan: " + cuti_request.approval_notes + "</p>" if cuti_request.approval_notes else ""}
                        
                        {"<p>Surat cuti telah dilampirkan pada email ini.</p>" if pdf_path else ""}
                        
                        <p>Untuk informasi lebih lanjut, silakan login ke sistem E-Cuti.</p>
                    </div>
                    <div class="footer">
                        <p>Email ini dikirim otomatis oleh Sistem E-Cuti. Mohon tidak membalas email ini.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        attachments = [pdf_path] if pdf_path else None
        
        return self.send_email(
            to_email=user.email,
            subject=f"[E-Cuti] Permintaan Cuti {status.upper()}",
            html_content=html_content,
            attachments=attachments
        )
    
    def send_new_cuti_request_email(self, cuti_request, user, approver):
        """Send notification email to approver about new cuti request"""
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; }}
                    .header {{ background-color: #f5f5f5; padding: 10px; text-align: center; }}
                    .content {{ padding: 15px; }}
                    .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
                    .action-btn {{ display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>E-Cuti: Permintaan Cuti Baru</h2>
                    </div>
                    <div class="content">
                        <p>Halo <b>{approver.first_name} {approver.last_name}</b>,</p>
                        <p>Ada permintaan cuti baru yang memerlukan verifikasi Anda:</p>
                        <ul>
                            <li><b>Nama Pegawai:</b> {user.first_name} {user.last_name}</li>
                            <li><b>Departemen:</b> {user.department}</li>
                            <li><b>Jenis Cuti:</b> {cuti_request.cuti_type.value}</li>
                            <li><b>Tanggal:</b> {cuti_request.start_date.strftime('%d-%m-%Y')} s/d {cuti_request.end_date.strftime('%d-%m-%Y')}</li>
                            <li><b>Total Hari:</b> {cuti_request.total_days} hari kerja</li>
                            <li><b>Alasan:</b> {cuti_request.reason}</li>
                        </ul>
                        <p>Sisa cuti tahunan pegawai: <b>{user.sisa_cuti} hari</b></p>
                        
                        <p style="text-align: center; margin-top: 20px;">
                            <a href="https://ecuti.example.com/atasan/verifikasi/{cuti_request.id}" class="action-btn">Verifikasi Sekarang</a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>Email ini dikirim otomatis oleh Sistem E-Cuti. Mohon tidak membalas email ini.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(
            to_email=approver.email,
            subject=f"[E-Cuti] Permintaan Cuti Baru dari {user.first_name} {user.last_name}",
            html_content=html_content
        )