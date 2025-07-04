"""
Comprehensive test suite for Admin Center functionality
Tests authentication, CRUD operations, audit logging, and role-based access control
"""
import pytest
import json
from datetime import datetime
from flask import url_for
from models import User, Setting, RolePermission, WorkflowTemplate, AuditLog, RoleEnum, db
from auth.stateless_auth import create_jwt_token

class TestAdminCenterAccess:
    """Test authentication and authorization for admin routes"""
    
    def test_admin_dashboard_requires_admin_role(self, client, sample_users):
        """Test that only Admin users can access admin dashboard"""
        admin_user = next(u for u in sample_users if u.role == RoleEnum.Admin)
        staff_user = next(u for u in sample_users if u.role == RoleEnum.Staff)
        
        # Test admin access - should succeed
        admin_token = create_jwt_token(admin_user.id)
        client.set_cookie('auth_token', admin_token)
        
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # Test non-admin access - should be denied
        staff_token = create_jwt_token(staff_user.id)
        client.set_cookie('auth_token', staff_token)
        
        response = client.get('/admin/')
        assert response.status_code == 302  # Redirect due to access denied
        
        # Test unauthenticated access - should be denied
        client.delete_cookie('auth_token')
        response = client.get('/admin/')
        assert response.status_code == 302

    def test_all_admin_routes_require_admin_role(self, client, sample_users):
        """Test that all admin routes require Admin role"""
        admin_user = next(u for u in sample_users if u.role == RoleEnum.Admin)
        staff_user = next(u for u in sample_users if u.role == RoleEnum.Staff)
        
        admin_routes = [
            '/admin/',
            '/admin/settings',
            '/admin/roles',
            '/admin/workflows',
            '/admin/audit-logs',
            '/admin/users'
        ]
        
        # Test admin access
        admin_token = create_jwt_token(admin_user.id)
        client.set_cookie('auth_token', admin_token)
        
        for route in admin_routes:
            response = client.get(route)
            assert response.status_code == 200, f"Admin should access {route}"
        
        # Test non-admin access
        staff_token = create_jwt_token(staff_user.id)
        client.set_cookie('auth_token', staff_token)
        
        for route in admin_routes:
            response = client.get(route)
            assert response.status_code == 302, f"Non-admin should be denied {route}"

class TestSettingsCRUD:
    """Test Settings management with audit logging"""
    
    def test_create_setting_with_audit_log(self, client, admin_user):
        """Test creating a new setting and verify audit log"""
        token = create_jwt_token(admin_user.id)
        client.set_cookie('auth_token', token)
        
        # Get initial counts
        initial_settings = Setting.query.count()
        initial_logs = AuditLog.query.count()
        
        # Create new setting
        response = client.post('/admin/settings', data={
            'setting_key': 'TEST_SETTING',
            'value': 'test_value',
            'description': 'Test setting description'
        })
        
        # Verify redirect (successful creation)
        assert response.status_code == 302
        
        # Verify setting was created
        setting = Setting.query.get('TEST_SETTING')
        assert setting is not None
        assert setting.value == 'test_value'
        assert setting.description == 'Test setting description'
        assert Setting.query.count() == initial_settings + 1
        
        # Verify audit log was created
        audit_logs = AuditLog.query.filter_by(user_id=admin_user.id).all()
        latest_log = max(audit_logs, key=lambda x: x.timestamp)
        assert latest_log.action == 'Updated setting TEST_SETTING'
        assert latest_log.target == 'Setting'
        assert latest_log.target_id == 'TEST_SETTING'
        assert 'test_value' in str(latest_log.details)

    def test_update_setting_with_audit_log(self, client, admin_user):
        """Test updating an existing setting and verify audit log"""
        # Create a test setting first
        test_setting = Setting(
            key='UPDATE_TEST',
            value='original_value',
            description='Original description'
        )
        db.session.add(test_setting)
        db.session.commit()
        
        token = create_jwt_token(admin_user.id)
        client.set_cookie('auth_token', token)
        
        initial_logs = AuditLog.query.count()
        
        # Update the setting
        response = client.post('/admin/settings', data={
            'setting_key': 'UPDATE_TEST',
            'value': 'updated_value',
            'description': 'Updated description'
        })
        
        assert response.status_code == 302
        
        # Verify setting was updated
        updated_setting = Setting.query.get('UPDATE_TEST')
        assert updated_setting.value == 'updated_value'
        assert updated_setting.description == 'Updated description'
        
        # Verify audit log was created
        audit_logs = AuditLog.query.filter_by(user_id=admin_user.id).all()
        latest_log = max(audit_logs, key=lambda x: x.timestamp)
        assert latest_log.action == 'Updated setting UPDATE_TEST'
        assert latest_log.details['old_value'] == 'original_value'
        assert latest_log.details['new_value'] == 'updated_value'

    def test_delete_setting_with_audit_log(self, client, admin_user):
        """Test deleting a setting and verify audit log"""
        # Create a test setting first
        test_setting = Setting(
            key='DELETE_TEST',
            value='delete_me',
            description='To be deleted'
        )
        db.session.add(test_setting)
        db.session.commit()
        
        token = create_jwt_token(admin_user.id)
        client.set_cookie('auth_token', token)
        
        initial_count = Setting.query.count()
        
        # Delete the setting
        response = client.post('/admin/settings/DELETE_TEST/delete')
        assert response.status_code == 302
        
        # Verify setting was deleted
        assert Setting.query.get('DELETE_TEST') is None
        assert Setting.query.count() == initial_count - 1
        
        # Verify audit log was created
        audit_logs = AuditLog.query.filter_by(user_id=admin_user.id).all()
        latest_log = max(audit_logs, key=lambda x: x.timestamp)
        assert latest_log.action == 'Deleted setting DELETE_TEST'
        assert latest_log.target == 'Setting'
        assert latest_log.details['value'] == 'delete_me'

