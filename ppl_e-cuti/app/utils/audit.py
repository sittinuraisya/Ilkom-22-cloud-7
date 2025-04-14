from app.models.user import AuditLog, db
from flask_login import current_user
from flask import request
import json

def log_activity(action, entity, entity_id, old_value=None, new_value=None):
    """Log user activity for auditing purposes"""
    if isinstance(old_value, dict) or isinstance(old_value, list):
        old_value = json.dumps(old_value)
    
    if isinstance(new_value, dict) or isinstance(new_value, list):
        new_value = json.dumps(new_value)
        
    audit = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        entity=entity,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=request.remote_addr
    )
    
    db.session.add(audit)
    db.session.commit()
    
    return audit