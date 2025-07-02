from app import create_app
from flask_mail import Mail, Message
import logging
from datetime import datetime

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()
mail = Mail(app)

def send_test_email():
    """Send a test email with comprehensive error handling"""
    with app.app_context():
        try:
            # Validate configuration
            if not all([app.config['MAIL_SERVER'], app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']]):
                raise ValueError("Incomplete email configuration")

            # Prepare message
            msg = Message(
                subject=f"Test Email dari Flask - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=['kelompok7cc2025@gmail.com'],  # Replace with actual email
                body='This is a plain text test email from Flask'
            )
            msg.html = """
            <h1>Test Email</h1>
            <p>This is a <strong>HTML test email</strong> from Flask</p>
            <p>Sent at: {}</p>
            """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            # Send email
            mail.send(msg)
            logger.info("Email successfully sent to %s", msg.recipients)
            return True

        except ValueError as ve:
            logger.error("Configuration error: %s", str(ve))
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP Authentication Failed. Check your username/password")
        except smtplib.SMTPException as smtp_error:
            logger.error("SMTP Protocol Error: %s", str(smtp_error))
        except Exception as e:
            logger.error("Unexpected error: %s", str(e), exc_info=True)
        
        return False

if __name__ == '__main__':
    if send_test_email():
        print("✅ Email sent successfully!")
    else:
        print("❌ Failed to send email. Check logs for details.")