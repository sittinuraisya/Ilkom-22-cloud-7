import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GoogleCalendarService:
    def __init__(self, app_config=None):
        """
        Initialize with optional Flask app config.
        If no app config provided, uses environment variables.
        """
        self.app_config = app_config
        self._configure_client()
        self._setup_paths()
        self._validate_config()

    def _configure_client(self):
        """Configure OAuth client from config"""
        self.client_config = {
            "web": {
                "client_id": self._get_config('GOOGLE_CLIENT_ID'),
                "client_secret": self._get_config('GOOGLE_CLIENT_SECRET'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [
                    self._get_config('GOOGLE_REDIRECT_URI', 'http://localhost:5000/callback')
                ]
            }
        }
        self.scopes = ['https://www.googleapis.com/auth/calendar']

    def _get_config(self, key, default=None):
        """Get config from app config or environment variables"""
        if self.app_config and key in self.app_config:
            return self.app_config[key]
        return os.getenv(key, default)

    def _setup_paths(self):
        """Set up file paths for token storage"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.credentials_dir = os.path.join(base_dir, 'credentials')
        os.makedirs(self.credentials_dir, exist_ok=True)
        self.token_file = os.path.join(self.credentials_dir, 'token.json')

    def _validate_config(self):
        """Validate required configuration"""
        required_config = [
            'GOOGLE_CLIENT_ID',
            'GOOGLE_CLIENT_SECRET'
        ]
        for config in required_config:
            if not self._get_config(config):
                raise ValueError(f"Missing required config: {config}")

    def _save_credentials(self, creds):
        """Save credentials to file"""
        try:
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        except IOError as e:
            logging.error(f"Failed to save credentials: {str(e)}")
            raise

    def _load_credentials(self):
        """Load credentials from file"""
        if not os.path.exists(self.token_file):
            return None
            
        try:
            return Credentials.from_authorized_user_file(self.token_file, self.scopes)
        except Exception as e:
            logging.error(f"Failed to load credentials: {str(e)}")
            return None

    def get_credentials(self):
        """Get valid credentials, refreshing if needed"""
        creds = self._load_credentials()
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = Flow.from_client_config(
                    self.client_config,
                    scopes=self.scopes,
                    redirect_uri=self._get_config('GOOGLE_REDIRECT_URI')
                )
                auth_url, _ = flow.authorization_url(prompt='consent')
                print('Please visit this URL to authorize:')
                print(auth_url)
                code = input('Enter authorization code: ')
                flow.fetch_token(code=code)
                creds = flow.credentials
                self._save_credentials(creds)
        
        return creds

    def create_cuti_event(self, cuti_data):
        """Create a leave event in Google Calendar"""
        try:
            creds = self.get_credentials()
            service = build('calendar', 'v3', credentials=creds)

            event = {
                'summary': f'Cuti {cuti_data["jenis_cuti"]} - {cuti_data["user_name"]}',
                'description': (
                    f"Jenis Cuti: {cuti_data['jenis_cuti']}\n"
                    f"Alasan: {cuti_data['perihal_cuti']}\n"
                    f"Status: Diajukan"
                ),
                'start': {
                    'date': cuti_data['tanggal_mulai'],
                    'timeZone': 'Asia/Makassar'
                },
                'end': {
                    'date': (datetime.strptime(cuti_data['tanggal_selesai'], '%Y-%m-%d') + 
                            timedelta(days=1)).strftime('%Y-%m-%d'),
                    'timeZone': 'Asia/Makassar'
                },
                'attendees': [{'email': cuti_data['user_email']}],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30}
                    ]
                }
            }

            created_event = service.events().insert(
                calendarId='primary',
                body=event
            ).execute()

            logging.info(f"Calendar event created: {created_event.get('htmlLink')}")
            return {
                'success': True,
                'event_link': created_event.get('htmlLink'),
                'event_id': created_event.get('id')
            }

        except Exception as e:
            logging.error(f"Failed to create calendar event: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_cuti_event(self, event_id):
        """Delete a leave event from Google Calendar"""
        try:
            creds = self.get_credentials()
            service = build('calendar', 'v3', credentials=creds)
            
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            logging.info(f"Deleted calendar event: {event_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to delete calendar event: {str(e)}")
            return False