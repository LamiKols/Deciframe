"""
AI-Driven Workflow Automation
Triggers real-time actions based on ML predictions
"""

from flask import url_for
from datetime import datetime, timedelta
from app import db
from models import (
    Project, ProjectMilestone, User, AIThresholdSettings,
    NotificationEventEnum
)
from notifications.service import NotificationService
import logging

logger = logging.getLogger(__name__)

class AIWorkflowEngine:
    """Orchestrates AI-driven workflow actions and escalations"""
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def check_project_risk_escalation(self, project_id, success_probability):
        """
        Escalate high-risk projects with notifications and alerts
        """
        try:
            project = Project.query.get(project_id)
            if not project:
                logger.error(f"Project {project_id} not found for risk escalation")
                return False
            
            # Get threshold from settings
            threshold = AIThresholdSettings.get_threshold('SUCCESS_ALERT_THRESHOLD', 0.5)
            
            if success_probability < threshold:
                # Create escalation notification
                message = f"🚨 Project {project.code or project.name} success probability is only {success_probability*100:.0f}%"
                link = url_for('projects.detail', id=project.id, _external=True)
                
                # Notify key stakeholders
                recipients = []
                if project.project_manager_id:
                    recipients.append(project.project_manager_id)
                if project.business_case and project.business_case.created_by:
                    recipients.append(project.business_case.created_by)
                if project.created_by:
                    recipients.append(project.created_by)
                
                # Remove duplicates
                recipients = list(set(recipients))
                
                for user_id in recipients:
                    self.notification_service.create_notification(
                        user_id=user_id,
                        message=message,
                        link=link,
                        event_type=NotificationEventEnum.PROJECT_CREATED  # Reuse existing enum
                    )
                
                logger.info(f"Risk escalation triggered for project {project.code}: {success_probability:.1%} success probability")
                return True
                
        except Exception as e:
            logger.error(f"Error in risk escalation for project {project_id}: {e}")
            return False
        
        return False
    
    def smart_milestone_reschedule(self, project_id, estimated_cycle_days):
        """
        Automatically reschedule milestones based on AI cycle time predictions
        """
        try:
            project = Project.query.get(project_id)
            if not project:
                logger.error(f"Project {project_id} not found for milestone rescheduling")
                return False
            
            # Calculate planned duration
            if project.start_date and project.planned_end_date:
                planned_days = (project.planned_end_date - project.start_date).days
            else:
                logger.warning(f"Project {project.code} missing start/end dates for rescheduling")
                return False
            
            # Get threshold factor from settings
            factor = AIThresholdSettings.get_threshold('CYCLE_TIME_ALERT_FACTOR', 1.25)
            
            if estimated_cycle_days > (planned_days * factor):
                # Calculate delay needed
                delay_days = int(estimated_cycle_days - planned_days)
                
                # Find incomplete milestones to reschedule
                incomplete_milestones = ProjectMilestone.query.filter_by(
                    project_id=project.id,
                    completed=False
                ).filter(
                    ProjectMilestone.due_date >= datetime.utcnow().date()
                ).order_by(ProjectMilestone.due_date).all()
                
                rescheduled_count = 0
                for milestone in incomplete_milestones:
                    # Reschedule milestone
                    old_date = milestone.due_date
                    milestone.due_date = old_date + timedelta(days=delay_days)
                    
                    # Notify milestone owner
                    if milestone.assigned_to:
                        message = f"🔄 Milestone '{milestone.name}' for {project.code or project.name} has been rescheduled from {old_date} to {milestone.due_date}"
                        link = url_for('projects.detail', id=project.id, _external=True)
                        
                        self.notification_service.create_notification(
                            user_id=milestone.assigned_to,
                            message=message,
                            link=link,
                            event_type=NotificationEventEnum.MILESTONE_DUE_SOON
                        )
                    
                    rescheduled_count += 1
                
                if rescheduled_count > 0:
                    # Update project end date
                    project.planned_end_date = project.planned_end_date + timedelta(days=delay_days)
                    db.session.commit()
                    
                    logger.info(f"Rescheduled {rescheduled_count} milestones for project {project.code} (+{delay_days} days)")
                    return True
                
        except Exception as e:
            logger.error(f"Error in milestone rescheduling for project {project_id}: {e}")
            return False
        
        return False
    
    def trigger_anomaly_investigation(self, project_id, anomaly_score, reasons=None):
        """
        Trigger investigation workflow for anomalous projects
        """
        try:
            project = Project.query.get(project_id)
            if not project:
                logger.error(f"Project {project_id} not found for anomaly investigation")
                return False
            
            # Create investigation notification
            reason_text = f" Reasons: {', '.join(reasons)}" if reasons else ""
            message = f"🔍 Project {project.code or project.name} flagged for investigation (anomaly score: {anomaly_score:.2f}).{reason_text}"
            link = url_for('projects.detail', id=project.id, _external=True)
            
            # Notify project manager and business analyst
            recipients = []
            if project.project_manager_id:
                recipients.append(project.project_manager_id)
            
            # Find business analysts in the department
            bas = User.query.filter_by(
                department_id=project.department_id,
                role='Business Analyst'
            ).all()
            for ba in bas:
                recipients.append(ba.id)
            
            # Remove duplicates
            recipients = list(set(recipients))
            
            for user_id in recipients:
                self.notification_service.create_notification(
                    user_id=user_id,
                    message=message,
                    link=link,
                    event_type=NotificationEventEnum.PROJECT_CREATED
                )
            
            logger.info(f"Anomaly investigation triggered for project {project.code}: score {anomaly_score:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error in anomaly investigation for project {project_id}: {e}")
            return False
    
    def evaluate_project_predictions(self, project_id):
        """
        Comprehensive evaluation of project predictions and trigger appropriate actions
        """
        from predict.routes import get_project_success_probability, get_cycle_time_estimate, detect_project_anomaly
        
        actions_taken = {
            'risk_escalation': False,
            'milestone_reschedule': False,
            'anomaly_investigation': False
        }
        
        try:
            # Get success probability
            success_prob = get_project_success_probability(project_id)
            if success_prob is not None:
                actions_taken['risk_escalation'] = self.check_project_risk_escalation(project_id, success_prob)
            
            # Get cycle time estimate
            cycle_time = get_cycle_time_estimate(project_id)
            if cycle_time is not None:
                actions_taken['milestone_reschedule'] = self.smart_milestone_reschedule(project_id, cycle_time)
            
            # Check for anomalies
            anomaly_result = detect_project_anomaly(project_id)
            if anomaly_result and anomaly_result.get('is_anomaly'):
                actions_taken['anomaly_investigation'] = self.trigger_anomaly_investigation(
                    project_id, 
                    anomaly_result.get('score', 0),
                    anomaly_result.get('reasons', [])
                )
            
            logger.info(f"AI workflow evaluation completed for project {project_id}: {actions_taken}")
            
        except Exception as e:
            logger.error(f"Error in project prediction evaluation for {project_id}: {e}")
        
        return actions_taken

