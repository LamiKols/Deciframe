"""
Event Hooks for Notification System
Handles automated notification triggers for business workflow events
"""

from datetime import date, timedelta
from flask import url_for
from extensions import db
from models import (
    BusinessCase, Problem, Project, ProjectMilestone, User, Department,
    NotificationEventEnum, StatusEnum
)
from notifications.service import send_notification


class NotificationEvents:
    """Event hooks for triggering notifications"""
    
    @staticmethod
    def on_business_case_approved(business_case_id, approved_by_user_id=None):
        """
        Trigger when business case is approved
        Notify assigned project manager
        """
        try:
            business_case = BusinessCase.query.get(business_case_id)
            if not business_case:
                print(f"❌ Business case not found: {business_case_id}")
                return False
            
            # Find project manager - could be assigned during approval or default to creator
            project_manager_id = approved_by_user_id or business_case.created_by
            
            # Check if there's an associated project with a different PM
            project = Project.query.filter_by(business_case_id=business_case_id).first()
            if project and project.project_manager_id:
                project_manager_id = project.project_manager_id
            
            context_data = {
                'business_case_code': business_case.code,
                'business_case_title': business_case.title,
                'budget': business_case.cost_estimate,
                'roi': business_case.roi,
                'link': url_for('business.view_business_case', id=business_case_id, _external=True)
            }
            
            return send_notification(
                NotificationEventEnum.BUSINESS_CASE_APPROVED,
                project_manager_id,
                context_data
            )
            
        except Exception as e:
            print(f"❌ Business case approval notification failed: {e}")
            return False
    
    @staticmethod
    def on_problem_created(problem_id):
        """
        Trigger when problem is created
        Notify department manager
        """
        try:
            problem = Problem.query.get(problem_id)
            if not problem:
                print(f"❌ Problem not found: {problem_id}")
                return False
            
            # Find department manager - user with Manager role in same department
            department_manager = User.query.join(Department).filter(
                User.department_id == problem.department_id,
                User.role.in_(['Manager', 'Director'])
            ).first()
            
            if not department_manager:
                print(f"❌ No department manager found for department: {problem.department_id}")
                return False
            
            context_data = {
                'problem_code': problem.code,
                'problem_title': problem.title,
                'problem_description': problem.description[:200] + '...' if len(problem.description) > 200 else problem.description,
                'priority': problem.priority.value,
                'department_name': problem.department.name,
                'reporter_name': problem.creator.name,
                'link': url_for('problems.view_problem', id=problem_id, _external=True)
            }
            
            return send_notification(
                NotificationEventEnum.PROBLEM_CREATED,
                department_manager.id,
                context_data
            )
            
        except Exception as e:
            print(f"❌ Problem creation notification failed: {e}")
            return False
    
    @staticmethod
    def on_milestone_due_soon(milestone_id, days_ahead=1):
        """
        Trigger when milestone is due soon (default 24h ahead)
        Notify milestone owner
        """
        try:
            milestone = ProjectMilestone.query.get(milestone_id)
            if not milestone:
                print(f"❌ Milestone not found: {milestone_id}")
                return False
            
            # Skip if already completed
            if milestone.completed:
                return True
            
            # Check if due date is within the specified days ahead
            days_until_due = (milestone.due_date - date.today()).days
            if days_until_due != days_ahead:
                return True  # Not the right time to send notification
            
            context_data = {
                'milestone_name': milestone.name,
                'milestone_description': milestone.description,
                'project_code': milestone.project.code,
                'project_name': milestone.project.name,
                'due_date': milestone.due_date.strftime('%Y-%m-%d'),
                'link': url_for('projects.view_project', id=milestone.project_id, _external=True)
            }
            
            return send_notification(
                NotificationEventEnum.MILESTONE_DUE_SOON,
                milestone.owner_id,
                context_data
            )
            
        except Exception as e:
            print(f"❌ Milestone due soon notification failed: {e}")
            return False
    
    @staticmethod
    def on_project_created(project_id):
        """
        Trigger when project is created
        Notify assigned project manager
        """
        try:
            project = Project.query.get(project_id)
            if not project:
                print(f"❌ Project not found: {project_id}")
                return False
            
            context_data = {
                'project_code': project.code,
                'project_name': project.name,
                'project_description': project.description[:200] + '...' if project.description and len(project.description) > 200 else project.description or '',
                'budget': project.budget or 0,
                'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else 'TBD',
                'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else 'TBD',
                'link': url_for('projects.view_project', id=project_id, _external=True)
            }
            
            return send_notification(
                NotificationEventEnum.PROJECT_CREATED,
                project.project_manager_id,
                context_data
            )
            
        except Exception as e:
            print(f"❌ Project creation notification failed: {e}")
            return False
    
    @staticmethod
    def check_overdue_milestones():
        """
        Batch job to check for overdue milestones
        Should be run daily via cron or scheduler
        """
        try:
            today = date.today()
            overdue_milestones = ProjectMilestone.query.filter(
                ProjectMilestone.due_date < today,
                ProjectMilestone.completed == False
            ).all()
            
            notifications_sent = 0
            for milestone in overdue_milestones:
                context_data = {
                    'milestone_name': milestone.name,
                    'milestone_description': milestone.description,
                    'project_code': milestone.project.code,
                    'project_name': milestone.project.name,
                    'due_date': milestone.due_date.strftime('%Y-%m-%d'),
                    'days_overdue': (today - milestone.due_date).days,
                    'link': url_for('projects.view_project', id=milestone.project_id, _external=True)
                }
                
                if send_notification(
                    NotificationEventEnum.MILESTONE_OVERDUE,
                    milestone.owner_id,
                    context_data
                ):
                    notifications_sent += 1
            
            print(f"✓ Sent {notifications_sent} overdue milestone notifications")
            return notifications_sent
            
        except Exception as e:
            print(f"❌ Overdue milestone check failed: {e}")
            return 0
    
    @staticmethod
    def check_upcoming_milestones(days_ahead=1):
        """
        Batch job to check for upcoming milestones
        Should be run daily via cron or scheduler
        """
        try:
            target_date = date.today() + timedelta(days=days_ahead)
            upcoming_milestones = ProjectMilestone.query.filter(
                ProjectMilestone.due_date == target_date,
                ProjectMilestone.completed == False
            ).all()
            
            notifications_sent = 0
            for milestone in upcoming_milestones:
                if NotificationEvents.on_milestone_due_soon(milestone.id, days_ahead):
                    notifications_sent += 1
            
            print(f"✓ Sent {notifications_sent} upcoming milestone notifications")
            return notifications_sent
            
        except Exception as e:
            print(f"❌ Upcoming milestone check failed: {e}")
            return 0


# Convenience functions for easy integration
def notify_business_case_approved(business_case_id, approved_by_user_id=None):
    """Convenience function for business case approval notifications"""
    return NotificationEvents.on_business_case_approved(business_case_id, approved_by_user_id)

def notify_problem_created(problem_id):
    """Convenience function for problem creation notifications"""
    return NotificationEvents.on_problem_created(problem_id)

def notify_project_created(project_id):
    """Convenience function for project creation notifications"""
    return NotificationEvents.on_project_created(project_id)

def notify_milestone_due_soon(milestone_id, days_ahead=1):
    """Convenience function for milestone due soon notifications"""
    return NotificationEvents.on_milestone_due_soon(milestone_id, days_ahead)

def run_daily_notification_checks():
    """Run daily batch notification checks"""
    print("🔄 Running daily notification checks...")
    
    # Check for upcoming milestones (due tomorrow)
    upcoming_count = NotificationEvents.check_upcoming_milestones(days_ahead=1)
    
    # Check for overdue milestones
    overdue_count = NotificationEvents.check_overdue_milestones()
    
    print(f"✓ Daily notification checks complete - Upcoming: {upcoming_count}, Overdue: {overdue_count}")
    return {'upcoming': upcoming_count, 'overdue': overdue_count}