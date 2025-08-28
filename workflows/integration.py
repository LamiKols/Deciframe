"""
Workflow Integration - Connect workflow events to existing DeciFrame modules
"""

import logging
from workflows import events

logger = logging.getLogger(__name__)

def integrate_with_problems():
    """Add workflow triggers to problem creation and updates"""
    
    # Problem creation integration
    def trigger_problem_workflows(problem):
        """Trigger workflows when a problem is created or updated"""
        try:
            problem_data = {
                'id': problem.id,
                'code': problem.code,
                'title': problem.title,
                'description': problem.description,
                'priority': problem.priority.name if problem.priority else 'Medium',
                'impact': problem.impact,
                'status': problem.status.name if problem.status else 'Open',
                'created_by': problem.created_by,
                'dept_id': problem.dept_id,
                'estimated_cost': getattr(problem, 'estimated_cost', 0)
            }
            
            # Trigger appropriate event based on problem state
            if problem.status and problem.status.name == 'Open':
                results = events.trigger_problem_created(problem_data)
                logger.info(f"📋 Problem {problem.id} triggered {len(results)} workflows")
            
            # Check if problem has been analyzed (has impact assessment)
            if problem.impact and problem.impact in ['Critical', 'High']:
                results = events.trigger_problem_analyzed(problem_data)
                logger.info(f"🔍 Problem {problem.id} analysis triggered {len(results)} workflows")
                
        except Exception as e:
            logger.error(f"❌ Error triggering problem workflows: {e}")
    
    return trigger_problem_workflows

def integrate_with_business_cases():
    """Add workflow triggers to business case lifecycle"""
    
    def trigger_case_workflows(case, event_type='submitted'):
        """Trigger workflows for business case events"""
        try:
            case_data = {
                'id': case.id,
                'code': case.code,
                'title': case.title,
                'summary': case.summary,
                'case_type': case.case_type,
                'status': case.status.name if case.status else 'Draft',
                'priority': case.priority.name if case.priority else 'Medium',
                'estimated_cost': case.estimated_cost or 0,
                'expected_benefit': case.expected_benefit or 0,
                'roi_percentage': case.roi_percentage or 0,
                'created_by': case.created_by,
                'assigned_ba': case.assigned_ba,
                'approved_by': case.approved_by,
                'dept_id': case.dept_id,
                'risk_level': getattr(case, 'risk_level', 'Medium')
            }
            
            # Trigger appropriate workflow based on event type
            if event_type == 'submitted':
                results = events.trigger_case_submitted(case_data)
                logger.info(f"📊 Case {case.id} submission triggered {len(results)} workflows")
            
            elif event_type == 'approved':
                results = events.trigger_case_approved(case_data)
                logger.info(f"✅ Case {case.id} approval triggered {len(results)} workflows")
            
            elif event_type == 'review_due':
                results = events.trigger_case_review_due(case_data)
                logger.info(f"📅 Case {case.id} review triggered {len(results)} workflows")
                
        except Exception as e:
            logger.error(f"❌ Error triggering case workflows: {e}")
    
    return trigger_case_workflows

def integrate_with_projects():
    """Add workflow triggers to project management"""
    
    def trigger_project_workflows(project, event_type='created', old_status=None):
        """Trigger workflows for project events"""
        try:
            project_data = {
                'id': project.id,
                'code': project.code,
                'name': project.name,
                'description': project.description,
                'status': project.status.name if project.status else 'Planning',
                'priority': project.priority.name if project.priority else 'Medium',
                'project_manager': project.project_manager,
                'created_by': project.created_by,
                'dept_id': project.dept_id,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'budget': project.budget or 0
            }
            
            # Trigger appropriate workflow based on event type
            if event_type == 'created':
                results = events.trigger_project_created(project_data)
                logger.info(f"🚀 Project {project.id} creation triggered {len(results)} workflows")
            
            elif event_type == 'status_change':
                new_status = project.status.name if project.status else 'Unknown'
                results = events.trigger_project_status_change(project_data, old_status, new_status)
                logger.info(f"🔄 Project {project.id} status change triggered {len(results)} workflows")
            
            elif event_type == 'completed':
                results = events.trigger_project_completed(project_data)
                logger.info(f"🏁 Project {project.id} completion triggered {len(results)} workflows")
                
        except Exception as e:
            logger.error(f"❌ Error triggering project workflows: {e}")
    
    return trigger_project_workflows

