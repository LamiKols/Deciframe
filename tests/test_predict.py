"""
Test suite for DeciFrame Predictive Analytics ML Pipeline
Tests model training, API endpoints, and prediction accuracy
"""

import os
import sys
import json
import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, Department, Project, BusinessCase, ProjectMilestone, PredictionFeedback
from models import RoleEnum, StatusEnum, PriorityEnum, CaseTypeEnum
from analytics.train_models import MLModelTrainer
from analytics.scheduler import MLScheduler


class TestMLModelTraining:
    """Test ML model training pipeline"""
    
    @pytest.fixture
    def setup_test_data(self):
        """Create test data for ML training"""
        with app.app_context():
            # Create department
            dept = Department(name="Test Engineering", level=1)
            db.session.add(dept)
            db.session.flush()
            
            # Create users
            admin = User(
                email="admin@test.com",
                password_hash="test_hash",
                name="Admin User",
                role=RoleEnum.Admin,
                department_id=dept.id
            )
            pm = User(
                email="pm@test.com", 
                password_hash="test_hash",
                name="Project Manager",
                role=RoleEnum.PM,
                department_id=dept.id
            )
            db.session.add_all([admin, pm])
            db.session.flush()
            
            # Create business cases and projects
            projects = []
            for i in range(15):  # Need sufficient data for training
                case = BusinessCase(
                    title=f"Test Case {i}",
                    description=f"Test business case {i}",
                    cost_estimate=10000 + (i * 5000),
                    benefit_estimate=15000 + (i * 7000),
                    case_type=CaseTypeEnum.Reactive,
                    department_id=dept.id,
                    created_by=admin.id
                )
                case.actual_cost = case.cost_estimate * (0.8 + (i % 3) * 0.2)  # Vary actual costs
                case.approval_date = datetime.utcnow().date() - timedelta(days=30+i)
                db.session.add(case)
                db.session.flush()
                
                project = Project(
                    name=f"Test Project {i}",
                    description=f"Test project {i}",
                    start_date=case.approval_date + timedelta(days=7),
                    end_date=case.approval_date + timedelta(days=60),
                    planned_end_date=case.approval_date + timedelta(days=55),
                    status=StatusEnum.Completed if i < 10 else StatusEnum.InProgress,
                    priority=PriorityEnum.High if i % 3 == 0 else PriorityEnum.Medium,
                    business_case_id=case.id,
                    project_manager_id=pm.id,
                    department_id=dept.id,
                    created_by=admin.id
                )
                db.session.add(project)
                db.session.flush()
                
                # Add milestones
                for j in range(3):
                    milestone = ProjectMilestone(
                        project_id=project.id,
                        name=f"Milestone {j+1}",
                        description=f"Test milestone {j+1}",
                        due_date=project.start_date + timedelta(days=(j+1)*15),
                        assigned_to=pm.id,
                        completed=j < 2 or project.status == StatusEnum.Completed
                    )
                    if milestone.completed:
                        milestone.completion_date = milestone.due_date - timedelta(days=1)
                    db.session.add(milestone)
                
                projects.append(project)
            
            db.session.commit()
            return {
                'department': dept,
                'admin': admin,
                'pm': pm,
                'projects': projects
            }
    
    def test_ml_trainer_initialization(self):
        """Test MLModelTrainer initialization"""
        trainer = MLModelTrainer()
        assert trainer.models_dir is not None
        assert os.path.exists(trainer.models_dir)
    
    def test_feature_extraction(self, setup_test_data):
        """Test feature extraction from project data"""
        trainer = MLModelTrainer()
        df = trainer.extract_project_features()
        
        assert not df.empty
        assert len(df) >= 10  # Should have extracted sufficient data
        
        # Check required columns
        required_cols = ['cost_estimate', 'priority', 'complexity_score', 
                        'team_size', 'milestone_count', 'success_probability']
        for col in required_cols:
            assert col in df.columns
        
        # Verify data types and ranges
        assert df['priority'].min() >= 1
        assert df['priority'].max() <= 3
        assert df['success_probability'].min() >= 0
        assert df['success_probability'].max() <= 1
    
    def test_model_training(self, setup_test_data):
        """Test complete model training pipeline"""
        trainer = MLModelTrainer()
        
        # Train all models
        success = trainer.train_all_models()
        assert success
        
        # Verify model files exist
        model_files = [
            'success_model.pkl', 'success_scaler.pkl', 'success_features.pkl',
            'cycle_time_model.pkl', 'cycle_time_scaler.pkl', 'cycle_time_features.pkl',
            'anomaly_model.pkl', 'anomaly_scaler.pkl', 'anomaly_features.pkl',
            'training_metadata.pkl'
        ]
        
        for filename in model_files:
            filepath = os.path.join(trainer.models_dir, filename)
            assert os.path.exists(filepath), f"Model file {filename} not found"
    
    def test_training_with_insufficient_data(self):
        """Test model training with insufficient data"""
        # Clear all data
        with app.app_context():
            db.session.query(ProjectMilestone).delete()
            db.session.query(Project).delete()
            db.session.query(BusinessCase).delete()
            db.session.commit()
        
        trainer = MLModelTrainer()
        df = trainer.extract_project_features()
        
        if df.empty:
            success = trainer.train_all_models()
            assert not success  # Should fail with no data
        else:
            # Even with minimal data, should handle gracefully
            success = trainer.train_all_models()
            # Result depends on data availability