class TestRolePermissionMatrix:
    """Test role permission management"""
    
    def test_create_role_permission(self, client, admin_user):
        """Test creating a role permission and verify in database"""
        token = create_jwt_token(admin_user.id)
        client.set_cookie('auth_token', token)
        
        initial_count = RolePermission.query.count()
        
        # Create new permission
        response = client.post('/admin/roles', data={
            'role': 'Staff',
            'module': 'TestModule',
            'can_create': 'on',
            'can_read': 'on',
            'can_update': '',
            'can_delete': ''
        })
        
        assert response.status_code == 302
        
        # Verify permission was created
        permission = RolePermission.query.filter_by(
            role=RoleEnum.Staff, 
            module='TestModule'
        ).first()
        assert permission is not None
        assert permission.can_create is True
        assert permission.can_read is True
        assert permission.can_update is False
        assert permission.can_delete is False
        
        # Verify audit log
        audit_logs = AuditLog.query.filter_by(user_id=admin_user.id).all()
        latest_log = max(audit_logs, key=lambda x: x.timestamp)
        assert 'Created permission for Staff role on TestModule module' in latest_log.action
        assert latest_log.target == 'RolePermission'

    def test_update_role_permissions_matrix(self, client, admin_user):
        """Test updating all permissions for a role"""
        token = create_jwt_token(admin_user.id)
        client.set_cookie('auth_token', token)
        
        # Update all permissions for Manager role
        form_data = {
            'Problem_create': 'on',
            'Problem_read': 'on',
            'Problem_update': 'on',
            'Problem_delete': '',
            'BusinessCase_create': 'on',
            'BusinessCase_read': 'on',
            'BusinessCase_update': '',
            'BusinessCase_delete': '',
            'Project_create': '',
            'Project_read': 'on',
            'Project_update': '',
            'Project_delete': '',
            'Department_create': '',
            'Department_read': 'on',
            'Department_update': 'on',
            'Department_delete': '',
            'User_create': '',
            'User_read': 'on',
            'User_update': '',
            'User_delete': '',
            'Report_create': 'on',
            'Report_read': 'on',
            'Report_update': '',
            'Report_delete': ''
        }
        
        response = client.post('/admin/roles/Manager/permissions', data=form_data)
        assert response.status_code == 302
        
        # Verify permissions were updated
        manager_permissions = RolePermission.query.filter_by(role=RoleEnum.Manager).all()
        permission_dict = {p.module: p for p in manager_permissions}
        
        # Check specific permissions
        assert permission_dict['Problem'].can_create is True
        assert permission_dict['Problem'].can_read is True
        assert permission_dict['Problem'].can_update is True
        assert permission_dict['Problem'].can_delete is False
        
        assert permission_dict['BusinessCase'].can_create is True
        assert permission_dict['BusinessCase'].can_read is True
        assert permission_dict['BusinessCase'].can_update is False
        assert permission_dict['BusinessCase'].can_delete is False
        
        # Verify audit log
        audit_logs = AuditLog.query.filter_by(user_id=admin_user.id).all()
        latest_log = max(audit_logs, key=lambda x: x.timestamp)
        assert 'Updated all permissions for Manager role' in latest_log.action

