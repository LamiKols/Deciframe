"""
Comprehensive test suite for Workflow Automation & Notifications system
Tests all notification models, event hooks, dispatch mechanisms, and UI functionality
"""

import sys
import os
from datetime import date, datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import (
    User, Department, Problem, BusinessCase, Project, ProjectMilestone,
    Notification, NotificationTemplate, NotificationEventEnum,
    StatusEnum, PriorityEnum, RoleEnum, CaseTypeEnum, CaseDepthEnum
)
from notifications.service import NotificationService, initialize_default_templates
from notifications.events import NotificationEvents
from werkzeug.security import generate_password_hash


def setup_test_data():
    """Create comprehensive test data for notification testing"""
    with app.app_context():
        # Clean up existing test data
        Notification.query.delete()
        NotificationTemplate.query.delete()
        
        # Get existing data or create minimal test data
        dept = Department.query.first()
        if not dept:
            dept = Department(name='Test Department', level=1)
            db.session.add(dept)
            db.session.flush()
        
        # Create test users with different roles
        users = {}
        user_data = [
            {'email': 'manager@test.com', 'name': 'Test Manager', 'role': RoleEnum.Manager},
            {'email': 'pm@test.com', 'name': 'Test PM', 'role': RoleEnum.PM},
            {'email': 'staff@test.com', 'name': 'Test Staff', 'role': RoleEnum.Staff},
            {'email': 'director@test.com', 'name': 'Test Director', 'role': RoleEnum.Director}
        ]
        
        for user_info in user_data:
            user = User.query.filter_by(email=user_info['email']).first()
            if not user:
                user = User(
                    email=user_info['email'],
                    password_hash=generate_password_hash('testpass'),
                    name=user_info['name'],
                    role=user_info['role'],
                    department_id=dept.id
                )
                db.session.add(user)
                db.session.flush()
            users[user_info['role'].value] = user
        
        db.session.commit()
        return dept, users


def test_notification_models():
    """Test notification model creation and functionality"""
    print("\n🧪 Testing Notification Models")
    print("=" * 35)
    
    with app.app_context():
        dept, users = setup_test_data()
        manager = users['Manager']
        
        # Test NotificationTemplate creation
        template = NotificationTemplate(
            event=NotificationEventEnum.BUSINESS_CASE_APPROVED,
            subject="Test Subject - {{ business_case_code }}",
            body="Test notification body with {{ user_name }}",
            email_enabled=True,
            in_app_enabled=True
        )
        db.session.add(template)
        db.session.flush()
        
        print(f"✓ Created NotificationTemplate: {template.event.value}")
        assert template.id is not None
        assert template.subject == "Test Subject - {{ business_case_code }}"
        
        # Test Notification creation
        notification = Notification(
            user_id=manager.id,
            message="Test notification message",
            link="/test/link",
            event_type=NotificationEventEnum.BUSINESS_CASE_APPROVED,
            read_flag=False
        )
        db.session.add(notification)
        db.session.flush()
        
        print(f"✓ Created Notification: {notification.id}")
        assert notification.user_id == manager.id
        assert notification.read_flag == False
        assert notification.event_type == NotificationEventEnum.BUSINESS_CASE_APPROVED
        
        # Test notification mark as read
        notification.mark_as_read()
        assert notification.read_flag == True
        print("✓ Mark as read functionality working")
        
        db.session.commit()
        return template, notification


def test_notification_service():
    """Test notification service functionality"""
    print("\n🧪 Testing Notification Service")
    print("=" * 33)
    
    with app.app_context():
        dept, users = setup_test_data()
        manager = users['Manager']
        
        # Initialize default templates
        initialize_default_templates()
        print("✓ Default templates initialized")
        
        # Create notification service
        service = NotificationService()
        print("✓ NotificationService created")
        
        # Test sending notification
        context_data = {
            'business_case_code': 'C0001',
            'business_case_title': 'Test Business Case',
            'budget': 50000.0,
            'roi': 150.0,
            'link': '/business/cases/1'
        }
        
        success = service.send_notification(
            NotificationEventEnum.BUSINESS_CASE_APPROVED,
            manager.id,
            context_data
        )
        
        print(f"✓ Notification sent: {success}")
        assert success == True
        
        # Verify notification was created
        notifications = service.get_user_notifications(manager.id)
        assert len(notifications) > 0
        print(f"✓ Retrieved {len(notifications)} notifications for user")
        
        # Test mark as read
        notification_id = notifications[0].id
        read_success = service.mark_notification_read(notification_id, manager.id)
        assert read_success == True
        print("✓ Mark notification as read working")
        
        # Test mark all as read
        all_read_success = service.mark_all_read(manager.id)
        assert all_read_success == True
        print("✓ Mark all notifications as read working")
        
        return service


