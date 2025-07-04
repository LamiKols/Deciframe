"""
Test Admin User Management functionality
Tests for user CRUD operations, access control, and security features
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, Department, RoleEnum
from stateless_auth import create_jwt_token
from werkzeug.security import check_password_hash

class TestAdminUsers:
    """Test suite for admin user management"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.client = self.app.test_client()
        
        with self.app.app_context():
            # Ensure we have a test department
            self.test_dept = Department.query.filter_by(name='Test Department').first()
            if not self.test_dept:
                self.test_dept = Department(name='Test Department', level=1)
                db.session.add(self.test_dept)
                db.session.commit()
            
            # Get admin user
            self.admin_user = User.query.filter_by(role=RoleEnum.Admin).first()
            assert self.admin_user is not None, "Admin user must exist for tests"
            
            # Create non-admin user for access control tests
            self.staff_user = User.query.filter_by(email='staff@test.com').first()
            if not self.staff_user:
                self.staff_user = User(
                    name='Staff User',
                    email='staff@test.com',
                    role=RoleEnum.Staff,
                    dept_id=self.test_dept.id,
                    is_active=True
                )
                self.staff_user.set_password('testpass123')
                db.session.add(self.staff_user)
                db.session.commit()
            
            # Generate auth tokens
            self.admin_token = create_jwt_token(self.admin_user.id)
            self.staff_token = create_jwt_token(self.staff_user.id)
    
    def test_admin_can_list_users(self):
        """Test that admin can access user list"""
        with self.app.app_context():
            response = self.client.get(f'/admin/users?auth_token={self.admin_token}')
            assert response.status_code == 200
            assert b'User Management' in response.data
            assert self.admin_user.email.encode() in response.data
    
    def test_non_admin_gets_403_on_user_list(self):
        """Test that non-admin users cannot access user list"""
        with self.app.app_context():
            response = self.client.get(f'/admin/users?auth_token={self.staff_token}')
            assert response.status_code == 302  # Redirect to login/index
            
            # Follow redirect to check final status
            response = self.client.get(f'/admin/users?auth_token={self.staff_token}', 
                                     follow_redirects=True)
            assert b'Admin access required' in response.data or b'Access denied' in response.data
    
    def test_admin_can_create_user(self):
        """Test that admin can create new users"""
        with self.app.app_context():
            # First get the creation form
            response = self.client.get(f'/admin/users/new?auth_token={self.admin_token}')
            assert response.status_code == 200
            assert b'Create User' in response.data
            
            # Submit new user data
            user_data = {
                'name': 'Test New User',
                'email': 'testnew@deciframe.com',
                'department': self.test_dept.id,
                'role': 'Staff',
                'password': 'password123',
                'is_active': True
            }
            
            response = self.client.post(f'/admin/users/new?auth_token={self.admin_token}',
                                      data=user_data, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'created successfully' in response.data
            
            # Verify user was created in database
            new_user = User.query.filter_by(email='testnew@deciframe.com').first()
            assert new_user is not None
            assert new_user.name == 'Test New User'
            assert new_user.role == RoleEnum.Staff
            assert new_user.dept_id == self.test_dept.id
            assert new_user.is_active == True
            
            # Clean up
            db.session.delete(new_user)
            db.session.commit()
    
    def test_non_admin_cannot_create_user(self):
        """Test that non-admin users cannot create users"""
        with self.app.app_context():
            response = self.client.get(f'/admin/users/new?auth_token={self.staff_token}')
            assert response.status_code == 302  # Redirect
            
            # Try to submit creation data anyway
            user_data = {
                'name': 'Unauthorized User',
                'email': 'unauthorized@test.com',
                'department': self.test_dept.id,
                'role': 'Staff',
                'password': 'password123',
                'is_active': True
            }
            
            response = self.client.post(f'/admin/users/new?auth_token={self.staff_token}',
                                      data=user_data, follow_redirects=True)
            
            # Verify user was NOT created
            unauthorized_user = User.query.filter_by(email='unauthorized@test.com').first()
            assert unauthorized_user is None
    
    def test_admin_can_edit_user(self):
        """Test that admin can edit existing users"""
        with self.app.app_context():
            # Create a test user to edit
            test_user = User(
                name='Edit Test User',
                email='edittest@deciframe.com',
                role=RoleEnum.Staff,
                dept_id=self.test_dept.id,
                is_active=True
            )
            test_user.set_password('originalpass')
            db.session.add(test_user)
            db.session.commit()
            
            # Get edit form
            response = self.client.get(f'/admin/users/{test_user.id}/edit?auth_token={self.admin_token}')
            assert response.status_code == 200
            assert b'Update User' in response.data
            assert test_user.email.encode() in response.data
            
            # Submit updated data
            update_data = {
                'name': 'Updated Test User',
                'email': 'edittest@deciframe.com',
                'department': self.test_dept.id,
                'role': 'Manager',
                'is_active': True
            }
            
            response = self.client.post(f'/admin/users/{test_user.id}/edit?auth_token={self.admin_token}',
                                      data=update_data, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'updated successfully' in response.data
            
            # Verify changes in database
            db.session.refresh(test_user)
            assert test_user.name == 'Updated Test User'
            assert test_user.role == RoleEnum.Manager
            
            # Clean up
            db.session.delete(test_user)
            db.session.commit()
    
    def test_non_admin_cannot_edit_user(self):
        """Test that non-admin users cannot edit users"""
        with self.app.app_context():
            response = self.client.get(f'/admin/users/{self.admin_user.id}/edit?auth_token={self.staff_token}')
            assert response.status_code == 302  # Redirect
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed"""
        with self.app.app_context():
            # Create user with password
            user_data = {
                'name': 'Password Test User',
                'email': 'passtest@deciframe.com',
                'department': self.test_dept.id,
                'role': 'Staff',
                'password': 'mysecretpassword123',
                'is_active': True
            }
            
            response = self.client.post(f'/admin/users/new?auth_token={self.admin_token}',
                                      data=user_data, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Verify password is hashed
            new_user = User.query.filter_by(email='passtest@deciframe.com').first()
            assert new_user is not None
            assert new_user.password_hash != 'mysecretpassword123'  # Should be hashed
            assert new_user.password_hash is not None
            assert len(new_user.password_hash) > 50  # Hashed passwords are longer
            
            # Verify password check works
            assert new_user.check_password('mysecretpassword123') == True
            assert new_user.check_password('wrongpassword') == False
            
            # Clean up
            db.session.delete(new_user)
            db.session.commit()
    
    def test_is_active_toggling(self):
        """Test user status toggling functionality"""
        with self.app.app_context():
            # Create test user
            test_user = User(
                name='Toggle Test User',
                email='toggletest@deciframe.com',
                role=RoleEnum.Staff,
                dept_id=self.test_dept.id,
                is_active=True
            )
            test_user.set_password('testpass')
            db.session.add(test_user)
            db.session.commit()
            
            # Verify initial state
            assert test_user.is_active == True
            
            # Toggle status (deactivate)
            response = self.client.post(f'/admin/users/{test_user.id}/toggle-status?auth_token={self.admin_token}',
                                      follow_redirects=True)
            
            assert response.status_code == 200
            
            # Verify status changed
            db.session.refresh(test_user)
            assert test_user.is_active == False
            
            # Toggle again (reactivate)
            response = self.client.post(f'/admin/users/{test_user.id}/toggle-status?auth_token={self.admin_token}',
                                      follow_redirects=True)
            
            assert response.status_code == 200
            
            # Verify status changed back
            db.session.refresh(test_user)
            assert test_user.is_active == True
            
            # Clean up
            db.session.delete(test_user)
            db.session.commit()
    
    def test_non_admin_cannot_toggle_status(self):
        """Test that non-admin users cannot toggle user status"""
        with self.app.app_context():
            original_status = self.admin_user.is_active
            
            response = self.client.post(f'/admin/users/{self.admin_user.id}/toggle-status?auth_token={self.staff_token}',
                                      follow_redirects=True)
            
            # Verify admin status unchanged
            db.session.refresh(self.admin_user)
            assert self.admin_user.is_active == original_status
    
    def test_duplicate_email_validation(self):
        """Test that duplicate email addresses are rejected"""
        with self.app.app_context():
            user_data = {
                'name': 'Duplicate Email User',
                'email': self.admin_user.email,  # Use existing admin email
                'department': self.test_dept.id,
                'role': 'Staff',
                'password': 'password123',
                'is_active': True
            }
            
            response = self.client.post(f'/admin/users/new?auth_token={self.admin_token}',
                                      data=user_data, follow_redirects=True)
            
            # Should show error message
            assert b'already exists' in response.data.lower()
            
            # Verify no duplicate user was created
            users_with_email = User.query.filter_by(email=self.admin_user.email).all()
            assert len(users_with_email) == 1  # Only the original admin user
    
    def test_form_validation(self):
        """Test form validation for required fields"""
        with self.app.app_context():
            # Submit incomplete data
            incomplete_data = {
                'name': '',  # Missing name
                'email': 'invalid-email',  # Invalid email format
                'department': '',  # Missing department
                'role': '',  # Missing role
                'password': '123',  # Too short password
                'is_active': True
            }
            
            response = self.client.post(f'/admin/users/new?auth_token={self.admin_token}',
                                      data=incomplete_data)
            
            # Should stay on form page due to validation errors
            assert response.status_code == 200
            assert b'Create User' in response.data
    
    def test_admin_dashboard_access(self):
        """Test admin dashboard access control"""
        with self.app.app_context():
            # Admin should have access
            response = self.client.get(f'/admin?auth_token={self.admin_token}')
            assert response.status_code == 200
            
            # Non-admin should not have access
            response = self.client.get(f'/admin?auth_token={self.staff_token}')
            assert response.status_code == 302  # Redirect
    
    def test_user_search_functionality(self):
        """Test user search and filtering"""
        with self.app.app_context():
            # Test search by name
            response = self.client.get(f'/admin/users?search={self.admin_user.name}&auth_token={self.admin_token}')
            assert response.status_code == 200
            assert self.admin_user.email.encode() in response.data
            
            # Test search by email
            response = self.client.get(f'/admin/users?search={self.admin_user.email}&auth_token={self.admin_token}')
            assert response.status_code == 200
            assert self.admin_user.email.encode() in response.data
            
            # Test filter by role
            response = self.client.get(f'/admin/users?role=Admin&auth_token={self.admin_token}')
            assert response.status_code == 200
            assert self.admin_user.email.encode() in response.data

if __name__ == '__main__':
    pytest.main([__file__, '-v'])