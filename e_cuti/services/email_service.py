from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

class EmailService:
    def __init__(self):
        self.sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        self.sender = 'noreply@ecuti-sultra.com'
    
    def send(self, to, subject, template):
        message = Mail(
            from_email=self.sender,
            to_emails=to,
            subject=f"[E-Cuti Sultra] {subject}",
            html_content=template)
        try:
            response = self.sg.send(message)
            return response.status_code == 202
        except Exception as e:
            print(f"Email error: {str(e)}")
            return False