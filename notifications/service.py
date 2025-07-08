"""
Notification Service Layer
Handles email dispatch via SendGrid and in-app notification creation
"""

import os
from datetime import datetime, timedelta
from flask import current_app, render_template_string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app import db
from models import NotificationTemplate, Notification, NotificationEventEnum, User, NotificationSetting, FrequencyEnum


def get_setting(event_name):
    """Get notification setting for a specific event"""
    return NotificationSetting.query.filter_by(event_name=event_name).first()


class NotificationService:
    """Service for handling notification dispatch"""
    
    def __init__(self):
        self.sendgrid_client = None
        self._init_sendgrid()
    
    @staticmethod
    def dispatch(event_name, user, **context):
        """
        Dispatch notification based on configured settings
        
        Args:
            event_name: String name of the event (e.g., 'problem_created')
            user: User object or user_id to receive notification
            **context: Additional context data for template rendering
        """
        # Get notification settings for this event
        setting = get_setting(event_name)
        if not setting or not (setting.channel_email or setting.channel_in_app or setting.channel_push):
            print(f"⏭️ No notification setting or channels enabled for event: {event_name}")
            return False
        
        # Get user object if user_id passed
        if isinstance(user, int):
            user = User.query.get(user)
            if not user:
                print(f"❌ User not found: {user}")
                return False
        
        try:
            # Handle frequency-based dispatch
            if setting.frequency == FrequencyEnum.immediate:
                # Send immediately
                return notification_service._send_immediate(setting, user, event_name, context)
            else:
                # Queue for batch processing (hourly, daily, weekly)
                return notification_service._queue_notification(setting, user, event_name, context)
                
        except Exception as e:
            print(f"❌ Notification dispatch failed - Event: {event_name}, Error: {e}")
            return False
    
    def _send_immediate(self, setting, user, event_name, context):
        """Send notification immediately based on enabled channels"""
        success = True
        
        # Send via enabled channels
        if setting.channel_in_app:
            success &= self._create_in_app_notification_with_setting(user.id, event_name, context)
        
        if setting.channel_email and self.sendgrid_client:
            success &= self._send_email_with_setting(user, event_name, context)
        
        # Schedule escalation if threshold is set
        if setting.threshold_hours and setting.threshold_hours > 0:
            self._schedule_escalation(setting, user, event_name, context)
        
        print(f"✓ Immediate notification sent - Event: {event_name}, User: {user.name}, Channels: {'email' if setting.channel_email else ''}{'in-app' if setting.channel_in_app else ''}")
        return success
    
    def _queue_notification(self, setting, user, event_name, context):
        """Queue notification for batch processing based on frequency"""
        try:
            # For now, store in-app notification immediately and queue email
            if setting.channel_in_app:
                self._create_in_app_notification_with_setting(user.id, event_name, context)
            
            # TODO: Implement actual queue system for batch email processing
            # For demonstration, we'll send email immediately but log the intended frequency
            if setting.channel_email and self.sendgrid_client:
                print(f"📧 Queuing email for {setting.frequency.value} batch processing - Event: {event_name}, User: {user.name}")
                self._send_email_with_setting(user, event_name, context)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to queue notification: {e}")
            return False
    
    def _schedule_escalation(self, setting, user, event_name, context):
        """Schedule escalation notification after threshold hours"""
        try:
            escalation_time = datetime.utcnow() + timedelta(hours=setting.threshold_hours)
            print(f"⏰ Escalation scheduled for {escalation_time} - Event: {event_name}, User: {user.name}")
            
            # TODO: Implement actual scheduling system (APScheduler or task queue)
            # For now, just log the intended escalation
            
        except Exception as e:
            print(f"❌ Failed to schedule escalation: {e}")
    
    def _create_in_app_notification_with_setting(self, user_id, event_name, context):
        """Create in-app notification using event name and context"""
        try:
            # Create a simple message from event name and context
            message = f"New {event_name.replace('_', ' ').title()}"
            if context.get('title'):
                message += f": {context['title']}"
            elif context.get('name'):
                message += f": {context['name']}"
            
            notification = Notification(
                user_id=user_id,
                message=message,
                link=context.get('link'),
                event_type=None,  # We don't have enum mapping for string event names
                read_flag=False
            )
            db.session.add(notification)
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Failed to create in-app notification: {e}")
            db.session.rollback()
            return False
    
    def _send_email_with_setting(self, user, event_name, context):
        """Send email using event name and context"""
        try:
            # Create subject and body from event name and context
            subject = f"DeciFrame: {event_name.replace('_', ' ').title()}"
            if context.get('title'):
                subject += f" - {context['title']}"
            elif context.get('name'):
                subject += f" - {context['name']}"
            
            # Create HTML body
            body = f"""
            <h3>{event_name.replace('_', ' ').title()}</h3>
            <p>Hello {user.name},</p>
            <p>This is a notification from DeciFrame regarding a {event_name.replace('_', ' ')}.</p>
            """
            
            # Add context details
            for key, value in context.items():
                if key not in ['link'] and value:
                    body += f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>"
            
            if context.get('link'):
                body += f'<p><a href="{context["link"]}">View Details</a></p>'
            
            body += "<p>Best regards,<br>DeciFrame Team</p>"
            
            return self._send_email(
                to_email=user.email,
                subject=subject,
                content=body,
                user_name=user.name
            )
            
        except Exception as e:
            print(f"❌ Failed to send email with setting: {e}")
            return False
    
    def _init_sendgrid(self):
        """Initialize SendGrid client if API key is available"""
        api_key = os.environ.get('SENDGRID_API_KEY')
        if api_key:
            self.sendgrid_client = SendGridAPIClient(api_key)
            print("✓ SendGrid client initialized")
        else:
            print("⚠️ SENDGRID_API_KEY not found - email notifications disabled")
    
    def send_notification(self, event_type, user_id, context_data=None):
        """
        Send notification for a specific event
        
        Args:
            event_type: NotificationEventEnum value
            user_id: Target user ID
            context_data: Dictionary with template variables
        """
        try:
            # Get notification template
            template = NotificationTemplate.query.filter_by(event=event_type).first()
            if not template:
                print(f"❌ No template found for event: {event_type.value}")
                return False
            
            # Get target user
            user = User.query.get(user_id)
            if not user:
                print(f"❌ User not found: {user_id}")
                return False
            
            # Prepare context data
            context = context_data or {}
            context.update({
                'user_name': user.name,
                'user_email': user.email,
                'app_name': 'DeciFrame'
            })
            
            # Render message content
            rendered_message = self._render_template(template.body, context)
            rendered_subject = self._render_template(template.subject, context)
            
            # Create in-app notification if enabled
            notification_id = None
            if template.in_app_enabled:
                notification_id = self._create_in_app_notification(
                    user_id=user_id,
                    message=rendered_message,
                    event_type=event_type,
                    link=context.get('link')
                )
            
            # Send email if enabled and SendGrid is available
            email_sent = False
            if template.email_enabled and self.sendgrid_client:
                email_sent = self._send_email(
                    to_email=user.email,
                    subject=rendered_subject,
                    content=rendered_message,
                    user_name=user.name
                )
                
                # Update notification record with email status
                if notification_id:
                    self._update_email_status(notification_id, email_sent)
            
            print(f"✓ Notification sent - Event: {event_type.value}, User: {user.name}, Email: {email_sent}")
            return True
            
        except Exception as e:
            print(f"❌ Notification failed - Event: {event_type.value}, Error: {e}")
            return False
    
    def _render_template(self, template_string, context):
        """Render template string with context variables"""
        try:
            return render_template_string(template_string, **context)
        except Exception as e:
            print(f"❌ Template rendering failed: {e}")
            return template_string
    
    def _create_in_app_notification(self, user_id, message, event_type, link=None):
        """Create in-app notification record"""
        try:
            notification = Notification(
                user_id=user_id,
                message=message,
                link=link,
                event_type=event_type,
                read_flag=False
            )
            db.session.add(notification)
            db.session.flush()
            db.session.commit()
            return notification.id
        except Exception as e:
            print(f"❌ Failed to create in-app notification: {e}")
            db.session.rollback()
            return None
    
    def _send_email(self, to_email, subject, content, user_name=None):
        """Send email via SendGrid"""
        try:
            from_email = Email(os.environ.get('FROM_EMAIL', 'noreply@deciframe.com'))
            to_email_obj = To(to_email, user_name)
            
            mail = Mail(
                from_email=from_email,
                to_emails=to_email_obj,
                subject=subject,
                html_content=Content("text/html", content)
            )
            
            response = self.sendgrid_client.send(mail)
            return response.status_code in [200, 202]
            
        except Exception as e:
            print(f"❌ Email send failed: {e}")
            return False
    
    def _send_email_with_attachment(self, to_email, subject, body, attachment_path, attachment_name):
        """Send email with PDF attachment using SendGrid"""
        if not self.sendgrid_client:
            print("⚠️ SendGrid not configured - cannot send report email")
            return False
        
        try:
            import base64
            from sendgrid.helpers.mail import Attachment, FileContent, FileName, FileType, Disposition
            
            # Read and encode attachment
            with open(attachment_path, 'rb') as f:
                data = f.read()
                f.close()
            encoded_file = base64.b64encode(data).decode()
            
            # Create email with attachment
            from_email = Email(self.from_email)
            to_email_obj = To(to_email)
            
            mail = Mail(
                from_email=from_email,
                to_emails=to_email_obj,
                subject=subject,
                html_content=Content("text/html", body)
            )
            
            # Add attachment
            attachedFile = Attachment(
                FileContent(encoded_file),
                FileName(attachment_name),
                FileType('application/pdf'),
                Disposition('attachment')
            )
            mail.attachment = attachedFile
            
            response = self.sendgrid_client.send(mail)
            return response.status_code in [200, 202]
            
        except Exception as e:
            print(f"❌ Email with attachment failed: {e}")
            return False
    
    def _update_email_status(self, notification_id, email_sent):
        """Update notification with email send status"""
        try:
            notification = Notification.query.get(notification_id)
            if notification:
                notification.email_sent = email_sent
                if email_sent:
                    notification.email_sent_at = datetime.utcnow()
                db.session.commit()
        except Exception as e:
            print(f"❌ Failed to update email status: {e}")
            db.session.rollback()
    
    def get_user_notifications(self, user_id, unread_only=False, limit=50):
        """Get notifications for a user"""
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(read_flag=False)
        
        return query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    def mark_notification_read(self, notification_id, user_id):
        """Mark a notification as read (with user verification)"""
        try:
            notification = Notification.query.filter_by(
                id=notification_id, 
                user_id=user_id
            ).first()
            
            if notification:
                notification.read_flag = True
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            print(f"❌ Failed to mark notification as read: {e}")
            db.session.rollback()
            return False
    
    def mark_all_read(self, user_id):
        """Mark all notifications as read for a user"""
        try:
            Notification.query.filter_by(
                user_id=user_id, 
                read_flag=False
            ).update({'read_flag': True})
            db.session.commit()
            return True
        except Exception as e:
            print(f"❌ Failed to mark all notifications as read: {e}")
            db.session.rollback()
            return False


