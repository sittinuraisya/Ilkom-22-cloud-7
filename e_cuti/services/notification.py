from models import Notification, db

def send_notification(user_id, title, message, link=None):
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link,
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        
        # Trigger real-time update
        socketio.emit('new_notification', {
            'user_id': user_id,
            'title': title,
            'message': message
        }, namespace='/notifications')
        
    except Exception as e:
        current_app.logger.error(f"Failed to send notification: {str(e)}")