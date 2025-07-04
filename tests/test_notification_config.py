"""
Test suite for Notifications & Escalations Configuration module
Verifies CRUD operations, admin access control, and default settings
"""

import pytest
from flask import url_for
from app import app, db
from models import NotificationSetting, FrequencyEnum, User, RoleEnum, Department
import json

@pytest.fixture
def client():
    """Create test client with in-memory database"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

@pytest.fixture
def admin_user(client):
    """Create admin user for testing"""
    with app.app_context():
        # Create department first
        dept = Department(name='Executive', level=1)
        db.session.add(dept)
        db.session.flush()
        
        # Create admin user
        admin = User(
            name='Admin User',
            email='admin@test.com',
            role=RoleEnum.Admin,
            dept_id=dept.id,
            is_active=True
        )
        admin.set_password('password123')
        db.session.add(admin)
        db.session.commit()
        return admin

@pytest.fixture
def regular_user(client):
    """Create regular user for testing access control"""
    with app.app_context():
        dept = Department.query.first() or Department(name='Engineering', level=1)
        if not Department.query.first():
            db.session.add(dept)
            db.session.flush()
        
        user = User(
            name='Regular User',
            email='user@test.com',
            role=RoleEnum.Staff,
            dept_id=dept.id,
            is_active=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

def login_user(client, email, password):
    """Helper function to login user"""
    return client.post('/auth/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)

class TestNotificationConfigRoutes:
    """Test notification configuration routes and functionality"""
    
    def test_notification_settings_list_admin_access(self, client, admin_user):
        """Test that admin can access notification settings list"""
        login_user(client, admin_user.email, 'password123')
        
        response = client.get('/admin/notifications/')
        assert response.status_code == 200
        assert b'Notifications & Escalations Configuration' in response.data
        assert b'Event Configuration' in response.data
    
    def test_notification_settings_regular_user_denied(self, client, regular_user):
        """Test that regular users cannot access notification settings"""
        login_user(client, regular_user.email, 'password123')
        
        response = client.get('/admin/notifications/')
        assert response.status_code == 302  # Redirect to access denied
    
    def test_default_settings_creation(self, client, admin_user):
        """Test that default notification settings are created automatically"""
        login_user(client, admin_user.email, 'password123')
        
        # Access the settings page to trigger default creation
        response = client.get('/admin/notifications/')
        assert response.status_code == 200
        
        # Check that default settings were created
        with app.app_context():
            settings_count = NotificationSetting.query.count()
            assert settings_count > 0
            
            # Check specific default events
            problem_created = NotificationSetting.query.filter_by(event_name='problem_created').first()
            assert problem_created is not None
            assert problem_created.frequency == FrequencyEnum.immediate
            assert problem_created.channel_email == True
            assert problem_created.channel_in_app == True
    
    def test_create_notification_setting(self, client, admin_user):
        """Test creating new notification setting"""
        login_user(client, admin_user.email, 'password123')
        
        # Test GET request for create form
        response = client.get('/admin/notifications/create')
        assert response.status_code == 200
        assert b'Create Notification Setting' in response.data
        
        # Test POST request to create setting
        response = client.post('/admin/notifications/create', data={
            'event_name': 'test_event',
            'frequency': 'daily',
            'threshold_hours': '24',
            'channel_email': 'on',
            'channel_in_app': 'on',
            'channel_push': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'created successfully' in response.data
        
        # Verify setting was created in database
        with app.app_context():
            setting = NotificationSetting.query.filter_by(event_name='test_event').first()
            assert setting is not None
            assert setting.frequency == FrequencyEnum.daily
            assert setting.threshold_hours == 24
            assert setting.channel_email == True
            assert setting.channel_in_app == True
            assert setting.channel_push == False
    
    def test_edit_notification_setting(self, client, admin_user):
        """Test editing existing notification setting"""
        login_user(client, admin_user.email, 'password123')
        
        # Create a setting first
        with app.app_context():
            setting = NotificationSetting(
                event_name='edit_test_event',
                frequency=FrequencyEnum.immediate,
                threshold_hours=None,
                channel_email=True,
                channel_in_app=True,
                channel_push=False
            )
            db.session.add(setting)
            db.session.commit()
            setting_id = setting.id
        
        # Test GET request for edit form
        response = client.get(f'/admin/notifications/edit/{setting_id}')
        assert response.status_code == 200
        assert b'Edit Notification Setting' in response.data
        
        # Test POST request to update setting
        response = client.post(f'/admin/notifications/edit/{setting_id}', data={
            'frequency': 'weekly',
            'threshold_hours': '48',
            'channel_email': 'on',
            'channel_in_app': '',
            'channel_push': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'updated successfully' in response.data
        
        # Verify setting was updated in database
        with app.app_context():
            updated_setting = NotificationSetting.query.get(setting_id)
            assert updated_setting.frequency == FrequencyEnum.weekly
            assert updated_setting.threshold_hours == 48
            assert updated_setting.channel_email == True
            assert updated_setting.channel_in_app == False
            assert updated_setting.channel_push == True
    
    def test_delete_notification_setting(self, client, admin_user):
        """Test deleting notification setting"""
        login_user(client, admin_user.email, 'password123')
        
        # Create a setting first
        with app.app_context():
            setting = NotificationSetting(
                event_name='delete_test_event',
                frequency=FrequencyEnum.immediate,
                channel_email=True,
                channel_in_app=True,
                channel_push=False
            )
            db.session.add(setting)
            db.session.commit()
            setting_id = setting.id
        
        # Test DELETE request
        response = client.post(f'/admin/notifications/delete/{setting_id}', follow_redirects=True)
        assert response.status_code == 200
        assert b'deleted successfully' in response.data
        
        # Verify setting was deleted from database
        with app.app_context():
            deleted_setting = NotificationSetting.query.get(setting_id)
            assert deleted_setting is None
    
    def test_reset_defaults(self, client, admin_user):
        """Test resetting all settings to defaults"""
        login_user(client, admin_user.email, 'password123')
        
        # Create some custom settings first
        with app.app_context():
            custom_setting = NotificationSetting(
                event_name='custom_event',
                frequency=FrequencyEnum.weekly,
                channel_email=False,
                channel_in_app=True,
                channel_push=True
            )
            db.session.add(custom_setting)
            db.session.commit()
        
        # Test reset defaults
        response = client.post('/admin/notifications/reset-defaults', follow_redirects=True)
        assert response.status_code == 200
        assert b'reset to defaults' in response.data
        
        # Verify custom setting was removed and defaults were created
        with app.app_context():
            custom_setting = NotificationSetting.query.filter_by(event_name='custom_event').first()
            assert custom_setting is None
            
            # Check that default settings exist
            problem_created = NotificationSetting.query.filter_by(event_name='problem_created').first()
            assert problem_created is not None
            assert problem_created.frequency == FrequencyEnum.immediate
    
    def test_escalation_test_api(self, client, admin_user):
        """Test escalation testing API endpoint"""
        login_user(client, admin_user.email, 'password123')
        
        # Create a setting first
        with app.app_context():
            setting = NotificationSetting(
                event_name='api_test_event',
                frequency=FrequencyEnum.daily,
                threshold_hours=24,
                channel_email=True,
                channel_in_app=True,
                channel_push=False
            )
            db.session.add(setting)
            db.session.commit()
            setting_id = setting.id
        
        # Test API endpoint
        response = client.post(f'/admin/notifications/api/test-escalation/{setting_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['test_status'] == 'success'
        assert data['event_name'] == 'api_test_event'
        assert data['frequency'] == 'daily'
        assert data['threshold_hours'] == 24
        assert data['channels']['email'] == True
        assert data['channels']['in_app'] == True
        assert data['channels']['push'] == False
    
    def test_duplicate_event_name_prevention(self, client, admin_user):
        """Test that duplicate event names are prevented"""
        login_user(client, admin_user.email, 'password123')
        
        # Create first setting
        with app.app_context():
            setting1 = NotificationSetting(
                event_name='duplicate_test',
                frequency=FrequencyEnum.immediate,
                channel_email=True,
                channel_in_app=True,
                channel_push=False
            )
            db.session.add(setting1)
            db.session.commit()
        
        # Try to create duplicate
        response = client.post('/admin/notifications/create', data={
            'event_name': 'duplicate_test',
            'frequency': 'daily',
            'channel_email': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'already exists' in response.data
    
    def test_frequency_enum_validation(self, client, admin_user):
        """Test that frequency enum values are properly validated"""
        login_user(client, admin_user.email, 'password123')
        
        # Test with valid frequency
        response = client.post('/admin/notifications/create', data={
            'event_name': 'frequency_test',
            'frequency': 'hourly',
            'channel_email': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'created successfully' in response.data
        
        # Verify frequency was set correctly
        with app.app_context():
            setting = NotificationSetting.query.filter_by(event_name='frequency_test').first()
            assert setting.frequency == FrequencyEnum.hourly

class TestNotificationConfigModel:
    """Test NotificationSetting model functionality"""
    
    def test_model_creation(self, client):
        """Test creating NotificationSetting model instances"""
        with app.app_context():
            setting = NotificationSetting(
                event_name='model_test',
                frequency=FrequencyEnum.daily,
                threshold_hours=48,
                channel_email=True,
                channel_in_app=False,
                channel_push=True
            )
            db.session.add(setting)
            db.session.commit()
            
            # Verify model was created correctly
            retrieved = NotificationSetting.query.filter_by(event_name='model_test').first()
            assert retrieved is not None
            assert retrieved.frequency == FrequencyEnum.daily
            assert retrieved.threshold_hours == 48
            assert retrieved.channel_email == True
            assert retrieved.channel_in_app == False
            assert retrieved.channel_push == True
            assert retrieved.updated_at is not None
    
    def test_model_repr(self, client):
        """Test model string representation"""
        with app.app_context():
            setting = NotificationSetting(
                event_name='repr_test',
                frequency=FrequencyEnum.weekly
            )
            assert 'repr_test' in str(setting)
            assert 'weekly' in str(setting)
    
    def test_frequency_enum_values(self, client):
        """Test all FrequencyEnum values"""
        with app.app_context():
            frequencies = [
                FrequencyEnum.immediate,
                FrequencyEnum.hourly,
                FrequencyEnum.daily,
                FrequencyEnum.weekly
            ]
            
            for i, freq in enumerate(frequencies):
                setting = NotificationSetting(
                    event_name=f'freq_test_{i}',
                    frequency=freq,
                    channel_email=True,
                    channel_in_app=True
                )
                db.session.add(setting)
            
            db.session.commit()
            
            # Verify all frequencies were saved correctly
            for i, freq in enumerate(frequencies):
                retrieved = NotificationSetting.query.filter_by(event_name=f'freq_test_{i}').first()
                assert retrieved.frequency == freq

if __name__ == '__main__':
    pytest.main([__file__])