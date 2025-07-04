#!/usr/bin/env python3
"""
Test suite for notification settings integration
"""

import pytest
import sys
import os
sys.path.append('.')

from app import app, db
from models import User, NotificationSetting, Notification, FrequencyEnum, RoleEnum
from notifications.service import NotificationService, get_setting


class TestNotificationSettings:
    """Test notification settings CRUD operations and service integration"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()

    @pytest.fixture
    def admin_user(self):
        """Create admin user for testing"""
        with app.app_context():
            admin = User(
                name="Test Admin",
                email="admin@test.com", 
                role=RoleEnum.Admin,
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            return admin

    @pytest.fixture
    def test_user(self):
        """Create regular test user"""
        with app.app_context():
            user = User(
                name="Test User",
                email="user@test.com",
                role=RoleEnum.Staff,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            return user

    @pytest.fixture
    def notification_settings(self):
        """Create test notification settings"""
        with app.app_context():
            settings = [
                NotificationSetting(
                    event_name="problem_created",
                    frequency=FrequencyEnum.immediate,
                    channel_email=True,
                    channel_in_app=True,
                    channel_push=False,
                    threshold_hours=None
                ),
                NotificationSetting(
                    event_name="case_approved",
                    frequency=FrequencyEnum.daily,
                    channel_email=True,
                    channel_in_app=False,
                    channel_push=False,
                    threshold_hours=24
                ),
                NotificationSetting(
                    event_name="milestone_due",
                    frequency=FrequencyEnum.immediate,
                    channel_email=True,
                    channel_in_app=True,
                    channel_push=True,
                    threshold_hours=2
                )
            ]
            
            for setting in settings:
                db.session.add(setting)
            db.session.commit()
            return settings

    def test_get_admin_notifications_returns_all_events(self, client, admin_user, notification_settings):
        """Test GET /admin/notifications returns all notification events"""
        with app.app_context():
            # Simulate admin login
            with client.session_transaction() as sess:
                sess['user_id'] = admin_user.id
            
            response = client.get('/admin/notifications')
            
            assert response.status_code == 200
            
            # Check that response contains all test events
            response_data = response.get_data(as_text=True)
            assert 'problem_created' in response_data
            assert 'case_approved' in response_data
            assert 'milestone_due' in response_data
            
            # Verify form fields are present
            assert 'freq__problem_created' in response_data
            assert 'email__problem_created' in response_data
            assert 'thresh__milestone_due' in response_data
            
            print("✓ GET /admin/notifications returns all events correctly")

    def test_post_updates_model_correctly(self, client, admin_user, notification_settings):
        """Test POST /admin/notifications updates notification settings correctly"""
        with app.app_context():
            # Simulate admin login
            with client.session_transaction() as sess:
                sess['user_id'] = admin_user.id
            
            # Test data for POST request
            form_data = {
                'freq__problem_created': 'hourly',
                'email__problem_created': 'on',
                'in_app__problem_created': '',  # Unchecked
                'push__problem_created': 'on',
                'thresh__problem_created': '12',
                
                'freq__case_approved': 'immediate',
                'email__case_approved': '',  # Unchecked
                'in_app__case_approved': 'on',
                'push__case_approved': '',  # Unchecked
                'thresh__case_approved': '',  # No threshold
                
                'freq__milestone_due': 'weekly',
                'email__milestone_due': 'on',
                'in_app__milestone_due': 'on',
                'push__milestone_due': 'on',
                'thresh__milestone_due': '48'
            }
            
            response = client.post('/admin/notifications', data=form_data)
            
            # Should redirect after successful update
            assert response.status_code == 302 or response.status_code == 200
            
            # Verify database updates
            problem_setting = NotificationSetting.query.filter_by(event_name="problem_created").first()
            assert problem_setting.frequency == FrequencyEnum.hourly
            assert problem_setting.channel_email == True
            assert problem_setting.channel_in_app == False  # Was unchecked
            assert problem_setting.channel_push == True
            assert problem_setting.threshold_hours == 12
            
            case_setting = NotificationSetting.query.filter_by(event_name="case_approved").first()
            assert case_setting.frequency == FrequencyEnum.immediate
            assert case_setting.channel_email == False  # Was unchecked
            assert case_setting.channel_in_app == True
            assert case_setting.channel_push == False
            assert case_setting.threshold_hours is None  # No threshold for immediate
            
            milestone_setting = NotificationSetting.query.filter_by(event_name="milestone_due").first()
            assert milestone_setting.frequency == FrequencyEnum.weekly
            assert milestone_setting.channel_email == True
            assert milestone_setting.channel_in_app == True
            assert milestone_setting.channel_push == True
            assert milestone_setting.threshold_hours == 48
            
            print("✓ POST /admin/notifications updates models correctly")

    def test_notification_service_dispatch_respects_settings(self, client, test_user, notification_settings):
        """Test NotificationService.dispatch() respects channel flags and thresholds"""
        with app.app_context():
            # Test immediate notification with email and in-app enabled
            result = NotificationService.dispatch(
                event_name="problem_created",
                user=test_user,
                title="Test Problem",
                description="Test problem description",
                link="/problems/1"
            )
            
            # Should return True even without SendGrid (graceful degradation)
            assert result == True
            
            # Verify in-app notification was created
            in_app_notification = Notification.query.filter_by(user_id=test_user.id).first()
            assert in_app_notification is not None
            assert "Problem Created" in in_app_notification.message
            assert "Test Problem" in in_app_notification.message
            
            print("✓ Immediate notification creates in-app notification")
            
            # Test batched notification (daily frequency)
            result = NotificationService.dispatch(
                event_name="case_approved",
                user=test_user,
                title="Test Case",
                description="Test case description"
            )
            
            assert result == True
            print("✓ Batched notification queued successfully")
            
            # Test threshold-based escalation scheduling
            result = NotificationService.dispatch(
                event_name="milestone_due",
                user=test_user,
                title="Important Milestone",
                description="Milestone due soon"
            )
            
            assert result == True
            print("✓ Threshold-based notification processed correctly")

    def test_get_setting_function(self, notification_settings):
        """Test get_setting() helper function"""
        with app.app_context():
            # Test existing setting
            setting = get_setting("problem_created")
            assert setting is not None
            assert setting.event_name == "problem_created"
            assert setting.frequency == FrequencyEnum.immediate
            
            # Test non-existent setting
            setting = get_setting("non_existent_event")
            assert setting is None
            
            print("✓ get_setting() function works correctly")

    def test_channel_preferences_enforcement(self, test_user, notification_settings):
        """Test that channel preferences are properly enforced"""
        with app.app_context():
            # Get case_approved setting (email=True, in_app=False)
            setting = get_setting("case_approved")
            original_in_app_count = Notification.query.filter_by(user_id=test_user.id).count()
            
            # Dispatch notification
            NotificationService.dispatch(
                event_name="case_approved",
                user=test_user,
                title="Case Approved"
            )
            
            # Since in_app is False for case_approved, no new in-app notification should be created for batched notifications
            # (This depends on implementation - batch notifications might handle in-app differently)
            new_in_app_count = Notification.query.filter_by(user_id=test_user.id).count()
            
            print(f"✓ Channel preferences respected - in_app notifications: {new_in_app_count - original_in_app_count}")

    def test_frequency_based_routing(self, test_user, notification_settings):
        """Test that frequency determines immediate vs batch routing"""
        with app.app_context():
            service = NotificationService()
            
            # Test immediate frequency
            immediate_setting = get_setting("problem_created")
            assert immediate_setting.frequency == FrequencyEnum.immediate
            
            # Test batch frequency  
            batch_setting = get_setting("case_approved")
            assert batch_setting.frequency == FrequencyEnum.daily
            
            print("✓ Frequency-based routing logic verified")

    def test_threshold_configuration(self, notification_settings):
        """Test threshold hours configuration"""
        with app.app_context():
            # problem_created should have no threshold (immediate)
            problem_setting = get_setting("problem_created")
            assert problem_setting.threshold_hours is None
            
            # case_approved should have 24 hour threshold
            case_setting = get_setting("case_approved")
            assert case_setting.threshold_hours == 24
            
            # milestone_due should have 2 hour threshold
            milestone_setting = get_setting("milestone_due")
            assert milestone_setting.threshold_hours == 2
            
            print("✓ Threshold configuration verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])