from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import current_app
import os
from datetime import datetime, timedelta
import json

class GoogleCalendarService:
    def __init__(self):
        """
        Initialize Google Calendar service with proper authentication.
        Requires the following app config settings:
        - GOOGLE_CREDENTIALS_PATH: Path to credentials folder
        - GOOGLE_SCOPES: List of OAuth scopes
        - GOOGLE_CALENDAR_ID: Calendar ID to use (default 'primary')
        """
        try:
            self.credentials = self._authenticate()
            self.service = build('calendar', 'v3', credentials=self.credentials)
            self.calendar_id = current_app.config.get('GOOGLE_CALENDAR_ID', 'primary')
        except Exception as e:
            current_app.logger.error(f"Failed to initialize Google Calendar Service: {str(e)}")
            raise

    def _authenticate(self):
        """Handle OAuth2 authentication for Google Calendar API"""
        creds = None
        credentials_path = current_app.config['GOOGLE_CREDENTIALS_PATH']
        token_path = os.path.join(credentials_path, 'token.json')
        
        # Load existing credentials if available
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, current_app.config['GOOGLE_SCOPES'])
            except json.JSONDecodeError:
                current_app.logger.warning("Invalid token file, will recreate")
                os.unlink(token_path)
            except Exception as e:
                current_app.logger.error(f"Error loading credentials: {str(e)}")
                os.unlink(token_path)
        
        # If no valid credentials, create new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    current_app.logger.error(f"Failed to refresh token: {str(e)}")
                    creds = None
            
            if not creds:
                client_secrets_path = os.path.join(credentials_path, 'client_secrets.json')
                if not os.path.exists(client_secrets_path):
                    raise FileNotFoundError("Client secrets file not found")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_path,
                    current_app.config['GOOGLE_SCOPES']
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for next run
            with open(token_path, 'w') as token_file:
                token_file.write(creds.to_json())
        
        return creds

    def create_event(self, event_data):
        """
        Create a new calendar event
        Args:
            event_data (dict): {
                'summary': str,
                'description': str,
                'start': datetime,
                'end': datetime,
                'attendees': list of emails,
                'timezone': str (optional),
                'all_day': bool (optional)
            }
        Returns:
            dict: {'success': bool, 'event_id': str, 'error': str}
        """
        try:
            timezone = event_data.get('timezone', 'Asia/Jakarta')
            
            if event_data.get('all_day', False):
                start = {'date': event_data['start'].strftime('%Y-%m-%d')}
                end = {'date': (event_data['end'] + timedelta(days=1)).strftime('%Y-%m-%d')}
            else:
                start = {
                    'dateTime': event_data['start'].isoformat(),
                    'timeZone': timezone
                }
                end = {
                    'dateTime': event_data['end'].isoformat(),
                    'timeZone': timezone
                }

            event_body = {
                'summary': event_data.get('summary'),
                'description': event_data.get('description', ''),
                'start': start,
                'end': end,
                'reminders': {
                    'useDefault': True,
                },
            }

            if 'attendees' in event_data:
                event_body['attendees'] = [{'email': email} for email in event_data['attendees']]

            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_body
            ).execute()

            return {
                'success': True,
                'event_id': created_event['id'],
                'html_link': created_event.get('htmlLink'),
                'event': created_event
            }

        except HttpError as e:
            error_details = json.loads(e.content.decode()).get('error', {})
            current_app.logger.error(f"Google Calendar API Error: {error_details.get('message', str(e))}")
            return {
                'success': False,
                'error': error_details.get('message', 'Google Calendar API Error'),
                'code': error_details.get('code')
            }
        except Exception as e:
            current_app.logger.error(f"Error creating calendar event: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def update_event(self, event_id, event_data):
        """Update an existing calendar event"""
        try:
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()

            # Update only provided fields
            if 'summary' in event_data:
                event['summary'] = event_data['summary']
            if 'description' in event_data:
                event['description'] = event_data['description']
            if 'start' in event_data:
                event['start'] = event_data['start']
            if 'end' in event_data:
                event['end'] = event_data['end']
            if 'attendees' in event_data:
                event['attendees'] = [{'email': email} for email in event_data['attendees']]

            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()

            return {
                'success': True,
                'event_id': updated_event['id'],
                'html_link': updated_event.get('htmlLink')
            }

        except HttpError as e:
            error_details = json.loads(e.content.decode()).get('error', {})
            current_app.logger.error(f"Google Calendar Update Error: {error_details.get('message', str(e))}")
            return {
                'success': False,
                'error': error_details.get('message', 'Failed to update event'),
                'code': error_details.get('code')
            }

    def delete_event(self, event_id):
        """Delete a calendar event"""
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            return {'success': True}
        except HttpError as e:
            if e.resp.status == 404:
                return {'success': True}  # Already deleted
            error_details = json.loads(e.content.decode()).get('error', {})
            current_app.logger.error(f"Google Calendar Delete Error: {error_details.get('message', str(e))}")
            return {
                'success': False,
                'error': error_details.get('message', 'Failed to delete event'),
                'code': error_details.get('code')
            }

    def list_events(self, time_min=None, time_max=None, max_results=250):
        """
        List events from calendar
        Args:
            time_min: datetime for start of range
            time_max: datetime for end of range
            max_results: maximum number of results
        Returns:
            list: List of event dictionaries
        """
        try:
            time_min = time_min or datetime.utcnow()
            time_max = time_max or (time_min + timedelta(days=30))
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
        except HttpError as e:
            error_details = json.loads(e.content.decode()).get('error', {})
            current_app.logger.error(f"Google Calendar List Error: {error_details.get('message', str(e))}")
            return []
        except Exception as e:
            current_app.logger.error(f"Error listing calendar events: {str(e)}")
            return []

    def get_event(self, event_id):
        """Get a specific event by ID"""
        try:
            return self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
        except HttpError as e:
            if e.resp.status == 404:
                return None
            error_details = json.loads(e.content.decode()).get('error', {})
            current_app.logger.error(f"Google Calendar Get Error: {error_details.get('message', str(e))}")
            return None