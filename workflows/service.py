"""
Workflow Service - Public API for workflow operations
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from workflows.processor import dispatch_event
from workflows.actions import _resolve_recipients, _resolve_assignee, _compute_due_date
from workflows.context import WorkflowContext
from models import WorkflowTemplate, User, db

class WorkflowService:
    """Service class for workflow operations"""
    
    @staticmethod
    def resolve_recipients(target: str, context: Dict[str, Any]) -> List[int]:
        """
        Resolve target string to list of user IDs
        
        Args:
            target: Target identifier (e.g., 'department_manager', 'stakeholders')
            context: Workflow context data
            
        Returns:
            List of user IDs
        """
        mock_template = WorkflowTemplate()
        mock_template.id = 0
        mock_template.name = "Service Call"
        mock_template.definition = {"triggers": []}
        
        workflow_context = WorkflowContext(
            event_name="service_call",
            workflow_template=mock_template,
            original_context=context
        )
        
        return _resolve_recipients(target, workflow_context)
    
    @staticmethod
    def resolve_assignee(assignee_role: str, context: Dict[str, Any]) -> Optional[int]:
        """
        Resolve assignee role to specific user ID
        
        Args:
            assignee_role: Role identifier (e.g., 'available_ba', 'department_manager')
            context: Workflow context data
            
        Returns:
            User ID or None if not found
        """
        mock_template = WorkflowTemplate()
        mock_template.id = 0
        mock_template.name = "Service Call"
        mock_template.definition = {"triggers": []}
        
        workflow_context = WorkflowContext(
            event_name="service_call",
            workflow_template=mock_template,
            original_context=context
        )
        
        return _resolve_assignee(assignee_role, workflow_context)
    
    @staticmethod
    def compute_due_date(due_days: Optional[int] = None) -> datetime:
        """
        Compute due date from number of days
        
        Args:
            due_days: Number of days from now (defaults to 7)
            
        Returns:
            Due date as datetime object
        """
        return _compute_due_date(due_days)
    
    @staticmethod
    def trigger_workflow_event(event_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger workflow execution for an event
        
        Args:
            event_name: Name of the event to trigger
            context: Event context data
            
        Returns:
            List of workflow execution results
        """
        return dispatch_event(event_name, context)
    
    @staticmethod
    def get_available_targets() -> List[str]:
        """Get list of available notification targets"""
        return [
            'problem_owner',
            'case_owner',
            'project_manager',
            'business_analyst',
            'department_manager',
            'milestone_owner',
            'stakeholders',
            'all_employees',
            'executives'
        ]
    
    @staticmethod
    def get_available_assignee_roles() -> List[str]:
        """Get list of available assignee roles"""
        return [
            'problem_owner',
            'case_owner',
            'available_ba',
            'department_manager',
            'project_manager',
            'system_admin',
            'ceo'
        ]
    
    @staticmethod
    def get_active_workflows() -> List[WorkflowTemplate]:
        """Get all active workflow templates"""
        return WorkflowTemplate.query.filter_by(is_active=True).all()
    
    @staticmethod
    def create_workflow_task(
        title: str,
        assignee_role: str,
        context: Dict[str, Any],
        description: str = "",
        due_days: int = 7,
        priority: str = "Medium"
    ) -> Dict[str, Any]:
        """
        Create a workflow task with proper assignee resolution
        
        Args:
            title: Task title
            assignee_role: Role to assign task to
            context: Workflow context
            description: Task description
            due_days: Days until due
            priority: Task priority
            
        Returns:
            Task creation result
        """
        from models import Task
        
        # Resolve assignee
        assignee_id = WorkflowService.resolve_assignee(assignee_role, context)
        
        if not assignee_id:
            return {
                'status': 'error',
                'message': f'Could not resolve assignee: {assignee_role}'
            }
        
        # Compute due date
        due_date = WorkflowService.compute_due_date(due_days)
        
        # Create task
        task = Task(
            title=title,
            description=description,
            assigned_to=assignee_id,
            created_by=context.get('user_id', 1),
            status='Open',
            priority=priority,
            due_date=due_date
        )
        
        db.session.add(task)
        db.session.commit()
        
        return {
            'status': 'success',
            'task_id': task.id,
            'assigned_to': assignee_id,
            'due_date': due_date.isoformat(),
            'title': title
        }
    
    @staticmethod
    def send_workflow_notification(
        target: str,
        template: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send notification through workflow system
        
        Args:
            target: Notification target
            template: Notification template
            context: Workflow context
            
        Returns:
            Notification send result
        """
        from notifications.service import NotificationService
        
        # Resolve recipients
        recipients = WorkflowService.resolve_recipients(target, context)
        
        if not recipients:
            return {
                'status': 'error',
                'message': f'Could not resolve recipients for: {target}'
            }
        
        notification_service = NotificationService()
        sent_notifications = []
        
        # Send to all recipients
        for user_id in recipients:
            try:
                result = notification_service.create_notification(
                    user_id=user_id,
                    event_type='workflow_notification',
                    context=context
                )
                
                sent_notifications.append({
                    'user_id': user_id,
                    'notification_id': result.get('notification_id'),
                    'status': 'sent'
                })
                
            except Exception as e:
                sent_notifications.append({
                    'user_id': user_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return {
            'status': 'success',
            'recipients_count': len(recipients),
            'notifications': sent_notifications
        }