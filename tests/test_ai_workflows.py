"""
Tests for AI Workflow Automation System
Validates real-time workflow actions triggered by ML predictions
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import (
    User, Department, Project, BusinessCase, ProjectMilestone, 
    AIThresholdSettings, Notification, RoleEnum, StatusEnum, 
    PriorityEnum, CaseTypeEnum
)
from analytics.ai_workflows import AIWorkflowEngine

class TestAIWorkflowAutomation:
    """Test suite for AI-driven workflow automation"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        with app.app_context():
            # Create department
            dept = Department(name='AI Test Dept', level=1)
            db.session.add(dept)
            db.session.flush()
            
            # Create users
            admin = User(
                email='admin@ai.test',
                password_hash='test',
                name='AI Admin',
                role=RoleEnum.Admin,
                department_id=dept.id
            )
            pm = User(
                email='pm@ai.test',
                password_hash='test',
                name='Project Manager',
                role=RoleEnum.PM,
                department_id=dept.id
            )
            ba = User(
                email='ba@ai.test',
                password_hash='test',
                name='Business Analyst',
                role=RoleEnum.BA,
                department_id=dept.id
            )
            
            db.session.add_all([admin, pm, ba])
            db.session.flush()
            
            # Create business case
            case = BusinessCase(
                title='AI Test Case',
                description='Test case for AI workflows',
                cost_estimate=50000,
                benefit_estimate=100000,
                case_type=CaseTypeEnum.Reactive,
                department_id=dept.id,
                created_by=admin.id
            )
            case.calculate_roi()
            db.session.add(case)
            db.session.flush()
            
            # Create project
            project = Project(
                name='AI Test Project',
                description='Test project for AI automation',
                start_date=datetime.utcnow().date() - timedelta(days=10),
                planned_end_date=datetime.utcnow().date() + timedelta(days=50),
                status=StatusEnum.InProgress,
                priority=PriorityEnum.High,
                business_case_id=case.id,
                project_manager_id=pm.id,
                department_id=dept.id,
                created_by=admin.id
            )
            db.session.add(project)
            db.session.flush()
            
            # Create milestones
            milestone1 = ProjectMilestone(
                project_id=project.id,
                name='Phase 1',
                description='First phase',
                due_date=datetime.utcnow().date() + timedelta(days=15),
                assigned_to=pm.id,
                completed=False
            )
            milestone2 = ProjectMilestone(
                project_id=project.id,
                name='Phase 2',
                description='Second phase',
                due_date=datetime.utcnow().date() + timedelta(days=30),
                assigned_to=pm.id,
                completed=False
            )
            
            db.session.add_all([milestone1, milestone2])
            db.session.commit()
            
            return {
                'department': dept,
                'admin': admin,
                'pm': pm,
                'ba': ba,
                'case': case,
                'project': project,
                'milestones': [milestone1, milestone2]
            }
    
    def test_ai_threshold_settings_model(self, client):
        """Test AIThresholdSettings model functionality"""
        with app.app_context():
            # Test setting threshold
            setting = AIThresholdSettings.set_threshold(
                'SUCCESS_ALERT_THRESHOLD', 0.6, description='Test threshold'
            )
            
            assert setting.setting_name == 'SUCCESS_ALERT_THRESHOLD'
            assert setting.setting_value == 0.6
            assert setting.description == 'Test threshold'
            
            # Test getting threshold
            value = AIThresholdSettings.get_threshold('SUCCESS_ALERT_THRESHOLD')
            assert value == 0.6
            
            # Test getting non-existent threshold with default
            value = AIThresholdSettings.get_threshold('NON_EXISTENT', 0.5)
            assert value == 0.5
            
            # Test updating existing threshold
            updated = AIThresholdSettings.set_threshold(
                'SUCCESS_ALERT_THRESHOLD', 0.7
            )
            assert updated.setting_value == 0.7
    
    def test_risk_escalation_trigger(self, client, sample_data):
        """Test risk escalation workflow for low success probability"""
        with app.app_context():
            # Set up threshold
            AIThresholdSettings.set_threshold('SUCCESS_ALERT_THRESHOLD', 0.5)
            
            workflow_engine = AIWorkflowEngine()
            project = sample_data['project']
            
            # Test with low success probability (should trigger)
            result = workflow_engine.check_project_risk_escalation(project.id, 0.3)
            assert result == True
            
            # Verify notification was created
            notifications = Notification.query.filter_by(
                user_id=sample_data['pm'].id
            ).all()
            
            assert len(notifications) > 0
            notification = notifications[0]
            assert 'success probability is only 30%' in notification.message
            assert '🚨' in notification.message
            
            # Test with high success probability (should not trigger)
            result = workflow_engine.check_project_risk_escalation(project.id, 0.8)
            assert result == False
    
    def test_milestone_rescheduling_trigger(self, client, sample_data):
        """Test smart milestone rescheduling based on cycle time predictions"""
        with app.app_context():
            # Set up threshold
            AIThresholdSettings.set_threshold('CYCLE_TIME_ALERT_FACTOR', 1.25)
            
            workflow_engine = AIWorkflowEngine()
            project = sample_data['project']
            
            # Calculate current planned duration
            planned_days = (project.planned_end_date - project.start_date).days
            
            # Test with extended cycle time (should trigger rescheduling)
            extended_days = int(planned_days * 1.5)  # 50% over planned
            result = workflow_engine.smart_milestone_reschedule(project.id, extended_days)
            assert result == True
            
            # Verify milestones were rescheduled
            milestones = ProjectMilestone.query.filter_by(
                project_id=project.id,
                completed=False
            ).all()
            
            # Check that project end date was extended
            updated_project = Project.query.get(project.id)
            assert updated_project.planned_end_date > project.planned_end_date
            
            # Verify notification was sent
            notifications = Notification.query.filter_by(
                user_id=sample_data['pm'].id
            ).all()
            
            reschedule_notifications = [
                n for n in notifications 
                if 'rescheduled' in n.message
            ]
            assert len(reschedule_notifications) > 0
            
            # Test with normal cycle time (should not trigger)
            normal_days = int(planned_days * 1.1)  # 10% over planned
            result = workflow_engine.smart_milestone_reschedule(project.id, normal_days)
            assert result == False
    
    def test_anomaly_investigation_trigger(self, client, sample_data):
        """Test anomaly investigation workflow"""
        with app.app_context():
            workflow_engine = AIWorkflowEngine()
            project = sample_data['project']
            
            # Test anomaly investigation trigger
            reasons = ['High complexity', 'Cost variance', 'Extended timeline']
            result = workflow_engine.trigger_anomaly_investigation(
                project.id, 0.8, reasons
            )
            assert result == True
            
            # Verify notifications were sent to PM and BA
            pm_notifications = Notification.query.filter_by(
                user_id=sample_data['pm'].id
            ).all()
            ba_notifications = Notification.query.filter_by(
                user_id=sample_data['ba'].id
            ).all()
            
            # Check PM notification
            investigation_notifications = [
                n for n in pm_notifications 
                if 'flagged for investigation' in n.message
            ]
            assert len(investigation_notifications) > 0
            
            notification = investigation_notifications[0]
            assert 'anomaly score: 0.80' in notification.message
            assert '🔍' in notification.message
            for reason in reasons:
                assert reason in notification.message
    
    def test_comprehensive_project_evaluation(self, client, sample_data):
        """Test comprehensive evaluation of project predictions"""
        with app.app_context():
            # Set up thresholds
            AIThresholdSettings.set_threshold('SUCCESS_ALERT_THRESHOLD', 0.5)
            AIThresholdSettings.set_threshold('CYCLE_TIME_ALERT_FACTOR', 1.25)
            
            workflow_engine = AIWorkflowEngine()
            project = sample_data['project']
            
            # Mock prediction functions to return specific values
            with patch('analytics.ai_workflows.get_project_success_probability') as mock_success:
                with patch('analytics.ai_workflows.get_cycle_time_estimate') as mock_cycle:
                    with patch('analytics.ai_workflows.detect_project_anomaly') as mock_anomaly:
                        
                        # Set up mock returns
                        mock_success.return_value = 0.3  # Low success probability
                        mock_cycle.return_value = 100    # Extended cycle time
                        mock_anomaly.return_value = {
                            'is_anomaly': True,
                            'score': 0.7,
                            'reasons': ['High complexity']
                        }
                        
                        # Execute comprehensive evaluation
                        actions = workflow_engine.evaluate_project_predictions(project.id)
                        
                        # Verify all workflow actions were triggered
                        assert actions['risk_escalation'] == True
                        assert actions['milestone_reschedule'] == True
                        assert actions['anomaly_investigation'] == True
                        
                        # Verify prediction functions were called
                        mock_success.assert_called_once_with(project.id)
                        mock_cycle.assert_called_once_with(project.id)
                        mock_anomaly.assert_called_once_with(project.id)
    
    def test_ai_workflow_with_missing_project(self, client):
        """Test AI workflow behavior with non-existent project"""
        with app.app_context():
            workflow_engine = AIWorkflowEngine()
            
            # Test with non-existent project ID
            result = workflow_engine.check_project_risk_escalation(99999, 0.3)
            assert result == False
            
            result = workflow_engine.smart_milestone_reschedule(99999, 100)
            assert result == False
            
            result = workflow_engine.trigger_anomaly_investigation(99999, 0.8, [])
            assert result == False
    
    def test_threshold_boundary_conditions(self, client, sample_data):
        """Test workflow triggers at threshold boundaries"""
        with app.app_context():
            workflow_engine = AIWorkflowEngine()
            project = sample_data['project']
            
            # Test success probability exactly at threshold
            AIThresholdSettings.set_threshold('SUCCESS_ALERT_THRESHOLD', 0.5)
            
            # Below threshold (should trigger)
            result = workflow_engine.check_project_risk_escalation(project.id, 0.49)
            assert result == True
            
            # At threshold (should trigger)
            result = workflow_engine.check_project_risk_escalation(project.id, 0.5)
            assert result == True
            
            # Above threshold (should not trigger)
            result = workflow_engine.check_project_risk_escalation(project.id, 0.51)
            assert result == False
    
    def test_multiple_stakeholder_notifications(self, client, sample_data):
        """Test that notifications are sent to all relevant stakeholders"""
        with app.app_context():
            AIThresholdSettings.set_threshold('SUCCESS_ALERT_THRESHOLD', 0.5)
            
            workflow_engine = AIWorkflowEngine()
            project = sample_data['project']
            
            # Trigger risk escalation
            result = workflow_engine.check_project_risk_escalation(project.id, 0.3)
            assert result == True
            
            # Check that notifications were sent to multiple stakeholders
            all_notifications = Notification.query.all()
            
            # Should have notifications for PM, case creator, and project creator
            user_ids_notified = {n.user_id for n in all_notifications}
            
            assert sample_data['pm'].id in user_ids_notified  # Project manager
            assert sample_data['admin'].id in user_ids_notified  # Case creator/project creator
    
    def test_workflow_error_handling(self, client, sample_data):
        """Test error handling in workflow automation"""
        with app.app_context():
            workflow_engine = AIWorkflowEngine()
            project = sample_data['project']
            
            # Test with invalid data that could cause errors
            with patch('analytics.ai_workflows.logger') as mock_logger:
                # Test with database session error simulation
                with patch.object(db.session, 'commit', side_effect=Exception('DB Error')):
                    result = workflow_engine.check_project_risk_escalation(project.id, 0.3)
                    
                    # Should handle error gracefully
                    assert result == False
                    
                    # Should log the error
                    mock_logger.error.assert_called()

