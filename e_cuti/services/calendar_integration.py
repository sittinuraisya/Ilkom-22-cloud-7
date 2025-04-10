from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os

class GoogleCalendarService:
    def __init__(self, token_path='token.json'):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.token_path = token_path

    def get_credentials(self):
        if not os.path.exists(self.token_path):
            raise Exception("Token not found")
        return Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

    def create_cuti_event(self, cuti_data):
        creds = self.get_credentials()
        service = build('calendar', 'v3', credentials=creds)

        event = {
            'summary': f'Cuti {cuti_data["jenis_cuti"]}',
            'description': cuti_data["perihal_cuti"],
            'start': {
                'dateTime': f'{cuti_data["tanggal_mulai"]}T00:00:00',
                'timeZone': 'Asia/Makassar',
            },
            'end': {
                'dateTime': f'{cuti_data["tanggal_selesai"]}T23:59:59',
                'timeZone': 'Asia/Makassar',
            },
            'attendees': [
                {'email': cuti_data["email_atasan"]},
            ],
        }

        return service.events().insert(
            calendarId='primary',
            body=event
        ).execute()