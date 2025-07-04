#!/usr/bin/env python3
"""
Simple test script for notification settings functionality
"""

import sys
sys.path.append('.')

from app import app, db
from models import User, NotificationSetting, Notification, FrequencyEnum, RoleEnum
from notifications.service import NotificationService, get_setting

def test_notification_settings():
    """Test notification settings integration"""
    
    with app.app_context():
        print("🧪 Testing notification settings functionality...")
        
        # Test 1: Check if seed data was created
        print("\n1. Testing automatic seed data creation...")
        settings_count = NotificationSetting.query.count()
        print(f"   Found {settings_count} notification settings")
        
        expected_events = ['problem_created', 'case_approved', 'project_created', 'milestone_due', 'milestone_overdue']
        for event_name in expected_events:
            setting = get_setting(event_name)
            if setting:
                print(f"   ✓ {event_name}: {setting.frequency.value} frequency, email={setting.channel_email}")
            else:
                print(f"   ❌ {event_name}: Not found")
        
        # Test 2: Test get_setting function
        print("\n2. Testing get_setting() helper function...")
        setting = get_setting("problem_created")
        if setting:
            print(f"   ✓ get_setting() returns: {setting.event_name} with {setting.frequency.value}")
        else:
            print("   ❌ get_setting() failed")
        
        # Test non-existent setting
        missing_setting = get_setting("non_existent_event")
        if missing_setting is None:
            print("   ✓ get_setting() returns None for missing events")
        else:
            print("   ❌ get_setting() should return None for missing events")
        
        # Test 3: Test NotificationService.dispatch() integration
        print("\n3. Testing NotificationService.dispatch()...")
        
        # Create test user
        test_user = User.query.filter_by(email="lami.kolade@gmail.com").first()
        if not test_user:
            print("   ❌ Test user not found")
            return
        
        original_count = Notification.query.filter_by(user_id=test_user.id).count()
        
        # Test immediate notification
        result = NotificationService.dispatch(
            event_name="problem_created",
            user=test_user,
            title="Test Problem",
            description="Test problem description",
            link="/problems/1"
        )
        
        if result:
            print("   ✓ dispatch() returned success")
            
            # Check if in-app notification was created for immediate events
            new_count = Notification.query.filter_by(user_id=test_user.id).count()
            if new_count > original_count:
                print(f"   ✓ In-app notification created ({new_count - original_count} new)")
            else:
                print("   • No new in-app notification (may be by design for this event)")
        else:
            print("   ❌ dispatch() failed")
        
        # Test 4: Test frequency-based routing
        print("\n4. Testing frequency-based routing...")
        
        immediate_setting = get_setting("problem_created")
        batch_setting = get_setting("project_created")
        
        if immediate_setting and immediate_setting.frequency == FrequencyEnum.immediate:
            print("   ✓ problem_created uses immediate frequency")
        else:
            print("   ❌ problem_created should use immediate frequency")
            
        if batch_setting and batch_setting.frequency == FrequencyEnum.daily:
            print("   ✓ project_created uses daily frequency")
        else:
            print("   ❌ project_created should use daily frequency")
        
        # Test 5: Test threshold configuration
        print("\n5. Testing threshold configuration...")
        
        milestone_setting = get_setting("milestone_due")
        if milestone_setting:
            if milestone_setting.threshold_hours == 2:
                print("   ✓ milestone_due has 2-hour threshold")
            else:
                print(f"   • milestone_due threshold: {milestone_setting.threshold_hours} hours")
        else:
            print("   ❌ milestone_due setting not found")
        
        print("\n🎉 Notification settings tests completed!")

if __name__ == "__main__":
    test_notification_settings()