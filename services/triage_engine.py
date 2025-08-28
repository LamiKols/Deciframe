"""
Triage Engine Service for DeciFrame
Applies automated triage rules to trigger status updates, notifications, and escalations
"""

from datetime import datetime, timedelta
from models import TriageRule, Epic, BusinessCase, Project, Notification, User, AuditLog, NotificationEventEnum
from app import db
import logging

logger = logging.getLogger(__name__)


class TriageEngine:
    """
    Engine for applying automated triage rules to workflow entities
    """
    
    # Mapping of target names to model classes
    TARGET_MODELS = {
        'Epic': Epic,
        'BusinessCase': BusinessCase,
        'Project': Project
    }
    
    # Supported operators for rule conditions
    OPERATORS = {
        '=': 'equals',
        '>': 'greater_than',
        '<': 'less_than',
        'contains': 'contains',
        'days_ago': 'days_ago',
        '>=': 'greater_equal',
        '<=': 'less_equal'
    }
    
    # Supported actions
    ACTIONS = {
        'auto_approve': 'Auto Approve',
        'flag': 'Flag for Review',
        'notify_admin': 'Notify Administrators',
        'escalate': 'Escalate to Manager',
        'assign_reviewer': 'Assign Reviewer'
    }
    
    @classmethod
    def apply_all_rules(cls):
        """Apply all active triage rules"""
        logger.info("Starting triage rule application")
        
        try:
            rules = TriageRule.get_active_rules()
            applied_count = 0
            
            for rule in rules:
                count = cls._apply_single_rule(rule)
                applied_count += count
                logger.info(f"Applied rule '{rule.name}' to {count} entities")
            
            db.session.commit()
            logger.info(f"Triage rules completed. Applied {applied_count} actions total.")
            return applied_count
            
        except Exception as e:
            logger.error(f"Error applying triage rules: {e}")
            db.session.rollback()
            raise
    
    @classmethod
    def _apply_single_rule(cls, rule):
        """Apply a single triage rule"""
        try:
            # Get the target model class
            Model = cls.TARGET_MODELS.get(rule.target)
            if not Model:
                logger.warning(f"Unknown target model: {rule.target}")
                return 0
            
            # Build query based on rule conditions
            query = cls._build_query(Model, rule)
            if query is None:
                return 0
            
            # Get entities that match the rule
            entities = query.all()
            applied_count = 0
            
            for entity in entities:
                if cls._apply_action(entity, rule):
                    applied_count += 1
            
            return applied_count
            
        except Exception as e:
            logger.error(f"Error applying rule '{rule.name}': {e}")
            return 0
    
    @classmethod
    def _build_query(cls, Model, rule):
        """Build query based on rule conditions"""
        try:
            # Check if the field exists on the model
            if not hasattr(Model, rule.field):
                logger.warning(f"Field '{rule.field}' not found on {Model.__name__}")
                return None
            
            field_attr = getattr(Model, rule.field)
            query = Model.query
            
            # Apply operator-specific filtering
            if rule.operator == '=':
                query = query.filter(field_attr == rule.value)
            elif rule.operator == '>':
                try:
                    value = float(rule.value)
                    query = query.filter(field_attr > value)
                except ValueError:
                    logger.warning(f"Invalid numeric value for > operator: {rule.value}")
                    return None
            elif rule.operator == '<':
                try:
                    value = float(rule.value)
                    query = query.filter(field_attr < value)
                except ValueError:
                    logger.warning(f"Invalid numeric value for < operator: {rule.value}")
                    return None
            elif rule.operator == '>=':
                try:
                    value = float(rule.value)
                    query = query.filter(field_attr >= value)
                except ValueError:
                    logger.warning(f"Invalid numeric value for >= operator: {rule.value}")
                    return None
            elif rule.operator == '<=':
                try:
                    value = float(rule.value)
                    query = query.filter(field_attr <= value)
                except ValueError:
                    logger.warning(f"Invalid numeric value for <= operator: {rule.value}")
                    return None
            elif rule.operator == 'contains':
                query = query.filter(field_attr.like(f"%{rule.value}%"))
            elif rule.operator == 'days_ago':
                try:
                    days = int(rule.value)
                    cutoff = datetime.utcnow() - timedelta(days=days)
                    query = query.filter(field_attr < cutoff)
                except ValueError:
                    logger.warning(f"Invalid days value for days_ago operator: {rule.value}")
                    return None
            else:
                logger.warning(f"Unsupported operator: {rule.operator}")
                return None
            
            return query
            
        except Exception as e:
            logger.error(f"Error building query for rule: {e}")
            return None
    
    @classmethod
    def _apply_action(cls, entity, rule):
        """Apply the specified action to an entity"""
        try:
            action_applied = False
            previous_status = getattr(entity, 'status', None)
            
            if rule.action == 'auto_approve':
                if hasattr(entity, 'status') and entity.status != 'Approved':
                    entity.status = 'Approved'
                    if hasattr(entity, 'approved_at'):
                        entity.approved_at = datetime.utcnow()
                    action_applied = True
                    
            elif rule.action == 'flag':
                if hasattr(entity, 'status'):
                    entity.status = 'Flagged'
                    action_applied = True
                    
            elif rule.action == 'notify_admin':
                cls._notify_admins(entity, rule)
                action_applied = True
                
            elif rule.action == 'escalate':
                cls._escalate_to_manager(entity, rule)
                action_applied = True
            
            # Always log triage action to audit trail (whether status changed or notification sent)
            cls._log_comprehensive_triage_action(entity, rule, previous_status, action_applied)
            
            return action_applied
            
        except Exception as e:
            logger.error(f"Error applying action '{rule.action}' to {type(entity).__name__} {entity.id}: {e}")
            # Log the error as well
            cls._log_triage_error(entity, rule, str(e))
            return False
    
    @classmethod
    def _notify_admins(cls, entity, rule):
        """Send notification to all administrators"""
        try:
            # Get all admin users
            admins = User.query.filter_by(role='Admin').all()
            
            # Create message
            message = rule.message or f"Triage Rule '{rule.name}' triggered"
            url = cls._get_entity_url(entity)
            
            for admin in admins:
                notification = Notification(
                    user_id=admin.id,
                    message=f"{message} - {type(entity).__name__} #{entity.id}",
                    link=url,
                    event_type=NotificationEventEnum.TRIAGE_RULE_TRIGGERED
                )
                db.session.add(notification)
                
        except Exception as e:
            logger.error(f"Error notifying admins: {e}")
    
    @classmethod
    def _escalate_to_manager(cls, entity, rule):
        """Escalate entity to manager for review"""
        try:
            # Find the entity creator's manager
            creator = None
            if hasattr(entity, 'created_by'):
                creator = User.query.get(entity.created_by)
            elif hasattr(entity, 'submitted_by'):
                creator = User.query.get(entity.submitted_by)
            
            if creator and creator.manager:
                message = rule.message or f"Escalated for review: {type(entity).__name__} #{entity.id}"
                url = cls._get_entity_url(entity)
                
                notification = Notification(
                    user_id=creator.manager.id,
                    message=message,
                    link=url,
                    event_type=NotificationEventEnum.ESCALATION
                )
                db.session.add(notification)
                
        except Exception as e:
            logger.error(f"Error escalating to manager: {e}")
    
    @classmethod
    def _get_entity_url(cls, entity):
        """Get the URL for viewing an entity"""
        entity_type = type(entity).__name__.lower()
        
        if entity_type == 'epic':
            return f"/review/epic/{entity.id}"
        elif entity_type == 'businesscase':
            return f"/review/business-case/{entity.id}"
        elif entity_type == 'project':
            return f"/review/project/{entity.id}"
        else:
            return f"/admin/{entity_type}/{entity.id}"
    
    @classmethod
    def _log_comprehensive_triage_action(cls, entity, rule, previous_status, action_applied):
        """Log comprehensive triage action details to audit trail"""
        try:
            # Determine what changed
            changes = []
            current_status = getattr(entity, 'status', None)
            
            if previous_status != current_status:
                changes.append(f"status: {previous_status} → {current_status}")
            
            if rule.action == 'notify_admin':
                changes.append("admin notification sent")
            elif rule.action == 'escalate':
                changes.append("escalated to manager")
            
            # Create detailed audit log entry
            action_details = {
                'rule_id': rule.id,
                'rule_name': rule.name,
                'target_type': rule.target,
                'target_id': entity.id,
                'field_condition': f"{rule.field} {rule.operator} {rule.value}",
                'action_type': rule.action,
                'changes_made': changes,
                'previous_status': previous_status,
                'new_status': current_status,
                'action_applied': action_applied,
                'rule_message': rule.message
            }
            
            log_entry = AuditLog(
                user_id=None,  # System action
                action=f"triage:{rule.action}",
                module='triage_engine',
                target=f"{rule.target}",
                target_id=entity.id,
                details=action_details,
                timestamp=datetime.utcnow()
            )
            db.session.add(log_entry)
            
            # Also log in application logs
            logger.info(f"TRIAGE AUDIT: Rule '{rule.name}' (#{rule.id}) applied '{rule.action}' to {rule.target} #{entity.id} - Changes: {changes}")
            
        except Exception as e:
            logger.error(f"Error logging comprehensive triage action: {e}")
    
    @classmethod 
    def _log_triage_error(cls, entity, rule, error_message):
        """Log triage errors to audit trail"""
        try:
            log_entry = AuditLog(
                user_id=None,  # System action
                action="triage:error",
                module='triage_engine',
                target=f"{rule.target}",
                target_id=entity.id,
                details={
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'error': error_message,
                    'action_attempted': rule.action
                },
                timestamp=datetime.utcnow()
            )
            db.session.add(log_entry)
            
        except Exception as e:
            logger.error(f"Error logging triage error: {e}")
    
    @classmethod
    def _log_triage_action(cls, entity, rule):
        """Legacy method - maintained for backward compatibility"""
        previous_status = getattr(entity, 'status', None)
        cls._log_comprehensive_triage_action(entity, rule, previous_status, True)
    
    @classmethod
    def test_rule(cls, rule):
        """Test a rule without applying actions (dry run)"""
        try:
            Model = cls.TARGET_MODELS.get(rule.target)
            if not Model:
                return 0, f"Unknown target model: {rule.target}"
            
            query = cls._build_query(Model, rule)
            if query is None:
                return 0, "Invalid query conditions"
            
            count = query.count()
            entities = query.limit(5).all()  # Get sample for preview
            
            return count, [cls._entity_summary(e) for e in entities]
            
        except Exception as e:
            return 0, f"Error testing rule: {e}"
    
    @classmethod
    def _entity_summary(cls, entity):
        """Create a summary of an entity for testing purposes"""
        return {
            'id': entity.id,
            'type': type(entity).__name__,
            'title': getattr(entity, 'title', getattr(entity, 'name', f"ID {entity.id}")),
            'status': getattr(entity, 'status', 'Unknown'),
            'created_at': getattr(entity, 'created_at', None)
        }


def apply_rules():
    """Convenience function for applying all triage rules"""
    return TriageEngine.apply_all_rules()


def test_rule(rule):
    """Convenience function for testing a rule"""
    return TriageEngine.test_rule(rule)


def test_rule_dry_run(rule):
    """Test a rule without applying actions (dry run) - returns count and sample data"""
    count, data = TriageEngine.test_rule(rule)
    return {
        'count': count,
        'sample_entities': data if isinstance(data, list) else [],
        'error': data if isinstance(data, str) else None
    }