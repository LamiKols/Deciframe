"""
Workflow Context - Provides context and data access for workflow execution
"""

from typing import Any, Optional
from models import WorkflowTemplate

class WorkflowContext:
    """
    Context object passed to workflow action handlers
    Provides access to event data, workflow configuration, and helper methods
    """
    
    def __init__(self, event_name: str, workflow_template: WorkflowTemplate, original_context: dict):
        self.event_name = event_name
        self.workflow_template = workflow_template
        self.original_context = original_context
        self._computed_data = {}
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data from the original context"""
        return self.original_context.get(key, default)
    
    def get_workflow_definition(self) -> dict:
        """Get the workflow template definition"""
        return self.workflow_template.definition
    
    def get_workflow_name(self) -> str:
        """Get the workflow template name"""
        return self.workflow_template.name
    
    def get_event_name(self) -> str:
        """Get the triggering event name"""
        return self.event_name
    
    def set_computed_data(self, key: str, value: Any) -> None:
        """Store computed data for use in subsequent steps"""
        self._computed_data[key] = value
    
    def get_computed_data(self, key: str, default: Any = None) -> Any:
        """Get computed data from previous steps"""
        return self._computed_data.get(key, default)
    
    def get_user_id(self) -> Optional[int]:
        """Get the user ID associated with this event"""
        return self.original_context.get('user_id')
    
    def get_problem_data(self) -> Optional[dict]:
        """Get problem data if available"""
        return self.original_context.get('problem')
    
    def get_case_data(self) -> Optional[dict]:
        """Get business case data if available"""
        return self.original_context.get('case')
    
    def get_project_data(self) -> Optional[dict]:
        """Get project data if available"""
        return self.original_context.get('project')
    
    def get_milestone_data(self) -> Optional[dict]:
        """Get milestone data if available"""
        return self.original_context.get('milestone')
    
    def get_department_id(self) -> Optional[int]:
        """Get department ID from context"""
        # Try to get from various sources
        if 'department_id' in self.original_context:
            return self.original_context['department_id']
        
        # Try to get from user data
        user_data = self.original_context.get('user', {})
        if 'dept_id' in user_data:
            return user_data['dept_id']
        
        # Try to get from problem/case/project data
        for entity in ['problem', 'case', 'project']:
            entity_data = self.original_context.get(entity, {})
            if 'dept_id' in entity_data:
                return entity_data['dept_id']
        
        return None
    
    def to_dict(self) -> dict:
        """Convert context to dictionary for serialization"""
        return {
            'event_name': self.event_name,
            'workflow_id': self.workflow_template.id,
            'workflow_name': self.workflow_template.name,
            'original_context': self.original_context,
            'computed_data': self._computed_data
        }