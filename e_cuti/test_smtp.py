import os
import smtplib
from dotenv import load_dotenv

load_dotenv()  # Load .env file

def test_connection():
    try:
        with smtplib.SMTP(os.getenv('MAIL_SERVER'), os.getenv('MAIL_PORT')) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
            print("✅ SMTP Login Successful!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_connection()