def run_ai_workflow_tests():
    """Run all AI workflow automation tests"""
    print("Running AI Workflow Automation Tests...")
    
    test_class = TestAIWorkflowAutomation()
    
    with app.app_context():
        db.create_all()
        
        try:
            # Create test client
            app.config['TESTING'] = True
            client = app.test_client()
            
            # Create sample data
            sample_data = test_class.sample_data()
            
            # Run tests
            print("✓ Testing AI threshold settings model...")
            test_class.test_ai_threshold_settings_model(client)
            
            print("✓ Testing risk escalation triggers...")
            test_class.test_risk_escalation_trigger(client, sample_data)
            
            print("✓ Testing milestone rescheduling...")
            test_class.test_milestone_rescheduling_trigger(client, sample_data)
            
            print("✓ Testing anomaly investigation...")
            test_class.test_anomaly_investigation_trigger(client, sample_data)
            
            print("✓ Testing comprehensive evaluation...")
            test_class.test_comprehensive_project_evaluation(client, sample_data)
            
            print("✓ Testing error handling...")
            test_class.test_workflow_error_handling(client, sample_data)
            
            print("✓ Testing boundary conditions...")
            test_class.test_threshold_boundary_conditions(client, sample_data)
            
            print("✓ Testing stakeholder notifications...")
            test_class.test_multiple_stakeholder_notifications(client, sample_data)
            
            print("\n🎯 All AI Workflow Tests Passed!")
            
            # Show current system status
            print("\nAI System Configuration:")
            settings = AIThresholdSettings.query.all()
            for setting in settings:
                print(f"  {setting.setting_name}: {setting.setting_value}")
            
            print(f"\nTotal notifications created: {Notification.query.count()}")
            print(f"Total projects tested: {Project.query.count()}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            db.drop_all()

if __name__ == "__main__":
    run_ai_workflow_tests()