#!/usr/bin/env python3
"""
Seed notification settings with default configuration
"""

import os
import sys
sys.path.append('.')

from app import app, db
from models import NotificationSetting, FrequencyEnum

def seed_notification_settings():
    """Initialize default notification settings for core business workflow events"""
    
    with app.app_context():
        print("🌱 Seeding notification settings...")
        
        # Core notification events with intelligent defaults
        default_events = [
            {
                'event_name': 'problem_created',
                'frequency': FrequencyEnum.immediate,
                'channel_email': True,
                'channel_in_app': True,
                'channel_push': False,
                'threshold_hours': None  # No escalation for immediate notifications
            },
            {
                'event_name': 'case_approved', 
                'frequency': FrequencyEnum.immediate,
                'channel_email': True,
                'channel_in_app': True,
                'channel_push': False,
                'threshold_hours': None
            },
            {
                'event_name': 'project_created',
                'frequency': FrequencyEnum.daily,
                'channel_email': True,
                'channel_in_app': True,
                'channel_push': False,
                'threshold_hours': 24  # Escalate if no acknowledgment in 24 hours
            },
            {
                'event_name': 'milestone_due',
                'frequency': FrequencyEnum.immediate,
                'channel_email': True,
                'channel_in_app': True,
                'channel_push': True,  # Critical timing notification
                'threshold_hours': 2   # Quick escalation for time-sensitive events
            },
            {
                'event_name': 'milestone_overdue',
                'frequency': FrequencyEnum.immediate,
                'channel_email': True,
                'channel_in_app': True,
                'channel_push': True,  # Critical overdue notification
                'threshold_hours': 1   # Very quick escalation for overdue items
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for event_config in default_events:
            existing = NotificationSetting.query.filter_by(event_name=event_config['event_name']).first()
            
            if not existing:
                # Create new notification setting
                ns = NotificationSetting(
                    event_name=event_config['event_name'],
                    frequency=event_config['frequency'],
                    channel_email=event_config['channel_email'],
                    channel_in_app=event_config['channel_in_app'],
                    channel_push=event_config['channel_push'],
                    threshold_hours=event_config['threshold_hours']
                )
                db.session.add(ns)
                created_count += 1
                print(f"   ✓ Created: {event_config['event_name']} ({event_config['frequency'].value})")
            else:
                # Update existing if needed (optional - comment out if you want to preserve user changes)
                if existing.frequency != event_config['frequency']:
                    existing.frequency = event_config['frequency']
                    existing.threshold_hours = event_config['threshold_hours']
                    updated_count += 1
                    print(f"   ⟳ Updated: {event_config['event_name']} frequency")
        
        try:
            db.session.commit()
            print(f"\n🎉 Notification settings seeded successfully!")
            print(f"   Created: {created_count} new settings")
            print(f"   Updated: {updated_count} existing settings")
            
            # Verify all settings exist
            total_settings = NotificationSetting.query.count()
            print(f"   Total notification settings: {total_settings}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error seeding notification settings: {e}")
            return False
            
        return True

if __name__ == "__main__":
    success = seed_notification_settings()
    sys.exit(0 if success else 1)