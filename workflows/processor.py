"""
Workflow Processor - Execute admin-defined WorkflowTemplates on incoming events
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import text
from models import WorkflowTemplate, db
from workflows.actions import ACTION_HANDLERS
from workflows.context import WorkflowContext

logger = logging.getLogger(__name__)

class WorkflowProcessor:
    """Main workflow execution engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def dispatch_event(self, event_name: str, context: dict) -> List[Dict[str, Any]]:
        """
        Dispatch an event to all active workflow templates that match the trigger
        
        Args:
            event_name: The event that triggered the workflow (e.g., 'problem_created')
            context: Event context containing relevant data (e.g., problem details)
            
        Returns:
            List of execution results for each workflow that was triggered
        """
        self.logger.info(f"🔄 Dispatching event: {event_name}")
        
        # Load active templates matching the trigger
        templates = self._get_matching_templates(event_name)
        
        if not templates:
            self.logger.info(f"📭 No active workflows found for event: {event_name}")
            return []
        
        self.logger.info(f"📋 Found {len(templates)} active workflow(s) for event: {event_name}")
        
        execution_results = []
        
        # Execute each matching template
        for template in templates:
            try:
                result = self._execute_workflow(template, event_name, context)
                execution_results.append(result)
            except Exception as e:
                error_result = {
                    'workflow_id': template.id,
                    'workflow_name': template.name,
                    'status': 'error',
                    'error': str(e),
                    'executed_at': datetime.utcnow().isoformat()
                }
                execution_results.append(error_result)
                self.logger.error(f"❌ Workflow execution failed for {template.name}: {e}")
        
        return execution_results
    
    def _get_matching_templates(self, event_name: str) -> List[WorkflowTemplate]:
        """Find active workflow templates that match the given event trigger"""
        try:
            # Method 1: Try PostgreSQL JSON ? operator for exact array membership
            try:
                templates = WorkflowTemplate.query.filter(
                    WorkflowTemplate.is_active.is_(True),
                    text("definition->'triggers' ? :event_name")
                ).params(event_name=event_name).all()
                
                if templates:
                    return templates
            except Exception:
                pass
            
            # Method 2: Try JSONB @> operator for containment
            try:
                templates = WorkflowTemplate.query.filter(
                    WorkflowTemplate.is_active.is_(True),
                    text("definition->'triggers' @> :event_array")
                ).params(event_array=f'["{event_name}"]').all()
                
                if templates:
                    return templates
            except Exception:
                pass
            
            # Method 3: Try text-based search using CAST
            try:
                templates = WorkflowTemplate.query.filter(
                    WorkflowTemplate.is_active.is_(True),
                    text("CAST(definition->'triggers' AS TEXT) LIKE :pattern")
                ).params(pattern=f'%"{event_name}"%').all()
                
                if templates:
                    return templates
            except Exception:
                pass
            
            # Method 4: SQLAlchemy JSON column text search
            try:
                templates = WorkflowTemplate.query.filter(
                    WorkflowTemplate.is_active.is_(True),
                    WorkflowTemplate.definition['triggers'].astext.contains(f'"{event_name}"')
                ).all()
                
                if templates:
                    return templates
            except Exception:
                pass
            
            # Final fallback: Python filtering
            all_templates = WorkflowTemplate.query.filter(
                WorkflowTemplate.is_active.is_(True)
            ).all()
            
            matching_templates = []
            for template in all_templates:
                triggers = template.definition.get('triggers', [])
                if event_name in triggers:
                    matching_templates.append(template)
            
            return matching_templates
            
        except Exception as e:
            self.logger.error(f"❌ Error querying workflow templates: {e}")
            return []
    
    def _execute_workflow(self, template: WorkflowTemplate, event_name: str, context: dict) -> Dict[str, Any]:
        """Execute a single workflow template"""
        self.logger.info(f"⚡ Executing workflow: {template.name}")
        
        # Create workflow context
        workflow_context = WorkflowContext(
            event_name=event_name,
            workflow_template=template,
            original_context=context
        )
        
        # Track execution
        execution_result = {
            'workflow_id': template.id,
            'workflow_name': template.name,
            'status': 'started',
            'steps_executed': [],
            'started_at': datetime.utcnow().isoformat()
        }
        
        try:
            # Execute each step in the workflow
            steps = template.definition.get('steps', [])
            
            for step_index, step in enumerate(steps):
                step_result = self._execute_step(step, workflow_context, step_index)
                execution_result['steps_executed'].append(step_result)
                
                # If step failed and workflow should stop, break
                if step_result.get('status') == 'error' and step.get('stop_on_error', False):
                    self.logger.warning(f"⚠️ Stopping workflow {template.name} due to step error")
                    break
            
            execution_result['status'] = 'completed'
            execution_result['completed_at'] = datetime.utcnow().isoformat()
            
            self.logger.info(f"✅ Workflow {template.name} completed successfully")
            
        except Exception as e:
            execution_result['status'] = 'error'
            execution_result['error'] = str(e)
            execution_result['failed_at'] = datetime.utcnow().isoformat()
            self.logger.error(f"❌ Workflow {template.name} failed: {e}")
        
        return execution_result
    
    def _execute_step(self, step: dict, context: WorkflowContext, step_index: int) -> Dict[str, Any]:
        """Execute a single workflow step"""
        action = step.get('action')
        step_result = {
            'step_index': step_index,
            'action': action,
            'status': 'started',
            'started_at': datetime.utcnow().isoformat()
        }
        
        try:
            # Check if step conditions are met
            if not self._evaluate_conditions(step, context):
                step_result['status'] = 'skipped'
                step_result['reason'] = 'conditions_not_met'
                self.logger.info(f"⏭️ Skipping step {step_index}: conditions not met")
                return step_result
            
            # Get action handler
            handler = ACTION_HANDLERS.get(action)
            if not handler:
                raise ValueError(f"No handler found for action: {action}")
            
            # Execute the action
            self.logger.info(f"🔧 Executing step {step_index}: {action}")
            handler_result = handler(step, context)
            
            step_result['status'] = 'completed'
            step_result['result'] = handler_result
            step_result['completed_at'] = datetime.utcnow().isoformat()
            
            self.logger.info(f"✅ Step {step_index} completed: {action}")
            
        except Exception as e:
            step_result['status'] = 'error'
            step_result['error'] = str(e)
            step_result['failed_at'] = datetime.utcnow().isoformat()
            self.logger.error(f"❌ Step {step_index} failed: {e}")
        
        return step_result
    
    def _evaluate_conditions(self, step: dict, context: WorkflowContext) -> bool:
        """Evaluate whether step conditions are met"""
        conditions = step.get('conditions', [])
        
        if not conditions:
            return True  # No conditions means always execute
        
        # Simple condition evaluation - can be extended
        for condition in conditions:
            if not self._evaluate_single_condition(condition, context):
                return False
        
        return True
    
    def _evaluate_single_condition(self, condition: str, context: WorkflowContext) -> bool:
        """Evaluate a single condition string"""
        try:
            # Simple condition evaluation for common patterns
            # This can be extended with a proper expression parser
            
            # Handle priority conditions
            if 'priority' in condition.lower():
                if 'problem.priority == "High"' in condition:
                    return context.get_data('problem', {}).get('priority') == 'High'
                elif 'problem.priority == "Medium"' in condition:
                    return context.get_data('problem', {}).get('priority') == 'Medium'
                elif 'problem.priority == "Low"' in condition:
                    return context.get_data('problem', {}).get('priority') == 'Low'
            
            # Handle cost conditions
            if 'estimated_cost' in condition.lower():
                if 'estimated_cost >' in condition:
                    threshold = self._extract_number_from_condition(condition)
                    cost = context.get_data('case', {}).get('estimated_cost', 0)
                    return cost > threshold
                elif 'estimated_cost <' in condition:
                    threshold = self._extract_number_from_condition(condition)
                    cost = context.get_data('case', {}).get('estimated_cost', 0)
                    return cost < threshold
            
            # Handle status conditions
            if 'status ==' in condition:
                status_value = condition.split('status ==')[1].strip().strip('"\'')
                entity_status = context.get_data('problem', {}).get('status') or \
                               context.get_data('case', {}).get('status') or \
                               context.get_data('project', {}).get('status')
                return entity_status == status_value
            
            # Handle impact conditions
            if 'impact ==' in condition:
                impact_value = condition.split('impact ==')[1].strip().strip('"\'')
                impact = context.get_data('problem', {}).get('impact')
                return impact == impact_value
            
            # Handle risk level conditions
            if 'risk_level ==' in condition:
                risk_value = condition.split('risk_level ==')[1].strip().strip('"\'')
                risk_level = context.get_data('case', {}).get('risk_level')
                return risk_level == risk_value
            
            # Default: try to evaluate as simple boolean
            self.logger.warning(f"⚠️ Unsupported condition format: {condition}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error evaluating condition '{condition}': {e}")
            return False
    
    def _extract_number_from_condition(self, condition: str) -> float:
        """Extract numeric value from condition string"""
        import re
        numbers = re.findall(r'\d+\.?\d*', condition)
        return float(numbers[0]) if numbers else 0


# Global processor instance
workflow_processor = WorkflowProcessor()

def dispatch_event(event_name: str, context: dict) -> List[Dict[str, Any]]:
    """
    Public interface for dispatching events to workflow processor
    
    Args:
        event_name: The event that triggered the workflow
        context: Event context containing relevant data
        
    Returns:
        List of execution results
    """
    return workflow_processor.dispatch_event(event_name, context)

def get_active_workflows_for_event(event_name: str) -> List[WorkflowTemplate]:
    """Get list of active workflows that would be triggered by an event"""
    return workflow_processor._get_matching_templates(event_name)