class TestPredictiveAPI:
    """Test predictive analytics API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers"""
        with app.app_context():
            # Create test user
            user = User(
                email="test@predict.com",
                password_hash="test_hash",
                name="Test User",
                role=RoleEnum.Admin
            )
            db.session.add(user)
            db.session.commit()
            
            # Mock JWT authentication
            return {'Authorization': 'Bearer test_token'}
    
    @patch('predict.routes.current_user')
    def test_project_success_prediction(self, mock_user, client, auth_headers, setup_test_data):
        """Test project success prediction endpoint"""
        mock_user.is_authenticated = True
        mock_user.id = 1
        
        data = setup_test_data
        project = data['projects'][0]
        
        # Mock model loading
        with patch('predict.routes.load_model') as mock_load:
            mock_model_data = {
                'model': MagicMock(),
                'scaler': MagicMock(),
                'features': ['cost_estimate', 'priority', 'complexity_score', 'team_size']
            }
            mock_load.return_value = mock_model_data
            mock_model_data['model'].predict_proba.return_value = [[0.3, 0.7]]
            mock_model_data['scaler'].transform.return_value = [[1, 2, 3, 4]]
            
            response = client.get(
                f'/api/predict/project-success?project_id={project.id}',
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'probability' in data
            assert 'confidence' in data
            assert 'factors' in data
            assert 0 <= data['probability'] <= 1
    
    @patch('predict.routes.current_user')
    def test_cycle_time_prediction(self, mock_user, client, auth_headers, setup_test_data):
        """Test cycle time prediction endpoint"""
        mock_user.is_authenticated = True
        mock_user.id = 1
        
        data = setup_test_data
        project = data['projects'][0]
        
        with patch('predict.routes.load_model') as mock_load:
            mock_model_data = {
                'model': MagicMock(),
                'scaler': MagicMock(),
                'features': ['cost_estimate', 'priority', 'complexity_score']
            }
            mock_load.return_value = mock_model_data
            mock_model_data['model'].predict.return_value = [42]
            mock_model_data['scaler'].transform.return_value = [[1, 2, 3]]
            
            response = client.get(
                f'/api/predict/cycle-time?project_id={project.id}',
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'estimated_days' in data
            assert 'estimated_weeks' in data
            assert data['estimated_days'] > 0
    
    @patch('predict.routes.current_user')
    def test_anomaly_detection(self, mock_user, client, auth_headers, setup_test_data):
        """Test anomaly detection endpoint"""
        mock_user.is_authenticated = True
        mock_user.id = 1
        
        with patch('predict.routes.load_model') as mock_load:
            mock_model_data = {
                'model': MagicMock(),
                'scaler': MagicMock(),
                'features': ['cost_estimate', 'actual_cost', 'priority']
            }
            mock_load.return_value = mock_model_data
            mock_model_data['model'].predict.return_value = [1, -1, 1]  # One anomaly
            mock_model_data['model'].decision_function.return_value = [0.5, -0.8, 0.3]
            mock_model_data['scaler'].transform.return_value = [[1, 2, 3]]
            
            response = client.get(
                '/api/predict/anomalies?module=project',
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'anomalies' in data
            assert 'total_analyzed' in data
            assert 'anomaly_count' in data
    
    @patch('predict.routes.current_user')
    def test_feedback_submission(self, mock_user, client, auth_headers):
        """Test prediction feedback submission"""
        mock_user.is_authenticated = True
        mock_user.id = 1
        
        feedback_data = {
            'type': 'project-success',
            'id': 1,
            'actual': 0.8
        }
        
        response = client.post(
            '/api/predict/feedback',
            data=json.dumps(feedback_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'feedback_id' in data
        
        # Verify feedback stored in database
        with app.app_context():
            feedback = PredictionFeedback.query.filter_by(
                prediction_type='project-success',
                entity_id=1
            ).first()
            assert feedback is not None
            assert feedback.actual_value == 0.8
    
    @patch('predict.routes.current_user')
    def test_model_stats(self, mock_user, client, auth_headers):
        """Test model statistics endpoint"""
        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_user.role = RoleEnum.Admin
        
        response = client.get(
            '/api/predict/model-stats',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'models_available' in data
        assert 'feedback_counts' in data
        assert 'recent_predictions' in data
    
    def test_authentication_required(self, client):
        """Test that endpoints require authentication"""
        endpoints = [
            '/api/predict/project-success?project_id=1',
            '/api/predict/cycle-time?project_id=1',
            '/api/predict/anomalies',
            '/api/predict/model-stats'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [401, 302]  # Unauthorized or redirect to login


class TestMLScheduler:
    """Test ML training scheduler"""
    
    def test_scheduler_initialization(self):
        """Test scheduler initialization"""
        scheduler = MLScheduler()
        assert scheduler.scheduler is not None
        assert not scheduler.running
    
    def test_scheduler_start_stop(self):
        """Test scheduler start and stop"""
        scheduler = MLScheduler()
        
        # Start scheduler
        scheduler.start()
        assert scheduler.running
        
        # Stop scheduler
        scheduler.stop()
        assert not scheduler.running
    
    def test_manual_retrain(self, setup_test_data):
        """Test manual model retraining"""
        scheduler = MLScheduler()
        
        # Mock successful training
        with patch.object(scheduler.trainer, 'train_all_models', return_value=True):
            result = scheduler.manual_retrain()
            assert result['success'] is True
            assert 'message' in result
    
    def test_backup_and_restore(self):
        """Test model backup and restore functionality"""
        scheduler = MLScheduler()
        
        # Create dummy model files
        test_files = ['success_model.pkl', 'cycle_time_model.pkl']
        for filename in test_files:
            filepath = os.path.join(scheduler.trainer.models_dir, filename)
            with open(filepath, 'w') as f:
                f.write('dummy model data')
        
        # Test backup
        scheduler._backup_existing_models()
        
        # Verify backup exists
        backup_dir = os.path.join(scheduler.trainer.models_dir, 'backups')
        assert os.path.exists(backup_dir)
        
        # Clean up
        shutil.rmtree(backup_dir, ignore_errors=True)
    
    def test_scheduler_status(self):
        """Test scheduler status reporting"""
        scheduler = MLScheduler()
        status = scheduler.get_status()
        
        assert 'running' in status
        assert 'jobs' in status
        assert 'models_directory' in status


class TestPredictionAccuracy:
    """Test prediction accuracy and model validation"""
    
    def test_feature_consistency(self, setup_test_data):
        """Test that feature extraction is consistent"""
        trainer = MLModelTrainer()
        
        # Extract features twice
        df1 = trainer.extract_project_features()
        df2 = trainer.extract_project_features()
        
        # Should get same results
        assert len(df1) == len(df2)
        if not df1.empty:
            assert df1.equals(df2)
    
    def test_prediction_bounds(self, setup_test_data):
        """Test that predictions stay within reasonable bounds"""
        trainer = MLModelTrainer()
        df = trainer.extract_project_features()
        
        if not df.empty:
            # Success probability should be [0, 1]
            assert df['success_probability'].min() >= 0
            assert df['success_probability'].max() <= 1
            
            # Cycle time should be positive
            assert df['cycle_time'].min() >= 0
            
            # Cost variance should be positive
            assert df['cost_variance'].min() > 0
    
    def test_complexity_calculation(self, setup_test_data):
        """Test project complexity calculation logic"""
        from predict.routes import extract_project_features
        
        data = setup_test_data
        project = data['projects'][0]
        
        with app.app_context():
            features = extract_project_features(project)
            assert features is not None
            assert 'complexity_score' in features
            assert features['complexity_score'] >= 0
            assert features['complexity_score'] <= 20  # Max complexity cap


def run_comprehensive_tests():
    """Run all predictive analytics tests"""
    import subprocess
    
    print("🧪 Running ML prediction tests...")
    result = subprocess.run(['python', '-m', 'pytest', 'tests/test_predict.py', '-v'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ All prediction tests passed")
        return True
    else:
        print("❌ Some prediction tests failed")
        print(result.stdout)
        print(result.stderr)
        return False


if __name__ == "__main__":
    run_comprehensive_tests()