class TestWorkflowTemplates:
    """Test workflow template management with JSON handling"""
    
    def test_create_workflow_template_with_json(self, client, admin_user):
        """Test creating workflow template with JSON definition"""
        token = create_jwt_token(admin_user.id)
        client.set_cookie('auth_token', token)
        
        initial_count = WorkflowTemplate.query.count()
        
        workflow_definition = {
            "steps": [
                {
                    "id": "step1",
                    "name": "Initial Review",
                    "type": "approval",
                    "assignee": "manager",
                    "conditions": {"amount": "> 1000"}
                },
                {
                    "id": "step2",
                    "name": "Final Approval", 
                    "type": "approval",
                    "assignee": "director",
                    "depends_on": ["step1"]
                }
            ]
        }
        
        response = client.post('/admin/workflows', data={
            'name': 'Test Approval Workflow',
            'description': 'Test workflow for approval process',
            'definition': json.dumps(workflow_definition)
        })
        
        assert response.status_code == 302
        
        # Verify template was created
        template = WorkflowTemplate.query.filter_by(name='Test Approval Workflow').first()
        assert template is not None
        assert template.description == 'Test workflow for approval process'
        assert template.is_active is True
        assert template.created_by == admin_user.id
        
        # Verify JSON definition was stored correctly
        assert 'steps' in template.definition
        assert len(template.definition['steps']) == 2
        assert template.definition['steps'][0]['name'] == 'Initial Review'
        assert template.definition['steps'][1]['depends_on'] == ['step1']
        
        # Verify audit log
        audit_logs = AuditLog.query.filter_by(user_id=admin_user.id).all()
        latest_log = max(audit_logs, key=lambda x: x.timestamp)
        assert 'Created workflow template Test Approval Workflow' in latest_log.action

    def test_update_workflow_template_json(self, client, admin_user):
        """Test updating workflow template JSON definition"""
        # Create a test template first
        initial_definition = {"steps": [{"id": "step1", "name": "Basic Step"}]}
        test_template = WorkflowTemplate(
            name='Update Test Template',
            description='For testing updates',
            definition=initial_definition,
            created_by=admin_user.id
        )
        db.session.add(test_template)
        db.session.commit()
        
        token = create_jwt_token(admin_user.id)
        client.set_cookie('auth_token', token)
        
        # Update with new JSON definition
        updated_definition = {
            "steps": [
                {"id": "step1", "name": "Updated Step", "type": "review"},
                {"id": "step2", "name": "New Step", "type": "approval"}
            ],
            "version": "2.0"
        }
        
        response = client.post(f'/admin/workflows/{test_template.id}', data={
            'name': 'Updated Template Name',
            'description': 'Updated description',
            'is_active': 'on',
            'definition': json.dumps(updated_definition)
        })
        
        assert response.status_code == 302
        
        # Verify template was updated
        updated_template = WorkflowTemplate.query.get(test_template.id)
        assert updated_template.name == 'Updated Template Name'
        assert updated_template.description == 'Updated description'
        assert updated_template.is_active is True
        
        # Verify JSON definition was updated
        assert updated_template.definition['version'] == '2.0'
        assert len(updated_template.definition['steps']) == 2
        assert updated_template.definition['steps'][0]['name'] == 'Updated Step'
        assert updated_template.definition['steps'][1]['type'] == 'approval'

    def test_invalid_json_workflow_definition(self, client, admin_user):
        """Test that invalid JSON in workflow definition is handled"""
        token = create_jwt_token(admin_user.id)
        client.set_cookie('auth_token', token)
        
        # Attempt to create workflow with invalid JSON
        response = client.post('/admin/workflows', data={
            'name': 'Invalid JSON Template',
            'description': 'This should fail',
            'definition': '{"invalid": json syntax}'  # Invalid JSON
        })
        
        # Should not redirect (stays on form with error)
        assert response.status_code == 200
        assert b'Invalid JSON' in response.data
        
        # Verify template was not created
        template = WorkflowTemplate.query.filter_by(name='Invalid JSON Template').first()
        assert template is None

