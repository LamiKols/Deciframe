#!/usr/bin/env python3
"""
Test script to verify notification settings integration with NotificationService
"""

import os
import sys
sys.path.append('.')

from app import app
from models import User, NotificationSetting, FrequencyEnum
from notifications.service import NotificationService, get_setting

def test_notification_integration():
    """Test the complete notification settings integration"""
    
    with app.app_context():
        print("🧪 Testing Notification Settings Integration")
        print("=" * 50)
        
        # Test 1: Check if notification settings exist
        print("\n1. Checking notification settings...")
        settings = NotificationSetting.query.all()
        print(f"   Found {len(settings)} notification settings")
        
        for setting in settings[:3]:  # Show first 3
            print(f"   - {setting.event_name}: {setting.frequency.value} | Email: {setting.channel_email} | In-App: {setting.channel_in_app}")
        
        # Test 2: Test get_setting function
        print("\n2. Testing get_setting function...")
        test_event = "problem_created"
        setting = get_setting(test_event)
        
        if setting:
            print(f"   ✓ Found setting for '{test_event}'")
            print(f"     Frequency: {setting.frequency.value}")
            print(f"     Channels: Email={setting.channel_email}, In-App={setting.channel_in_app}")
            if setting.threshold_hours:
                print(f"     Threshold: {setting.threshold_hours} hours")
        else:
            print(f"   ❌ No setting found for '{test_event}'")
        
        # Test 3: Test dispatch with real user
        print("\n3. Testing NotificationService.dispatch...")
        test_user = User.query.first()
        
        if test_user:
            print(f"   Testing with user: {test_user.name} ({test_user.email})")
            
            # Test dispatch with immediate frequency
            result = NotificationService.dispatch(
                event_name="problem_created",
                user=test_user,
                title="Test Problem Title",
                description="This is a test notification",
                link="/problems/test"
            )
            
            if result:
                print("   ✓ Dispatch successful")
            else:
                print("   ⚠️ Dispatch returned False (may be due to missing SendGrid)")
        else:
            print("   ❌ No test user found")
        
        # Test 4: Test frequency-based logic
        print("\n4. Testing frequency-based dispatch logic...")
        
        # Test immediate frequency
        immediate_setting = NotificationSetting.query.filter_by(frequency=FrequencyEnum.immediate).first()
        if immediate_setting:
            print(f"   ✓ Found immediate frequency setting: {immediate_setting.event_name}")
        
        # Test non-immediate frequency
        batch_setting = NotificationSetting.query.filter(
            NotificationSetting.frequency != FrequencyEnum.immediate
        ).first()
        if batch_setting:
            print(f"   ✓ Found batch frequency setting: {batch_setting.event_name} ({batch_setting.frequency.value})")
        
        print("\n" + "=" * 50)
        print("✓ Notification settings integration test completed")
        
        return True

if __name__ == "__main__":
    test_notification_integration()