# Global notification service instance
notification_service = NotificationService()


def send_notification(event_type, user_id, context_data=None):
    """Convenience function for sending notifications"""
    return notification_service.send_notification(event_type, user_id, context_data)


def initialize_default_templates():
    """Initialize default notification templates"""
    templates = [
        {
            'event': NotificationEventEnum.BUSINESS_CASE_APPROVED,
            'subject': 'Business Case Approved - {{ business_case_code }}',
            'body': '''
            <h3>Business Case Approved</h3>
            <p>Hello {{ user_name }},</p>
            <p>The business case <strong>{{ business_case_code }} - {{ business_case_title }}</strong> has been approved and you have been assigned as the Project Manager.</p>
            <p><strong>Budget:</strong> ${{ budget:,.2f }}</p>
            <p><strong>Expected ROI:</strong> {{ roi }}%</p>
            <p>Please review the details and begin project planning.</p>
            <p><a href="{{ link }}">View Business Case</a></p>
            <p>Best regards,<br>DeciFrame Team</p>
            '''
        },
        {
            'event': NotificationEventEnum.PROBLEM_CREATED,
            'subject': 'New Problem Reported - {{ problem_code }}',
            'body': '''
            <h3>New Problem Reported</h3>
            <p>Hello {{ user_name }},</p>
            <p>A new problem has been reported in your department:</p>
            <p><strong>{{ problem_code }} - {{ problem_title }}</strong></p>
            <p><strong>Priority:</strong> {{ priority }}</p>
            <p><strong>Department:</strong> {{ department_name }}</p>
            <p><strong>Reported by:</strong> {{ reporter_name }}</p>
            <p>{{ problem_description }}</p>
            <p><a href="{{ link }}">View Problem Details</a></p>
            <p>Best regards,<br>DeciFrame Team</p>
            '''
        },
        {
            'event': NotificationEventEnum.MILESTONE_DUE_SOON,
            'subject': 'Milestone Due Soon - {{ milestone_name }}',
            'body': '''
            <h3>Milestone Due Soon</h3>
            <p>Hello {{ user_name }},</p>
            <p>Your milestone <strong>{{ milestone_name }}</strong> is due soon:</p>
            <p><strong>Project:</strong> {{ project_code }} - {{ project_name }}</p>
            <p><strong>Due Date:</strong> {{ due_date }}</p>
            <p><strong>Description:</strong> {{ milestone_description }}</p>
            <p>Please ensure completion by the due date.</p>
            <p><a href="{{ link }}">View Project Details</a></p>
            <p>Best regards,<br>DeciFrame Team</p>
            '''
        },
        {
            'event': NotificationEventEnum.PROJECT_CREATED,
            'subject': 'New Project Assigned - {{ project_code }}',
            'body': '''
            <h3>New Project Assigned</h3>
            <p>Hello {{ user_name }},</p>
            <p>You have been assigned as Project Manager for:</p>
            <p><strong>{{ project_code }} - {{ project_name }}</strong></p>
            <p><strong>Budget:</strong> ${{ budget:,.2f }}</p>
            <p><strong>Start Date:</strong> {{ start_date }}</p>
            <p><strong>End Date:</strong> {{ end_date }}</p>
            <p>{{ project_description }}</p>
            <p><a href="{{ link }}">View Project Details</a></p>
            <p>Best regards,<br>DeciFrame Team</p>
            '''
        }
    ]
    
    try:
        for template_data in templates:
            existing = NotificationTemplate.query.filter_by(event=template_data['event']).first()
            if not existing:
                template = NotificationTemplate(
                    event=template_data['event'],
                    subject=template_data['subject'],
                    body=template_data['body']
                )
                db.session.add(template)
        
        db.session.commit()
        print("✓ Default notification templates initialized")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize templates: {e}")
        db.session.rollback()
        return False