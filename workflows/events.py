"""
Workflow Event Triggers - Integration points for triggering workflows
"""

import logging
from typing import Dict, Any
from workflows.processor import dispatch_event

logger = logging.getLogger(__name__)

def trigger_problem_created(problem_data: dict, user_data: dict = None) -> list:
    """Trigger workflows when a new problem is created"""
    context = {
        'problem': problem_data,
        'user': user_data,
        'user_id': problem_data.get('created_by'),
        'department_id': problem_data.get('dept_id')
    }
    
    logger.info(f"🔔 Triggering problem_created event for problem {problem_data.get('id')}")
    return dispatch_event('problem_created', context)

def trigger_problem_analyzed(problem_data: dict, analysis_data: dict = None) -> list:
    """Trigger workflows when a problem has been analyzed"""
    context = {
        'problem': problem_data,
        'analysis': analysis_data,
        'user_id': problem_data.get('created_by'),
        'department_id': problem_data.get('dept_id')
    }
    
    logger.info(f"🔔 Triggering problem_analyzed event for problem {problem_data.get('id')}")
    return dispatch_event('problem_analyzed', context)

def trigger_case_submitted(case_data: dict, user_data: dict = None) -> list:
    """Trigger workflows when a business case is submitted"""
    context = {
        'case': case_data,
        'user': user_data,
        'user_id': case_data.get('created_by'),
        'department_id': case_data.get('dept_id')
    }
    
    logger.info(f"🔔 Triggering case_submitted event for case {case_data.get('id')}")
    return dispatch_event('case_submitted', context)

def trigger_case_approved(case_data: dict, approver_data: dict = None) -> list:
    """Trigger workflows when a business case is approved"""
    context = {
        'case': case_data,
        'approver': approver_data,
        'user_id': case_data.get('approved_by'),
        'department_id': case_data.get('dept_id')
    }
    
    logger.info(f"🔔 Triggering case_approved event for case {case_data.get('id')}")
    return dispatch_event('case_approved', context)

def trigger_case_review_due(case_data: dict) -> list:
    """Trigger workflows when a business case review is due"""
    context = {
        'case': case_data,
        'user_id': case_data.get('assigned_ba'),
        'department_id': case_data.get('dept_id')
    }
    
    logger.info(f"🔔 Triggering case_review_due event for case {case_data.get('id')}")
    return dispatch_event('case_review_due', context)

def trigger_project_created(project_data: dict, user_data: dict = None) -> list:
    """Trigger workflows when a new project is created"""
    context = {
        'project': project_data,
        'user': user_data,
        'user_id': project_data.get('created_by'),
        'department_id': project_data.get('dept_id')
    }
    
    logger.info(f"🔔 Triggering project_created event for project {project_data.get('id')}")
    return dispatch_event('project_created', context)

def trigger_project_status_change(project_data: dict, old_status: str, new_status: str) -> list:
    """Trigger workflows when project status changes"""
    context = {
        'project': project_data,
        'old_status': old_status,
        'new_status': new_status,
        'user_id': project_data.get('project_manager'),
        'department_id': project_data.get('dept_id')
    }
    
    logger.info(f"🔔 Triggering project_status_change event for project {project_data.get('id')}")
    return dispatch_event('project_status_change', context)

def trigger_project_completed(project_data: dict) -> list:
    """Trigger workflows when a project is completed"""
    context = {
        'project': project_data,
        'user_id': project_data.get('project_manager'),
        'department_id': project_data.get('dept_id')
    }
    
    logger.info(f"🔔 Triggering project_completed event for project {project_data.get('id')}")
    return dispatch_event('project_completed', context)

def trigger_milestone_due_soon(milestone_data: dict, project_data: dict = None) -> list:
    """Trigger workflows when a milestone is due soon"""
    context = {
        'milestone': milestone_data,
        'project': project_data,
        'user_id': milestone_data.get('assigned_to'),
        'department_id': project_data.get('dept_id') if project_data else None
    }
    
    logger.info(f"🔔 Triggering milestone_due_soon event for milestone {milestone_data.get('id')}")
    return dispatch_event('milestone_due_soon', context)

def trigger_milestone_overdue(milestone_data: dict, project_data: dict = None) -> list:
    """Trigger workflows when a milestone is overdue"""
    context = {
        'milestone': milestone_data,
        'project': project_data,
        'user_id': milestone_data.get('assigned_to'),
        'department_id': project_data.get('dept_id') if project_data else None
    }
    
    logger.info(f"🔔 Triggering milestone_overdue event for milestone {milestone_data.get('id')}")
    return dispatch_event('milestone_overdue', context)

def trigger_milestone_completed(milestone_data: dict, project_data: dict = None) -> list:
    """Trigger workflows when a milestone is completed"""
    context = {
        'milestone': milestone_data,
        'project': project_data,
        'user_id': milestone_data.get('assigned_to'),
        'department_id': project_data.get('dept_id') if project_data else None
    }
    
    logger.info(f"🔔 Triggering milestone_completed event for milestone {milestone_data.get('id')}")
    return dispatch_event('milestone_completed', context)