# Helper functions for prediction routes
def get_project_success_probability(project_id):
    """Get success probability for a project"""
    from predict.routes import load_model, extract_project_features
    
    try:
        project = Project.query.get(project_id)
        if not project:
            return None
        
        success_model = load_model('success')
        if not success_model:
            return None
        
        features = extract_project_features(project)
        if not features:
            return None
        
        feature_vector = [features.get(f, 0) for f in success_model['features']]
        X_scaled = success_model['scaler'].transform([feature_vector])
        probability = success_model['model'].predict_proba(X_scaled)[0][1]
        
        return float(probability)
        
    except Exception as e:
        logger.error(f"Error getting success probability for project {project_id}: {e}")
        return None

def get_cycle_time_estimate(project_id):
    """Get cycle time estimate for a project"""
    from predict.routes import load_model, extract_project_features
    
    try:
        project = Project.query.get(project_id)
        if not project:
            return None
        
        cycle_model = load_model('cycle_time')
        if not cycle_model:
            return None
        
        features = extract_project_features(project)
        if not features:
            return None
        
        feature_vector = [features.get(f, 0) for f in cycle_model['features']]
        X_scaled = cycle_model['scaler'].transform([feature_vector])
        days = cycle_model['model'].predict(X_scaled)[0]
        
        return max(1, int(days))
        
    except Exception as e:
        logger.error(f"Error getting cycle time estimate for project {project_id}: {e}")
        return None

def detect_project_anomaly(project_id):
    """Detect if project is anomalous"""
    from predict.routes import load_model, extract_project_features
    
    try:
        project = Project.query.get(project_id)
        if not project:
            return None
        
        anomaly_model = load_model('anomaly')
        if not anomaly_model:
            return None
        
        features = extract_project_features(project)
        if not features:
            return None
        
        feature_vector = [features.get(f, 0) for f in anomaly_model['features']]
        X_scaled = anomaly_model['scaler'].transform([feature_vector])
        anomaly_score = anomaly_model['model'].decision_function(X_scaled)[0]
        is_anomaly = anomaly_model['model'].predict(X_scaled)[0] == -1
        
        reasons = []
        if is_anomaly:
            if features.get('cost_variance', 1.0) > 1.5:
                reasons.append("High cost variance")
            if features.get('complexity_score', 0) > 15:
                reasons.append("Very high complexity")
            if features.get('cycle_time', 0) > 120:
                reasons.append("Extended timeline")
        
        return {
            'is_anomaly': is_anomaly,
            'score': float(anomaly_score),
            'reasons': reasons
        }
        
    except Exception as e:
        logger.error(f"Error detecting anomaly for project {project_id}: {e}")
        return None