def test_event_hooks():
    """Test automated event hooks"""
    print("\n🧪 Testing Event Hooks")
    print("=" * 25)
    
    with app.app_context():
        dept, users = setup_test_data()
        manager = users['Manager']
        pm = users['Project Manager']
        staff = users['Staff']
        
        # Initialize templates
        initialize_default_templates()
        
        # Test 1: Business Case Approval Event
        print("\n1. Testing Business Case Approval Event")
        business_case = BusinessCase(
            title='Test Business Case for Approval',
            description='Testing notification on approval',
            cost_estimate=75000.0,
            benefit_estimate=150000.0,
            created_by=staff.id,
            case_type=CaseTypeEnum.Proactive,
            case_depth=CaseDepthEnum.Full,
            initiative_name='Test Initiative'
        )
        db.session.add(business_case)
        db.session.flush()
        business_case.code = f'C{business_case.id:04d}'
        business_case.calculate_roi()
        db.session.commit()
        
        # Trigger approval event
        approval_success = NotificationEvents.on_business_case_approved(
            business_case.id, 
            pm.id
        )
        print(f"✓ Business case approval notification: {approval_success}")
        assert approval_success == True
        
        # Verify notification was created
        pm_notifications = Notification.query.filter_by(
            user_id=pm.id,
            event_type=NotificationEventEnum.BUSINESS_CASE_APPROVED
        ).all()
        assert len(pm_notifications) > 0
        print(f"✓ PM received {len(pm_notifications)} approval notifications")
        
        # Test 2: Problem Creation Event
        print("\n2. Testing Problem Creation Event")
        problem = Problem(
            title='Test Problem for Notification',
            description='Testing notification on problem creation',
            priority=PriorityEnum.High,
            department_id=dept.id,
            created_by=staff.id
        )
        db.session.add(problem)
        db.session.flush()
        problem.code = f'P{problem.id:04d}'
        db.session.commit()
        
        # Trigger problem creation event
        problem_success = NotificationEvents.on_problem_created(problem.id)
        print(f"✓ Problem creation notification: {problem_success}")
        assert problem_success == True
        
        # Verify notification was created for department manager
        manager_notifications = Notification.query.filter_by(
            user_id=manager.id,
            event_type=NotificationEventEnum.PROBLEM_CREATED
        ).all()
        assert len(manager_notifications) > 0
        print(f"✓ Manager received {len(manager_notifications)} problem notifications")
        
        # Test 3: Project Creation Event
        print("\n3. Testing Project Creation Event")
        project = Project(
            name='Test Project for Notification',
            description='Testing notification on project creation',
            budget=85000.0,
            status=StatusEnum.Open,
            priority=PriorityEnum.Medium,
            business_case_id=business_case.id,
            project_manager_id=pm.id,
            department_id=dept.id,
            created_by=manager.id
        )
        db.session.add(project)
        db.session.flush()
        project.code = f'PRJ{project.id:04d}'
        db.session.commit()
        
        # Trigger project creation event
        project_success = NotificationEvents.on_project_created(project.id)
        print(f"✓ Project creation notification: {project_success}")
        assert project_success == True
        
        # Test 4: Milestone Due Soon Event
        print("\n4. Testing Milestone Due Soon Event")
        milestone = ProjectMilestone(
            project_id=project.id,
            name='Test Milestone Due Soon',
            description='Testing milestone due notification',
            due_date=date.today() + timedelta(days=1),
            owner_id=pm.id,
            completed=False
        )
        db.session.add(milestone)
        db.session.flush()
        db.session.commit()
        
        # Trigger milestone due soon event
        milestone_success = NotificationEvents.on_milestone_due_soon(milestone.id, days_ahead=1)
        print(f"✓ Milestone due soon notification: {milestone_success}")
        assert milestone_success == True
        
        # Verify PM received milestone notification
        milestone_notifications = Notification.query.filter_by(
            user_id=pm.id,
            event_type=NotificationEventEnum.MILESTONE_DUE_SOON
        ).all()
        assert len(milestone_notifications) > 0
        print(f"✓ PM received {len(milestone_notifications)} milestone notifications")
        
        return True


