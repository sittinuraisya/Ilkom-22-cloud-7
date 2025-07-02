import requests
from flask import current_app
from datetime import datetime
import json

class SlackService:
    def __init__(self):
        """
        Initialize Slack service with webhook URL from app config.
        Requires SLACK_WEBHOOK_URL in app configuration.
        """
        self.webhook_url = current_app.config.get('SLACK_WEBHOOK_URL')
        self.default_username = current_app.config.get('SLACK_USERNAME', 'E-Cuti Bot')
        self.default_icon = current_app.config.get('SLACK_ICON', ':calendar:')
        self.timeout = current_app.config.get('SLACK_TIMEOUT', 5)
        
    def _send_payload(self, payload):
        """Internal method to send payload to Slack"""
        if not self.webhook_url:
            current_app.logger.warning("Slack webhook URL not configured")
            return False
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                error_msg = f"Slack API Error - Status: {response.status_code}, Response: {response.text}"
                current_app.logger.error(error_msg)
                return False
                
            return True
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Slack Connection Error: {str(e)}")
            return False
        except Exception as e:
            current_app.logger.error(f"Unexpected Slack Error: {str(e)}")
            return False
    
    def send_message(self, text, **kwargs):
        """
        Send basic message to Slack
        Args:
            text: Message text
            kwargs:
                - username: Override default username
                - icon_emoji: Override default icon
                - channel: Override default channel
                - attachments: List of attachment dicts
        Returns:
            bool: True if successful
        """
        payload = {
            "text": text,
            "username": kwargs.get('username', self.default_username),
            "icon_emoji": kwargs.get('icon_emoji', self.default_icon),
        }
        
        if 'channel' in kwargs:
            payload['channel'] = kwargs['channel']
            
        if 'attachments' in kwargs:
            payload['attachments'] = kwargs['attachments']
            
        return self._send_payload(payload)
    
    def send_leave_request(self, leave_data):
        """
        Send formatted leave request notification
        Args:
            leave_data: {
                'user_name': str,
                'leave_type': str,
                'start_date': date/datetime/str,
                'end_date': date/datetime/str,
                'duration': int,
                'reason': str (optional),
                'status': str (optional),
                'approver': str (optional),
                'user_email': str (optional)
            }
        Returns:
            bool: True if successful
        """
        if not self.webhook_url:
            return False
            
        try:
            # Format dates if they're datetime objects
            start_date = self._format_date(leave_data.get('start_date'))
            end_date = self._format_date(leave_data.get('end_date'))
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📅 New Leave Request",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Employee:*\n<{leave_data.get('user_email', 'mailto:')}|{leave_data['user_name']}>"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Leave Type:*\n{leave_data['leave_type']}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Dates:*\n{start_date} - {end_date}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Duration:*\n{leave_data['duration']} days"
                        }
                    ]
                }
            ]
            
            if leave_data.get('reason'):
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Reason:*\n{leave_data['reason']}"
                    }
                })
                
            if leave_data.get('status'):
                status_block = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Status:* {leave_data['status']}"
                    }
                }
                if leave_data.get('approver'):
                    status_block['text']['text'] += f"\n*Approver:* {leave_data['approver']}"
                blocks.append(status_block)
            
            # Add action buttons for approval if status is pending
            if leave_data.get('status', '').lower() == 'pending' and 'request_id' in leave_data:
                blocks.append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Approve",
                                "emoji": True
                            },
                            "style": "primary",
                            "value": f"approve_{leave_data['request_id']}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Reject",
                                "emoji": True
                            },
                            "style": "danger",
                            "value": f"reject_{leave_data['request_id']}"
                        }
                    ]
                })
            
            payload = {
                "blocks": blocks,
                "username": self.default_username,
                "icon_emoji": self.default_icon
            }
            
            return self._send_payload(payload)
            
        except Exception as e:
            current_app.logger.error(f"Failed to format leave notification: {str(e)}")
            return False
    
    def send_approval_notification(self, leave_data):
        """
        Send leave approval/rejection notification
        Args:
            leave_data: {
                'user_name': str,
                'leave_type': str,
                'status': 'Approved'/'Rejected',
                'approver': str,
                'reason': str (optional for rejection),
                'user_email': str (optional)
            }
        """
        status = leave_data.get('status', '').lower()
        if status not in ['approved', 'rejected']:
            current_app.logger.error("Invalid status for approval notification")
            return False
            
        try:
            color = "#36a64f" if status == 'approved' else "#ff0000"
            pretext = f"{leave_data['user_name']}'s leave request has been {status}"
            
            if status == 'rejected' and 'reason' in leave_data:
                pretext += f": {leave_data['reason']}"
            
            attachment = {
                "fallback": pretext,
                "color": color,
                "pretext": pretext,
                "fields": [
                    {
                        "title": "Employee",
                        "value": leave_data['user_name'],
                        "short": True
                    },
                    {
                        "title": "Leave Type",
                        "value": leave_data['leave_type'],
                        "short": True
                    },
                    {
                        "title": "Status",
                        "value": leave_data['status'],
                        "short": True
                    },
                    {
                        "title": "Processed By",
                        "value": leave_data['approver'],
                        "short": True
                    }
                ],
                "ts": datetime.now().timestamp()
            }
            
            return self.send_message(
                text=pretext,
                attachments=[attachment]
            )
            
        except Exception as e:
            current_app.logger.error(f"Failed to send approval notification: {str(e)}")
            return False
    
    def _format_date(self, date_value):
        """Format date for display"""
        if not date_value:
            return "N/A"
            
        if isinstance(date_value, str):
            return date_value
            
        if isinstance(date_value, datetime):
            return date_value.strftime('%d %b %Y')
            
        if hasattr(date_value, 'strftime'):
            return date_value.strftime('%d %b %Y')
            
        return str(date_value)