def trigger_daily_review() -> list:
    """Trigger daily review workflows"""
    context = {
        'review_type': 'daily',
        'trigger_time': 'scheduled'
    }
    
    logger.info("🔔 Triggering daily_review event")
    return dispatch_event('daily_review', context)

def trigger_weekly_review() -> list:
    """Trigger weekly review workflows"""
    context = {
        'review_type': 'weekly',
        'trigger_time': 'scheduled'
    }
    
    logger.info("🔔 Triggering weekly_review event")
    return dispatch_event('weekly_review', context)

def trigger_monthly_review() -> list:
    """Trigger monthly review workflows"""
    context = {
        'review_type': 'monthly',
        'trigger_time': 'scheduled'
    }
    
    logger.info("🔔 Triggering monthly_review event")
    return dispatch_event('monthly_review', context)

def trigger_quarterly_review() -> list:
    """Trigger quarterly review workflows"""
    context = {
        'review_type': 'quarterly',
        'trigger_time': 'scheduled'
    }
    
    logger.info("🔔 Triggering quarterly_review event")
    return dispatch_event('quarterly_review', context)

# HR Events
def trigger_employee_hired(employee_data: dict) -> list:
    """Trigger workflows when a new employee is hired"""
    context = {
        'employee': employee_data,
        'user_id': employee_data.get('id'),
        'department_id': employee_data.get('dept_id')
    }
    
    logger.info(f"🔔 Triggering employee_hired event for employee {employee_data.get('id')}")
    return dispatch_event('employee_hired', context)

def trigger_leave_request_submitted(leave_request_data: dict, employee_data: dict = None) -> list:
    """Trigger workflows when leave request is submitted"""
    context = {
        'leave_request': leave_request_data,
        'employee': employee_data,
        'user_id': leave_request_data.get('employee_id'),
        'department_id': employee_data.get('dept_id') if employee_data else None
    }
    
    logger.info(f"🔔 Triggering leave_request_submitted event")
    return dispatch_event('leave_request_submitted', context)

def trigger_review_period_start(review_period_data: dict) -> list:
    """Trigger workflows when performance review period starts"""
    context = {
        'review_period': review_period_data,
        'trigger_time': 'scheduled'
    }
    
    logger.info("🔔 Triggering review_period_start event")
    return dispatch_event('review_period_start', context)

# IT Events
def trigger_incident_reported(incident_data: dict) -> list:
    """Trigger workflows when IT incident is reported"""
    context = {
        'incident': incident_data,
        'user_id': incident_data.get('reported_by')
    }
    
    logger.info(f"🔔 Triggering incident_reported event for incident {incident_data.get('id')}")
    return dispatch_event('incident_reported', context)

def trigger_change_request_submitted(change_request_data: dict) -> list:
    """Trigger workflows when change request is submitted"""
    context = {
        'change_request': change_request_data,
        'user_id': change_request_data.get('requested_by')
    }
    
    logger.info(f"🔔 Triggering change_request_submitted event")
    return dispatch_event('change_request_submitted', context)

def trigger_maintenance_due(system_data: dict) -> list:
    """Trigger workflows when system maintenance is due"""
    context = {
        'system': system_data,
        'trigger_time': 'scheduled'
    }
    
    logger.info(f"🔔 Triggering maintenance_due event for system {system_data.get('name')}")
    return dispatch_event('maintenance_due', context)

# Finance Events
def trigger_purchase_request_submitted(purchase_request_data: dict) -> list:
    """Trigger workflows when purchase request is submitted"""
    context = {
        'purchase_request': purchase_request_data,
        'user_id': purchase_request_data.get('requested_by'),
        'department_id': purchase_request_data.get('dept_id')
    }
    
    logger.info(f"🔔 Triggering purchase_request_submitted event")
    return dispatch_event('purchase_request_submitted', context)

def trigger_invoice_received(invoice_data: dict) -> list:
    """Trigger workflows when invoice is received"""
    context = {
        'invoice': invoice_data,
        'trigger_time': 'automated'
    }
    
    logger.info(f"🔔 Triggering invoice_received event for invoice {invoice_data.get('id')}")
    return dispatch_event('invoice_received', context)

def trigger_month_end_close() -> list:
    """Trigger workflows for month end close"""
    context = {
        'process': 'month_end_close',
        'trigger_time': 'scheduled'
    }
    
    logger.info("🔔 Triggering month_end_close event")
    return dispatch_event('month_end_close', context)

# Utility function for custom event triggering
def trigger_custom_event(event_name: str, context: dict) -> list:
    """Trigger a custom workflow event with provided context"""
    logger.info(f"🔔 Triggering custom event: {event_name}")
    return dispatch_event(event_name, context)