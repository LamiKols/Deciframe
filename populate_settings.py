"""
Populate Settings Management with Current Application Configurations
Creates comprehensive system settings based on config.py and application defaults
"""

from app import app, db
from models import Setting
from config import Config
import os
from datetime import datetime

def populate_application_settings():
    """Populate settings management with current application configurations"""
    
    with app.app_context():
        print("🔧 Populating Settings Management with application configurations...")
        
        # Define comprehensive application settings
        application_settings = [
            # Business Logic Settings
            {
                'key': 'FULL_CASE_THRESHOLD',
                'value': '25000',
                'description': 'Monetary threshold (in base currency) above which business cases require full elaboration instead of light treatment'
            },
            {
                'key': 'ENABLE_HYBRID_CASES',
                'value': 'True',
                'description': 'Enable hybrid business cases that can be both reactive (problem-linked) and proactive (initiative-only)'
            },
            {
                'key': 'ENABLE_AI_REQS',
                'value': 'True',
                'description': 'Enable AI-powered requirements generation for technology projects'
            },
            
            # Session & Security Settings
            {
                'key': 'SESSION_LIFETIME_HOURS',
                'value': '12',
                'description': 'Maximum session duration in hours before automatic logout'
            },
            {
                'key': 'SESSION_COOKIE_SECURE',
                'value': 'False',
                'description': 'Require HTTPS for session cookies (set to True in production)'
            },
            {
                'key': 'DEBUG_MODE',
                'value': 'True',
                'description': 'Enable debug mode for development (should be False in production)'
            },
            
            # Organization Defaults
            {
                'key': 'DEFAULT_CURRENCY',
                'value': 'USD',
                'description': 'Default currency code for new organizations (USD, EUR, GBP, etc.)'
            },
            {
                'key': 'DEFAULT_DATE_FORMAT',
                'value': '%Y-%m-%d',
                'description': 'Default date format pattern for new organizations'
            },
            {
                'key': 'DEFAULT_TIMEZONE',
                'value': 'UTC',
                'description': 'Default timezone for new organizations'
            },
            
            # Workflow & Automation Settings
            {
                'key': 'BA_ASSIGNMENT_TIMEOUT_HOURS',
                'value': '72',
                'description': 'Hours before business case assignment to Business Analyst times out'
            },
            {
                'key': 'DIRECTOR_APPROVAL_TIMEOUT_HOURS',
                'value': '72',
                'description': 'Hours before director approval of business cases times out'
            },
            {
                'key': 'AUTO_TRIAGE_ENABLED',
                'value': 'True',
                'description': 'Enable automatic triage rule execution every 30 minutes'
            },
            {
                'key': 'EMAIL_NOTIFICATIONS_ENABLED',
                'value': 'True',
                'description': 'Enable email notifications for workflow events'
            },
            {
                'key': 'IN_APP_NOTIFICATIONS_ENABLED',
                'value': 'True',
                'description': 'Enable in-app notifications for workflow events'
            },
            
            # Database & Performance Settings
            {
                'key': 'DB_POOL_RECYCLE_SECONDS',
                'value': '300',
                'description': 'Database connection pool recycle time in seconds'
            },
            {
                'key': 'DB_POOL_PRE_PING',
                'value': 'True',
                'description': 'Enable database connection pre-ping for reliability'
            },
            
            # AI Service Settings
            {
                'key': 'AI_SERVICE_AVAILABLE',
                'value': str(bool(os.getenv('OPENAI_API_KEY'))),
                'description': 'Whether AI services are available (depends on OPENAI_API_KEY)'
            },
            {
                'key': 'AI_MODEL_DEFAULT',
                'value': 'gpt-4o',
                'description': 'Default AI model for requirements generation and analysis'
            },
            
            # Report & Export Settings
            {
                'key': 'MAX_EXPORT_RECORDS',
                'value': '10000',
                'description': 'Maximum number of records to export in a single CSV/Excel file'
            },
            {
                'key': 'REPORT_CACHE_MINUTES',
                'value': '15',
                'description': 'Cache duration for generated reports in minutes'
            },
            
            # Project Management Settings
            {
                'key': 'DEFAULT_PROJECT_STATUS',
                'value': 'Open',
                'description': 'Default status for newly created projects'
            },
            {
                'key': 'DEFAULT_PROBLEM_PRIORITY',
                'value': 'Medium',
                'description': 'Default priority level for newly submitted problems'
            },
            {
                'key': 'AUTO_MILESTONE_CREATION',
                'value': 'True',
                'description': 'Automatically create default milestones when converting business case to project'
            },
            
            # Help & Support Settings
            {
                'key': 'CONTEXTUAL_HELP_ENABLED',
                'value': 'True',
                'description': 'Enable contextual help buttons throughout the application'
            },
            {
                'key': 'HELP_SEARCH_ENABLED',
                'value': 'True',
                'description': 'Enable real-time search in help center'
            },
            {
                'key': 'FLOATING_HELP_WIDGET',
                'value': 'True',
                'description': 'Show floating help widget in bottom-right corner'
            },
            
            # Integration Settings
            {
                'key': 'SENDGRID_ENABLED',
                'value': str(bool(os.getenv('SENDGRID_API_KEY'))),
                'description': 'Whether SendGrid email service is available'
            },
            {
                'key': 'SENTRY_MONITORING_ENABLED',
                'value': 'True',
                'description': 'Enable Sentry error monitoring and performance tracking'
            }
        ]
        
        # Create or update settings
        created_count = 0
        updated_count = 0
        
        for setting_data in application_settings:
            existing_setting = Setting.query.filter_by(key=setting_data['key']).first()
            
            if existing_setting:
                # Update existing setting description if it's improved
                if existing_setting.description != setting_data['description']:
                    existing_setting.description = setting_data['description']
                    existing_setting.updated_at = datetime.utcnow()
                    updated_count += 1
                    print(f"✅ Updated: {setting_data['key']}")
            else:
                # Create new setting
                new_setting = Setting(
                    key=setting_data['key'],
                    value=setting_data['value'],
                    description=setting_data['description'],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(new_setting)
                created_count += 1
                print(f"🆕 Created: {setting_data['key']}")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n🎉 Settings population complete!")
            print(f"   📊 Created: {created_count} new settings")
            print(f"   🔄 Updated: {updated_count} existing settings")
            print(f"   📈 Total settings: {len(application_settings)}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error saving settings: {e}")
            return False
        
        return True

if __name__ == "__main__":
    success = populate_application_settings()
    if success:
        print("\n✅ Settings Management has been populated with current application configurations!")
        print("   Users can now see and manage all system settings through the Settings Management interface.")
    else:
        print("\n❌ Failed to populate settings. Please check the error messages above.")