def test_batch_notification_jobs():
    """Test batch notification jobs for overdue and upcoming milestones"""
    print("\n🧪 Testing Batch Notification Jobs")
    print("=" * 38)
    
    with app.app_context():
        dept, users = setup_test_data()
        pm = users['Project Manager']
        
        # Initialize templates
        initialize_default_templates()
        
        # Create test project
        project = Project(
            name='Test Project for Batch Jobs',
            description='Testing batch notification jobs',
            budget=50000.0,
            status=StatusEnum.InProgress,
            priority=PriorityEnum.Medium,
            project_manager_id=pm.id,
            department_id=dept.id,
            created_by=pm.id
        )
        db.session.add(project)
        db.session.flush()
        project.code = f'PRJ{project.id:04d}'
        
        # Create milestones with different due dates
        milestones_data = [
            {
                'name': 'Overdue Milestone',
                'due_date': date.today() - timedelta(days=2),
                'completed': False
            },
            {
                'name': 'Due Tomorrow',
                'due_date': date.today() + timedelta(days=1),
                'completed': False
            },
            {
                'name': 'Due Next Week',
                'due_date': date.today() + timedelta(days=7),
                'completed': False
            },
            {
                'name': 'Completed Overdue',
                'due_date': date.today() - timedelta(days=1),
                'completed': True
            }
        ]
        
        created_milestones = []
        for milestone_data in milestones_data:
            milestone = ProjectMilestone(
                project_id=project.id,
                name=milestone_data['name'],
                description=f"Testing {milestone_data['name']}",
                due_date=milestone_data['due_date'],
                owner_id=pm.id,
                completed=milestone_data['completed']
            )
            db.session.add(milestone)
            created_milestones.append(milestone)
        
        db.session.commit()
        print(f"✓ Created {len(created_milestones)} test milestones")
        
        # Test upcoming milestones check
        upcoming_count = NotificationEvents.check_upcoming_milestones(days_ahead=1)
        print(f"✓ Upcoming milestones check sent {upcoming_count} notifications")
        assert upcoming_count >= 1  # Should find "Due Tomorrow"
        
        # Test overdue milestones check
        overdue_count = NotificationEvents.check_overdue_milestones()
        print(f"✓ Overdue milestones check sent {overdue_count} notifications")
        assert overdue_count >= 1  # Should find "Overdue Milestone"
        
        # Verify notifications were created
        all_notifications = Notification.query.filter_by(user_id=pm.id).all()
        print(f"✓ Total notifications created: {len(all_notifications)}")
        
        return True


def test_notification_statistics():
    """Test notification statistics and reporting"""
    print("\n🧪 Testing Notification Statistics")
    print("=" * 37)
    
    with app.app_context():
        dept, users = setup_test_data()
        
        # Get notification statistics
        total_notifications = Notification.query.count()
        unread_notifications = Notification.query.filter_by(read_flag=False).count()
        read_notifications = Notification.query.filter_by(read_flag=True).count()
        
        print(f"✓ Total notifications: {total_notifications}")
        print(f"✓ Unread notifications: {unread_notifications}")
        print(f"✓ Read notifications: {read_notifications}")
        
        # Event type distribution
        event_stats = {}
        for event in NotificationEventEnum:
            count = Notification.query.filter_by(event_type=event).count()
            if count > 0:
                event_stats[event.value] = count
                print(f"  {event.value}: {count}")
        
        # User notification distribution
        user_stats = db.session.query(
            User.name,
            db.func.count(Notification.id).label('notification_count')
        ).join(Notification).group_by(User.name).all()
        
        print(f"✓ Notifications by user:")
        for user_name, count in user_stats:
            print(f"  {user_name}: {count}")
        
        # Template statistics
        template_count = NotificationTemplate.query.count()
        print(f"✓ Total notification templates: {template_count}")
        
        return {
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'event_stats': event_stats,
            'user_stats': dict(user_stats),
            'template_count': template_count
        }


