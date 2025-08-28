"""
Comprehensive audit logging system
"""

import json
from datetime import datetime, timedelta
from flask import request
from flask_login import current_user
from models import db, AuditLog
import logging

logger = logging.getLogger(__name__)


def audit(event, obj_type, obj_id=None, before=None, after=None, actor_id=None, details=None):
    """
    Create an audit log entry
    
    Args:
        event: Action performed (e.g., 'CREATE_USER', 'UPDATE_ROLE', 'DELETE_DEPARTMENT')
        obj_type: Type of object affected (e.g., 'User', 'Department', 'Organization')
        obj_id: ID of the affected object
        before: Previous state (dict or object)
        after: New state (dict or object)
        actor_id: User ID performing the action (defaults to current_user)
        details: Additional details about the action
    """
    try:
        # Get actor information
        if actor_id is None and current_user.is_authenticated:
            actor_id = current_user.id
            actor_org_id = current_user.organization_id
        else:
            # Fallback for system actions
            actor_org_id = None
        
        # Serialize before/after states
        before_json = _serialize_state(before) if before else None
        after_json = _serialize_state(after) if after else None
        
        # Create audit log entry
        audit_entry = AuditLog(
            user_id=actor_id,
            action=event,
            object_type=obj_type,
            object_id=obj_id,
            before_state=before_json,
            after_state=after_json,
            details=details or f"{event} performed on {obj_type} {obj_id}",
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent', '') if request else None,
            organization_id=actor_org_id,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(audit_entry)
        db.session.commit()
        
        logger.info(f"Audit log created: {event} on {obj_type} {obj_id} by user {actor_id}")
        return audit_entry
        
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        # Don't let audit failures break the main operation
        db.session.rollback()
        return None


def _serialize_state(state):
    """Serialize an object state to JSON for audit logging"""
    if state is None:
        return None
    
    if isinstance(state, dict):
        return json.dumps(state, default=str, sort_keys=True)
    
    # Handle SQLAlchemy models
    if hasattr(state, '__dict__'):
        # Extract relevant attributes, excluding private/system attributes
        serializable = {}
        for key, value in state.__dict__.items():
            if not key.startswith('_') and key != 'password_hash':
                # Convert datetime objects to ISO format
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif hasattr(value, 'value'):  # Handle enums
                    value = value.value
                serializable[key] = value
        return json.dumps(serializable, default=str, sort_keys=True)
    
    # Fallback to string representation
    return str(state)


def audit_user_action(action, user_obj, before_state=None, after_state=None):
    """Specialized audit function for user-related actions"""
    return audit(
        event=f"USER_{action.upper()}",
        obj_type="User",
        obj_id=user_obj.id if user_obj else None,
        before=before_state,
        after=after_state,
        details=f"User {action.lower()}: {getattr(user_obj, 'email', 'unknown')}"
    )


def audit_organization_action(action, org_obj, before_state=None, after_state=None):
    """Specialized audit function for organization-related actions"""
    return audit(
        event=f"ORG_{action.upper()}",
        obj_type="Organization", 
        obj_id=org_obj.id if org_obj else None,
        before=before_state,
        after=after_state,
        details=f"Organization {action.lower()}: {getattr(org_obj, 'name', 'unknown')}"
    )


def audit_department_action(action, dept_obj, before_state=None, after_state=None):
    """Specialized audit function for department-related actions"""
    return audit(
        event=f"DEPT_{action.upper()}",
        obj_type="Department",
        obj_id=dept_obj.id if dept_obj else None,
        before=before_state,
        after=after_state,
        details=f"Department {action.lower()}: {getattr(dept_obj, 'name', 'unknown')}"
    )


def audit_role_change(user_obj, old_role, new_role):
    """Specialized audit function for role changes"""
    return audit(
        event="ROLE_CHANGE",
        obj_type="User",
        obj_id=user_obj.id,
        before={'role': old_role.value if hasattr(old_role, 'value') else str(old_role)},
        after={'role': new_role.value if hasattr(new_role, 'value') else str(new_role)},
        details=f"Role changed from {old_role} to {new_role} for {user_obj.email}"
    )


def get_audit_trail(obj_type=None, obj_id=None, user_id=None, organization_id=None, limit=100):
    """
    Retrieve audit trail with filters
    
    Args:
        obj_type: Filter by object type
        obj_id: Filter by object ID
        user_id: Filter by user who performed action
        organization_id: Filter by organization
        limit: Maximum number of entries to return
    """
    try:
        query = AuditLog.query
        
        if obj_type:
            query = query.filter(AuditLog.object_type == obj_type)
        if obj_id:
            query = query.filter(AuditLog.object_id == obj_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if organization_id:
            query = query.filter(AuditLog.organization_id == organization_id)
        
        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
    except Exception as e:
        logger.error(f"Failed to retrieve audit trail: {e}")
        return []


def cleanup_old_audit_logs(days_to_keep=365):
    """Clean up audit logs older than specified days"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted_count = AuditLog.query.filter(
            AuditLog.timestamp < cutoff_date
        ).delete()
        
        db.session.commit()
        logger.info(f"Cleaned up {deleted_count} old audit log entries")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup audit logs: {e}")
        db.session.rollback()
        return 0