def integrate_with_milestones():
    """Add workflow triggers to milestone management"""
    
    def trigger_milestone_workflows(milestone, project=None, event_type='due_soon'):
        """Trigger workflows for milestone events"""
        try:
            milestone_data = {
                'id': milestone.id,
                'title': milestone.title,
                'description': milestone.description,
                'due_date': milestone.due_date.isoformat() if milestone.due_date else None,
                'status': milestone.status.name if milestone.status else 'Open',
                'assigned_to': milestone.assigned_to,
                'project_id': milestone.project_id,
                'completion_percentage': getattr(milestone, 'completion_percentage', 0)
            }
            
            project_data = None
            if project:
                project_data = {
                    'id': project.id,
                    'code': project.code,
                    'name': project.name,
                    'project_manager': project.project_manager,
                    'dept_id': project.dept_id
                }
            
            # Trigger appropriate workflow based on event type
            if event_type == 'due_soon':
                results = events.trigger_milestone_due_soon(milestone_data, project_data)
                logger.info(f"⏰ Milestone {milestone.id} due soon triggered {len(results)} workflows")
            
            elif event_type == 'overdue':
                results = events.trigger_milestone_overdue(milestone_data, project_data)
                logger.info(f"🚨 Milestone {milestone.id} overdue triggered {len(results)} workflows")
            
            elif event_type == 'completed':
                results = events.trigger_milestone_completed(milestone_data, project_data)
                logger.info(f"✅ Milestone {milestone.id} completion triggered {len(results)} workflows")
                
        except Exception as e:
            logger.error(f"❌ Error triggering milestone workflows: {e}")
    
    return trigger_milestone_workflows

def setup_scheduled_workflows():
    """Setup scheduled workflow triggers"""
    
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        import atexit
        
        scheduler = BackgroundScheduler()
        
        # Daily review at 9 AM
        scheduler.add_job(
            func=events.trigger_daily_review,
            trigger="cron",
            hour=9,
            minute=0,
            id='daily_workflow_review'
        )
        
        # Weekly review on Mondays at 8 AM
        scheduler.add_job(
            func=events.trigger_weekly_review,
            trigger="cron",
            day_of_week='mon',
            hour=8,
            minute=0,
            id='weekly_workflow_review'
        )
        
        # Monthly review on 1st of month at 7 AM
        scheduler.add_job(
            func=events.trigger_monthly_review,
            trigger="cron",
            day=1,
            hour=7,
            minute=0,
            id='monthly_workflow_review'
        )
        
        # Quarterly review on 1st of quarter at 6 AM
        scheduler.add_job(
            func=events.trigger_quarterly_review,
            trigger="cron",
            month='1,4,7,10',
            day=1,
            hour=6,
            minute=0,
            id='quarterly_workflow_review'
        )
        
        # Triage rules execution every 30 minutes
        def run_triage_rules():
            """Execute triage rules periodically"""
            try:
                from app import app
                from services.triage_engine import apply_rules
                
                with app.app_context():
                    applied_count = apply_rules()
                    logger.info(f"🎯 Automated triage rules executed - {applied_count} actions applied")
                    return applied_count
            except Exception as e:
                logger.error(f"❌ Error in automated triage execution: {e}")
                return 0
        
        scheduler.add_job(
            func=run_triage_rules,
            trigger="interval",
            minutes=30,
            id='automated_triage_rules'
        )
        
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())
        
        logger.info("📅 Scheduled workflow triggers initialized")
        
    except Exception as e:
        logger.error(f"❌ Error setting up scheduled workflows: {e}")

def initialize_workflow_integrations():
    """Initialize all workflow integrations"""
    logger.info("🔧 Initializing workflow integrations")
    
    try:
        # Setup scheduled workflows
        setup_scheduled_workflows()
        
        # Return integration functions for use in other modules
        return {
            'problem_trigger': integrate_with_problems(),
            'case_trigger': integrate_with_business_cases(),
            'project_trigger': integrate_with_projects(),
            'milestone_trigger': integrate_with_milestones()
        }
        
    except Exception as e:
        logger.error(f"❌ Error initializing workflow integrations: {e}")
        return {}