class TestAuditLogViewing:
    """Test audit log viewing and pagination"""
    
    def test_audit_log_pagination(self, client, admin_user):
        """Test that audit logs are paginated correctly"""
        token = create_jwt_token(admin_user.id)
        client.set_cookie('auth_token', token)
        
        # Create multiple audit log entries
        for i in range(150):  # More than one page (100 per page)
            audit_log = AuditLog(
                user_id=admin_user.id,
                action=f'Test Action {i}',
                target='TestTarget',
                target_id=i,
                ip_address='127.0.0.1',
                user_agent='Test Agent'
            )
            db.session.add(audit_log)
        db.session.commit()
        
        # Test first page
        response = client.get('/admin/audit-logs')
        assert response.status_code == 200
        assert b'Test Action' in response.data
        
        # Test pagination exists
        assert b'page=2' in response.data or b'Next' in response.data
        
        # Test second page
        response = client.get('/admin/audit-logs?page=2')
        assert response.status_code == 200
        assert b'Test Action' in response.data
        
        # Test filtering by user
        response = client.get(f'/admin/audit-logs?user_id={admin_user.id}')
        assert response.status_code == 200
        
        # Test filtering by action
        response = client.get('/admin/audit-logs?action=Test')
        assert response.status_code == 200

    def test_audit_log_filtering(self, client, admin_user, sample_users):
        """Test audit log filtering functionality"""
        token = create_jwt_token(admin_user.id)
        client.set_cookie('auth_token', token)
        
        other_user = next(u for u in sample_users if u.id != admin_user.id)
        
        # Create audit logs for different users and actions
        admin_log = AuditLog(
            user_id=admin_user.id,
            action='ADMIN_ACTION',
            target='AdminTarget',
            ip_address='127.0.0.1'
        )
        
        other_log = AuditLog(
            user_id=other_user.id,
            action='USER_ACTION',
            target='UserTarget',
            ip_address='192.168.1.1'
        )
        
        db.session.add_all([admin_log, other_log])
        db.session.commit()
        
        # Test filtering by specific user
        response = client.get(f'/admin/audit-logs?user_id={admin_user.id}')
        assert response.status_code == 200
        assert b'ADMIN_ACTION' in response.data
        assert b'USER_ACTION' not in response.data
        
        # Test filtering by action
        response = client.get('/admin/audit-logs?action=ADMIN')
        assert response.status_code == 200
        assert b'ADMIN_ACTION' in response.data
        assert b'USER_ACTION' not in response.data
        
        # Test date range filtering
        today = datetime.now().strftime('%Y-%m-%d')
        response = client.get(f'/admin/audit-logs?date_from={today}&date_to={today}')
        assert response.status_code == 200

class TestAdminIntegration:
    """Integration tests for admin functionality"""
    
    def test_complete_admin_workflow(self, client, admin_user):
        """Test complete admin workflow: settings, permissions, workflows, audit"""
        token = create_jwt_token(admin_user.id)
        client.set_cookie('auth_token', token)
        
        # 1. Create a setting
        response = client.post('/admin/settings', data={
            'setting_key': 'WORKFLOW_TEST',
            'value': 'enabled',
            'description': 'Test workflow setting'
        })
        assert response.status_code == 302
        
        # 2. Create a permission
        response = client.post('/admin/roles', data={
            'role': 'Manager',
            'module': 'WorkflowTest',
            'can_create': 'on',
            'can_read': 'on'
        })
        assert response.status_code == 302
        
        # 3. Create a workflow template
        workflow_def = {"steps": [{"id": "test", "name": "Test Step"}]}
        response = client.post('/admin/workflows', data={
            'name': 'Integration Test Workflow',
            'description': 'Integration test',
            'definition': json.dumps(workflow_def)
        })
        assert response.status_code == 302
        
        # 4. Verify all operations created audit logs
        audit_logs = AuditLog.query.filter_by(user_id=admin_user.id).order_by(AuditLog.timestamp.desc()).limit(3).all()
        
        actions = [log.action for log in audit_logs]
        assert any('workflow template' in action.lower() for action in actions)
        assert any('permission' in action.lower() for action in actions)
        assert any('setting' in action.lower() for action in actions)
        
        # 5. View audit logs to ensure they're accessible
        response = client.get('/admin/audit-logs')
        assert response.status_code == 200
        assert b'Integration Test Workflow' in response.data or b'WORKFLOW_TEST' in response.data

    def test_admin_dashboard_displays_statistics(self, client, admin_user):
        """Test that admin dashboard shows system statistics"""
        token = create_jwt_token(admin_user.id)
        client.set_cookie('auth_token', token)
        
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # Check for key dashboard elements
        assert b'Users' in response.data
        assert b'Settings' in response.data
        assert b'Recent Activity' in response.data
        assert b'System Health' in response.data

# Fixtures for testing
@pytest.fixture
def admin_user(app):
    """Create an admin user for testing"""
    with app.app_context():
        admin = User(
            name="Admin Test User",
            email="admin@test.com",
            role=RoleEnum.Admin,
            password_hash="hashed_password",
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        return admin

@pytest.fixture
def sample_users(app):
    """Create sample users with different roles"""
    with app.app_context():
        users = [
            User(name="Admin User", email="admin@test.com", role=RoleEnum.Admin, password_hash="hash", is_active=True),
            User(name="Staff User", email="staff@test.com", role=RoleEnum.Staff, password_hash="hash", is_active=True),
            User(name="Manager User", email="manager@test.com", role=RoleEnum.Manager, password_hash="hash", is_active=True),
            User(name="BA User", email="ba@test.com", role=RoleEnum.BA, password_hash="hash", is_active=True)
        ]
        
        for user in users:
            db.session.add(user)
        db.session.commit()
        return users