def test_notification_integration():
    """Test end-to-end notification integration"""
    print("\n🧪 Testing End-to-End Integration")
    print("=" * 37)
    
    with app.app_context():
        dept, users = setup_test_data()
        manager = users['Manager']
        pm = users['Project Manager']
        staff = users['Staff']
        
        # Initialize system
        initialize_default_templates()
        service = NotificationService()
        
        print("✓ System initialized")
        
        # Simulate complete workflow
        print("\n1. Create Problem → Notify Manager")
        problem = Problem(
            title='Integration Test Problem',
            description='Testing complete notification workflow',
            priority=PriorityEnum.High,
            department_id=dept.id,
            created_by=staff.id
        )
        db.session.add(problem)
        db.session.flush()
        problem.code = f'P{problem.id:04d}'
        db.session.commit()
        
        # Trigger problem notification
        NotificationEvents.on_problem_created(problem.id)
        
        print("2. Create Business Case → Approve → Notify PM")
        business_case = BusinessCase(
            problem_id=problem.id,
            title='Integration Test Business Case',
            description='Testing complete workflow',
            cost_estimate=100000.0,
            benefit_estimate=200000.0,
            created_by=manager.id,
            case_type=CaseTypeEnum.Reactive,
            case_depth=CaseDepthEnum.Full
        )
        db.session.add(business_case)
        db.session.flush()
        business_case.code = f'C{business_case.id:04d}'
        business_case.calculate_roi()
        business_case.status = StatusEnum.Resolved  # Simulate approval
        db.session.commit()
        
        # Trigger approval notification
        NotificationEvents.on_business_case_approved(business_case.id, pm.id)
        
        print("3. Create Project → Notify PM")
        project = Project(
            name='Integration Test Project',
            description='Testing complete workflow',
            budget=business_case.cost_estimate,
            status=StatusEnum.Open,
            priority=PriorityEnum.High,
            business_case_id=business_case.id,
            project_manager_id=pm.id,
            department_id=dept.id,
            created_by=manager.id
        )
        db.session.add(project)
        db.session.flush()
        project.code = f'PRJ{project.id:04d}'
        db.session.commit()
        
        # Trigger project notification
        NotificationEvents.on_project_created(project.id)
        
        print("4. Create Milestones → Check Due Dates")
        milestone = ProjectMilestone(
            project_id=project.id,
            name='Integration Test Milestone',
            description='Testing milestone notifications',
            due_date=date.today() + timedelta(days=1),
            owner_id=pm.id,
            completed=False
        )
        db.session.add(milestone)
        db.session.commit()
        
        # Trigger milestone notification
        NotificationEvents.on_milestone_due_soon(milestone.id, days_ahead=1)
        
        # Verify complete workflow
        final_notifications = Notification.query.all()
        print(f"\n✓ Complete workflow generated {len(final_notifications)} notifications")
        
        # Check notifications per user
        manager_notifs = Notification.query.filter_by(user_id=manager.id).count()
        pm_notifs = Notification.query.filter_by(user_id=pm.id).count()
        
        print(f"✓ Manager received: {manager_notifs} notifications")
        print(f"✓ PM received: {pm_notifs} notifications")
        
        assert manager_notifs > 0
        assert pm_notifs > 0
        
        return True


def run_comprehensive_notification_tests():
    """Run all notification system tests"""
    print("🧪 Running Comprehensive Notification System Tests")
    print("=" * 60)
    
    try:
        # Test 1: Model functionality
        template, notification = test_notification_models()
        
        # Test 2: Service layer
        service = test_notification_service()
        
        # Test 3: Event hooks
        test_event_hooks()
        
        # Test 4: Batch jobs
        test_batch_notification_jobs()
        
        # Test 5: Statistics
        stats = test_notification_statistics()
        
        # Test 6: End-to-end integration
        test_notification_integration()
        
        print(f"\n🎉 All Notification System Tests Completed Successfully!")
        print("=" * 60)
        print("✅ Notification Models: Working")
        print("✅ Notification Service: Working")
        print("✅ Event Hooks: Working")
        print("✅ Batch Jobs: Working")
        print("✅ Statistics: Working")
        print("✅ End-to-End Integration: Working")
        print("\n📊 Final Statistics:")
        print(f"  Total Notifications: {stats['total_notifications']}")
        print(f"  Notification Templates: {stats['template_count']}")
        print(f"  Event Types Covered: {len(stats['event_stats'])}")
        print(f"  Users with Notifications: {len(stats['user_stats'])}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_comprehensive_notification_tests()
    exit(0 if success else 1)