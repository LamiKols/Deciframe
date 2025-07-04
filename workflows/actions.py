"""
Workflow Action Handlers - Implementation of workflow actions
"""

import logging
from typing import Dict, Any, Callable
from datetime import datetime, timedelta
from workflows.context import WorkflowContext

logger = logging.getLogger(__name__)

def send_notification(step: dict, context: WorkflowContext) -> dict:
    """Send notification to specified target"""
    target = step.get('target', 'unknown')
    template = step.get('template', 'default')
    
    logger.info(f"📧 Sending notification to {target} using template {template}")
    
    try:
        # Import here to avoid circular imports
        from notifications.service import NotificationService
        
        # Determine recipients based on target
        recipients = _resolve_recipients(target, context)
        
        if not recipients:
            logger.warning(f"⚠️ Could not resolve target users for: {target}")
            return {'status': 'warning', 'message': f'Could not resolve target: {target}'}
        
        notification_service = NotificationService()
        sent_notifications = []
        
        # Send notification to all resolved recipients
        for user_id in recipients:
            try:
                # Create notification based on event type and template
                event_type = _map_template_to_event_type(template)
                notification_context = _build_notification_context(context)
                
                # Send notification
                result = notification_service.create_notification(
                    user_id=user_id,
                    event_type=event_type,
                    context=notification_context
                )
                
                sent_notifications.append({
                    'user_id': user_id,
                    'notification_id': result.get('notification_id'),
                    'status': 'sent'
                })
                
            except Exception as e:
                logger.error(f"❌ Failed to send notification to user {user_id}: {e}")
                sent_notifications.append({
                    'user_id': user_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        logger.info(f"✅ Notifications processed for {len(sent_notifications)} recipients")
        return {
            'status': 'success',
            'recipients_count': len(recipients),
            'notifications': sent_notifications
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to send notification: {e}")
        return {'status': 'error', 'message': str(e)}

def create_task(step: dict, context: WorkflowContext) -> dict:
    """Create a task for specified target"""
    assignee_role = step.get('assignee', step.get('target', 'unknown'))
    title = step.get('title', 'Workflow Generated Task')
    description = step.get('description', '')
    due_days = step.get('due_days', 7)
    
    logger.info(f"📋 Creating task '{title}' for {assignee_role}")
    
    try:
        # Import here to avoid circular imports
        from models import Task, db
        
        # Determine assignee ID from context and role
        assignee_id = _resolve_assignee(assignee_role, context)
        
        if not assignee_id:
            logger.warning(f"⚠️ Could not resolve assignee for task: {assignee_role}")
            return {'status': 'warning', 'message': f'Could not resolve assignee: {assignee_role}'}
        
        # Compute due date
        due_date = _compute_due_date(due_days)
        
        # Create task with enhanced context
        task = Task(
            title=title,
            description=description,
            assigned_to=assignee_id,
            created_by=context.get_user_id() or 1,  # System user fallback
            status='Open',
            priority=step.get('priority', 'Medium'),
            due_date=due_date
        )
        
        db.session.add(task)
        db.session.commit()
        
        logger.info(f"✅ Task created successfully: {task.id}")
        return {
            'status': 'success', 
            'task_id': task.id, 
            'assigned_to': assignee_id,
            'due_date': due_date.isoformat() if due_date else None,
            'title': title
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to create task: {e}")
        return {'status': 'error', 'message': str(e)}

def escalate_to_manager(step: dict, context: WorkflowContext) -> dict:
    """Escalate issue to department manager"""
    target = step.get('target', 'department_manager')
    
    logger.info(f"🚨 Escalating to {target}")
    
    try:
        # Find department manager
        department_id = context.get_department_id()
        
        if not department_id:
            logger.warning("⚠️ No department ID found for escalation")
            return {'status': 'warning', 'message': 'No department ID available'}
        
        # Import here to avoid circular imports
        from models import User
        
        # Find department manager
        manager = User.query.filter_by(dept_id=department_id, role='Manager').first()
        
        if not manager:
            logger.warning(f"⚠️ No manager found for department {department_id}")
            return {'status': 'warning', 'message': f'No manager found for department {department_id}'}
        
        # Create escalation notification
        escalation_step = {
            'target': 'department_manager',
            'template': 'escalation_alert'
        }
        
        result = send_notification(escalation_step, context)
        
        logger.info(f"✅ Escalated to manager: {manager.name}")
        return {'status': 'success', 'manager_id': manager.id, 'manager_name': manager.name, 'notification_result': result}
        
    except Exception as e:
        logger.error(f"❌ Failed to escalate: {e}")
        return {'status': 'error', 'message': str(e)}

def auto_approve(step: dict, context: WorkflowContext) -> dict:
    """Auto-approve business case or request"""
    logger.info("✅ Auto-approving based on workflow conditions")
    
    try:
        # Get case data
        case_data = context.get_case_data()
        
        if not case_data:
            logger.warning("⚠️ No case data available for auto-approval")
            return {'status': 'warning', 'message': 'No case data available'}
        
        # Import here to avoid circular imports
        from models import BusinessCase, db
        
        # Find and update the business case
        case_id = case_data.get('id')
        if case_id:
            case = BusinessCase.query.get(case_id)
            if case:
                case.status = 'Approved'
                case.approved_at = datetime.utcnow()
                case.approved_by = context.get_user_id()
                db.session.commit()
                
                logger.info(f"✅ Case {case_id} auto-approved")
                return {'status': 'success', 'case_id': case_id, 'approved_at': case.approved_at.isoformat()}
        
        logger.warning("⚠️ Could not find case to auto-approve")
        return {'status': 'warning', 'message': 'Case not found'}
        
    except Exception as e:
        logger.error(f"❌ Failed to auto-approve: {e}")
        return {'status': 'error', 'message': str(e)}

def schedule_follow_up(step: dict, context: WorkflowContext) -> dict:
    """Schedule a follow-up action"""
    delay_hours = step.get('delay_hours', 24)
    follow_up_action = step.get('follow_up_action', 'status_check')
    
    logger.info(f"📅 Scheduling follow-up in {delay_hours} hours: {follow_up_action}")
    
    try:
        # Import here to avoid circular imports
        from models import ScheduledTask, db
        
        # Create scheduled task
        scheduled_task = ScheduledTask(
            task_type=follow_up_action,
            scheduled_for=datetime.utcnow() + timedelta(hours=delay_hours),
            context_data=context.to_dict(),
            created_by=context.get_user_id(),
            status='Pending'
        )
        
        db.session.add(scheduled_task)
        db.session.commit()
        
        logger.info(f"✅ Follow-up scheduled: {scheduled_task.id}")
        return {'status': 'success', 'scheduled_task_id': scheduled_task.id, 'scheduled_for': scheduled_task.scheduled_for.isoformat()}
        
    except Exception as e:
        logger.error(f"❌ Failed to schedule follow-up: {e}")
        return {'status': 'error', 'message': str(e)}

def create_business_case(step: dict, context: WorkflowContext) -> dict:
    """Create a business case from problem data"""
    logger.info("📊 Creating business case from problem")
    
    try:
        problem_data = context.get_problem_data()
        
        if not problem_data:
            logger.warning("⚠️ No problem data available for business case creation")
            return {'status': 'warning', 'message': 'No problem data available'}
        
        # Import here to avoid circular imports
        from models import BusinessCase, db
        from business.utils import generate_case_code
        
        # Create business case
        case = BusinessCase(
            code=generate_case_code(),
            title=f"Business Case for Problem: {problem_data.get('title', 'Unknown')}",
            summary=f"Automatically generated from problem: {problem_data.get('description', '')}",
            problem_id=problem_data.get('id'),
            created_by=context.get_user_id(),
            dept_id=context.get_department_id(),
            case_type='Reactive',
            status='Draft',
            estimated_cost=problem_data.get('estimated_cost', 0),
            priority=problem_data.get('priority', 'Medium')
        )
        
        db.session.add(case)
        db.session.commit()
        
        logger.info(f"✅ Business case created: {case.id}")
        return {'status': 'success', 'case_id': case.id, 'case_code': case.code}
        
    except Exception as e:
        logger.error(f"❌ Failed to create business case: {e}")
        return {'status': 'error', 'message': str(e)}

def assign_business_analyst(step: dict, context: WorkflowContext) -> dict:
    """Assign available business analyst to case"""
    logger.info("👤 Assigning business analyst")
    
    try:
        # Import here to avoid circular imports
        from models import User, BusinessCase, db
        
        # Find available business analyst
        ba = User.query.filter_by(role='BA').first()
        
        if not ba:
            logger.warning("⚠️ No business analyst available")
            return {'status': 'warning', 'message': 'No business analyst available'}
        
        # Get case data and assign BA
        case_data = context.get_case_data()
        if case_data and case_data.get('id'):
            case = BusinessCase.query.get(case_data['id'])
            if case:
                case.assigned_ba = ba.id
                db.session.commit()
                
                logger.info(f"✅ Business analyst {ba.name} assigned to case {case.id}")
                return {'status': 'success', 'ba_id': ba.id, 'ba_name': ba.name, 'case_id': case.id}
        
        logger.warning("⚠️ No case found to assign BA to")
        return {'status': 'warning', 'message': 'No case found'}
        
    except Exception as e:
        logger.error(f"❌ Failed to assign business analyst: {e}")
        return {'status': 'error', 'message': str(e)}

def log_workflow_action(step: dict, context: WorkflowContext) -> dict:
    """Log workflow action for audit purposes"""
    action_message = step.get('message', 'Workflow action executed')
    
    logger.info(f"📝 Logging workflow action: {action_message}")
    
    try:
        # Import here to avoid circular imports
        from models import AuditLog, db
        
        # Create audit log entry
        audit_log = AuditLog(
            user_id=context.get_user_id(),
            action=f"workflow_action_{context.get_workflow_name()}",
            details=action_message,
            ip_address='127.0.0.1',  # Workflow system
            user_agent='DeciFrame Workflow Engine'
        )
        
        db.session.add(audit_log)
        db.session.commit()
        
        logger.info(f"✅ Workflow action logged: {audit_log.id}")
        return {'status': 'success', 'audit_log_id': audit_log.id}
        
    except Exception as e:
        logger.error(f"❌ Failed to log workflow action: {e}")
        return {'status': 'error', 'message': str(e)}

# Helper Functions

def _resolve_recipients(target: str, context: WorkflowContext) -> list:
    """Resolve target string to list of user IDs"""
    try:
        # Import here to avoid circular imports
        from models import User
        
        recipients = []
        
        if target == 'problem_owner':
            problem_data = context.get_problem_data()
            if problem_data and problem_data.get('created_by'):
                recipients.append(problem_data['created_by'])
        
        elif target == 'case_owner':
            case_data = context.get_case_data()
            if case_data and case_data.get('created_by'):
                recipients.append(case_data['created_by'])
        
        elif target == 'project_manager':
            project_data = context.get_project_data()
            if project_data and project_data.get('project_manager'):
                recipients.append(project_data['project_manager'])
            else:
                # Fallback: find any PM
                pm = User.query.filter_by(role='PM').first()
                if pm:
                    recipients.append(pm.id)
        
        elif target == 'business_analyst':
            case_data = context.get_case_data()
            if case_data and case_data.get('assigned_ba'):
                recipients.append(case_data['assigned_ba'])
            else:
                # Fallback: find any BA
                ba = User.query.filter_by(role='BA').first()
                if ba:
                    recipients.append(ba.id)
        
        elif target == 'department_manager':
            department_id = context.get_department_id()
            if department_id:
                manager = User.query.filter_by(dept_id=department_id, role='Manager').first()
                if manager:
                    recipients.append(manager.id)
        
        elif target == 'milestone_owner':
            milestone_data = context.get_milestone_data()
            if milestone_data and milestone_data.get('assigned_to'):
                recipients.append(milestone_data['assigned_to'])
        
        elif target == 'stakeholders':
            # Get all relevant stakeholders based on context
            stakeholders = set()
            
            # Add problem owner
            problem_data = context.get_problem_data()
            if problem_data and problem_data.get('created_by'):
                stakeholders.add(problem_data['created_by'])
            
            # Add case owner and BA
            case_data = context.get_case_data()
            if case_data:
                if case_data.get('created_by'):
                    stakeholders.add(case_data['created_by'])
                if case_data.get('assigned_ba'):
                    stakeholders.add(case_data['assigned_ba'])
            
            # Add project manager
            project_data = context.get_project_data()
            if project_data and project_data.get('project_manager'):
                stakeholders.add(project_data['project_manager'])
            
            # Add department manager
            department_id = context.get_department_id()
            if department_id:
                manager = User.query.filter_by(dept_id=department_id, role='Manager').first()
                if manager:
                    stakeholders.add(manager.id)
            
            recipients = list(stakeholders)
        
        elif target == 'all_employees':
            # Get all active users
            all_users = User.query.filter_by(is_active=True).all()
            recipients = [user.id for user in all_users]
        
        elif target == 'executives':
            # Get CEO and Directors
            executives = User.query.filter(User.role.in_(['CEO', 'Director'])).all()
            recipients = [exec.id for exec in executives]
        
        return recipients
        
    except Exception as e:
        logger.error(f"❌ Error resolving recipients for {target}: {e}")
        return []

def _resolve_assignee(assignee_role: str, context: WorkflowContext) -> int:
    """Resolve assignee role to specific user ID"""
    try:
        # Import here to avoid circular imports
        from models import User
        
        if assignee_role in ['problem_owner', 'case_owner']:
            return _resolve_target_user(assignee_role, context)
        
        elif assignee_role == 'available_ba':
            # Find available business analyst (simple: first BA found)
            ba = User.query.filter_by(role='BA').first()
            return ba.id if ba else None
        
        elif assignee_role == 'department_manager':
            department_id = context.get_department_id()
            if department_id:
                manager = User.query.filter_by(dept_id=department_id, role='Manager').first()
                return manager.id if manager else None
        
        elif assignee_role == 'project_manager':
            project_data = context.get_project_data()
            if project_data and project_data.get('project_manager'):
                return project_data['project_manager']
            # Fallback: any PM
            pm = User.query.filter_by(role='PM').first()
            return pm.id if pm else None
        
        elif assignee_role == 'system_admin':
            # Find system administrator
            admin = User.query.filter_by(role='Admin').first()
            return admin.id if admin else None
        
        elif assignee_role == 'ceo':
            # Find CEO
            ceo = User.query.filter_by(role='CEO').first()
            return ceo.id if ceo else None
        
        else:
            # Try to resolve as target user
            return _resolve_target_user(assignee_role, context)
        
    except Exception as e:
        logger.error(f"❌ Error resolving assignee {assignee_role}: {e}")
        return None

def _compute_due_date(due_days: int = None) -> datetime:
    """Compute due date from number of days"""
    if due_days is not None and due_days > 0:
        return datetime.utcnow() + timedelta(days=due_days)
    return datetime.utcnow() + timedelta(days=7)  # Default 7 days

def _resolve_target_user(target: str, context: WorkflowContext) -> int:
    """Resolve target string to actual user ID"""
    try:
        # Import here to avoid circular imports
        from models import User
        
        if target == 'problem_owner':
            problem_data = context.get_problem_data()
            return problem_data.get('created_by') if problem_data else None
        
        elif target == 'case_owner':
            case_data = context.get_case_data()
            return case_data.get('created_by') if case_data else None
        
        elif target == 'project_manager':
            project_data = context.get_project_data()
            if project_data and project_data.get('project_manager'):
                return project_data['project_manager']
            # Fallback: find any PM
            pm = User.query.filter_by(role='PM').first()
            return pm.id if pm else None
        
        elif target == 'business_analyst':
            case_data = context.get_case_data()
            if case_data and case_data.get('assigned_ba'):
                return case_data['assigned_ba']
            # Fallback: find any BA
            ba = User.query.filter_by(role='BA').first()
            return ba.id if ba else None
        
        elif target == 'department_manager':
            department_id = context.get_department_id()
            if department_id:
                manager = User.query.filter_by(dept_id=department_id, role='Manager').first()
                return manager.id if manager else None
        
        elif target == 'milestone_owner':
            milestone_data = context.get_milestone_data()
            return milestone_data.get('assigned_to') if milestone_data else None
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error resolving target {target}: {e}")
        return None

def _map_template_to_event_type(template: str) -> str:
    """Map workflow template to notification event type"""
    mapping = {
        'problem_high_priority': 'problem_created',
        'problem_to_case_conversion': 'case_created',
        'escalation_alert': 'problem_escalated',
        'milestone_reminder': 'milestone_due_soon',
        'project_update': 'project_status_change',
        'roi_update': 'case_approved'
    }
    return mapping.get(template, 'workflow_notification')

def _build_notification_context(context: WorkflowContext) -> dict:
    """Build notification context from workflow context"""
    notification_context = {
        'workflow_name': context.get_workflow_name(),
        'event_name': context.get_event_name()
    }
    
    # Add relevant entity data
    if context.get_problem_data():
        notification_context['problem'] = context.get_problem_data()
    if context.get_case_data():
        notification_context['case'] = context.get_case_data()
    if context.get_project_data():
        notification_context['project'] = context.get_project_data()
    if context.get_milestone_data():
        notification_context['milestone'] = context.get_milestone_data()
    
    return notification_context

# Action handler registry
ACTION_HANDLERS: Dict[str, Callable] = {
    'send_notification': send_notification,
    'notify_manager': send_notification,  # Alias
    'create_task': create_task,
    'escalate_to_manager': escalate_to_manager,
    'escalate_to_director': escalate_to_manager,  # Alias
    'auto_approve': auto_approve,
    'schedule_follow_up': schedule_follow_up,
    'create_business_case': create_business_case,
    'assign_business_analyst': assign_business_analyst,
    'assign_user': assign_business_analyst,  # Alias
    'log_action': log_workflow_action,
    'notify_stakeholders': send_notification,  # Alias
    'request_status_update': create_task,  # Creates a task for status update
    'notify_manager': send_notification,  # Alias for manager notifications
    'assign_user': assign_business_analyst,  # General user assignment
    'check_overdue_problems': log_workflow_action,  # Placeholder for monitoring actions
    'gather_stakeholder_feedback': create_task,  # Create feedback collection task
    'schedule_review_meeting': schedule_follow_up,  # Schedule meeting follow-up
    'update_case_status': log_workflow_action,  # Log status update action
    'validate_roi_assumptions': create_task,  # Create ROI validation task
    'update_financial_projections': log_workflow_action,  # Log projection update
    'notify_finance_team': send_notification,  # Finance team notification
}