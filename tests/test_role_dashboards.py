"""
Test suite for Role-Scoped Dashboards System
Tests role-specific dashboard routing, content, and authentication
"""
import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import url_for


class TestRoleDashboards:
    """Test Role-Scoped Dashboard functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client with application context"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.test_client() as client:
            with app.app_context():
                # Create test department
                test_dept = Department()
                test_dept.name = "Test Department"
                test_dept.description = "Department for testing"
                db.session.add(test_dept)
                db.session.commit()
                
                # Create test users for each role
                self.test_users = {}
                roles = ['Staff', 'Manager', 'BA', 'PM', 'Director', 'CEO', 'Admin']
                
                for role in roles:
                    user = User()
                    user.name = f"Test {role} User"
                    user.email = f"test_{role.lower()}@example.com"
                    user.role = RoleEnum(role)
                    user.dept_id = test_dept.id
                    user.set_password("testpass123")
                    db.session.add(user)
                    self.test_users[role] = user
                
                db.session.commit()
                yield client
                
                # Cleanup
                db.session.rollback()
    
    def login_user(self, client, email, password="testpass123"):
        """Helper to log in a user"""
        return client.post('/auth/login', data={
            'email': email,
            'password': password,
            'csrf_token': 'test'
        }, follow_redirects=False)
    
    def test_staff_dashboard(self, client):
        """Test Staff role dashboard content and routing"""
        user = self.test_users['Staff']
        
        # Login as staff user
        response = self.login_user(client, user.email)
        
        # Test redirect to dashboard after login
        assert response.status_code == 302
        assert '/dashboard/' in response.location
        
        # Test dashboard home redirects to staff dashboard
        response = client.get('/dashboard/', follow_redirects=False)
        assert response.status_code == 302
        assert '/dashboard/staff' in response.location
        
        # Test staff dashboard content
        response = client.get('/dashboard/staff')
        assert response.status_code == 200
        
        # Verify staff-specific content
        content = response.data.decode()
        assert "Staff Dashboard" in content
        assert "My Problems" in content
        assert "My Business Cases" in content
        assert "Recent Activity" in content
        
    def test_manager_dashboard(self, client):
        """Test Manager role dashboard content and routing"""
        user = self.test_users['Manager']
        
        # Login as manager user
        response = self.login_user(client, user.email)
        
        # Test dashboard home redirects to manager dashboard
        response = client.get('/dashboard/', follow_redirects=False)
        assert response.status_code == 302
        assert '/dashboard/manager' in response.location
        
        # Test manager dashboard content
        response = client.get('/dashboard/manager')
        assert response.status_code == 200
        
        # Verify manager-specific content
        content = response.data.decode()
        assert "Manager Dashboard" in content
        assert "Department Overview" in content
        assert "Team Performance" in content
        assert "Department KPIs" in content
        
    def test_ba_dashboard(self, client):
        """Test Business Analyst role dashboard content and routing"""
        user = self.test_users['BA']
        
        # Login as BA user
        response = self.login_user(client, user.email)
        
        # Test dashboard home redirects to BA dashboard
        response = client.get('/dashboard/', follow_redirects=False)
        assert response.status_code == 302
        assert '/dashboard/ba' in response.location
        
        # Test BA dashboard content
        response = client.get('/dashboard/ba')
        assert response.status_code == 200
        
        # Verify BA-specific content
        content = response.data.decode()
        assert "Business Analyst Dashboard" in content
        assert "Assigned Cases" in content
        assert "Requirements Management" in content
        assert "Analysis Workflow" in content
        
    def test_pm_dashboard(self, client):
        """Test Project Manager role dashboard content and routing"""
        user = self.test_users['PM']
        
        # Login as PM user
        response = self.login_user(client, user.email)
        
        # Test dashboard home redirects to PM dashboard
        response = client.get('/dashboard/', follow_redirects=False)
        assert response.status_code == 302
        assert '/dashboard/pm' in response.location
        
        # Test PM dashboard content
        response = client.get('/dashboard/pm')
        assert response.status_code == 200
        
        # Verify PM-specific content
        content = response.data.decode()
        assert "Project Manager Dashboard" in content
        assert "Active Projects" in content
        assert "Upcoming Milestones" in content
        assert "Project Health" in content
        
    def test_director_dashboard(self, client):
        """Test Director role dashboard content and routing"""
        user = self.test_users['Director']
        
        # Login as Director user
        response = self.login_user(client, user.email)
        
        # Test dashboard home redirects to director dashboard
        response = client.get('/dashboard/', follow_redirects=False)
        assert response.status_code == 302
        assert '/dashboard/director' in response.location
        
        # Test director dashboard content
        response = client.get('/dashboard/director')
        assert response.status_code == 200
        
        # Verify director-specific content
        content = response.data.decode()
        assert "Director Dashboard" in content
        assert "Strategic Overview" in content
        assert "Approval Queue" in content
        assert "High Priority Items" in content
        
    def test_admin_dashboard(self, client):
        """Test Admin role dashboard content and routing"""
        user = self.test_users['Admin']
        
        # Login as Admin user
        response = self.login_user(client, user.email)
        
        # Test dashboard home redirects to admin dashboard
        response = client.get('/dashboard/', follow_redirects=False)
        assert response.status_code == 302
        assert '/dashboard/admin' in response.location
        
        # Test admin dashboard content
        response = client.get('/dashboard/admin')
        assert response.status_code == 200
        
        # Verify admin-specific content
        content = response.data.decode()
        assert "Admin Dashboard" in content
        assert "System Health" in content
        assert "User Management" in content
        assert "System Statistics" in content
        
    def test_unauthorized_dashboard_access(self, client):
        """Test that unauthenticated users cannot access dashboards"""
        # Test dashboard home without login
        response = client.get('/dashboard/')
        assert response.status_code == 302
        assert '/auth/login' in response.location
        
        # Test specific role dashboards without login
        role_paths = ['/dashboard/staff', '/dashboard/manager', '/dashboard/ba', 
                     '/dashboard/pm', '/dashboard/director', '/dashboard/admin']
        
        for path in role_paths:
            response = client.get(path)
            assert response.status_code == 302
            assert '/auth/login' in response.location
    
    def test_dashboard_navigation_integration(self, client):
        """Test that dashboard navigation is properly integrated"""
        user = self.test_users['Staff']
        
        # Login as staff user
        self.login_user(client, user.email)
        
        # Test that navigation includes dashboard link
        response = client.get('/dashboard/staff')
        assert response.status_code == 200
        
        content = response.data.decode()
        assert 'href="/dashboard/"' in content or 'dashboards.dashboard_home' in content
        assert 'Dashboard' in content
        
    def test_role_specific_data_display(self, client):
        """Test that each dashboard displays role-appropriate data"""
        # Test different roles see different content
        test_cases = [
            ('Staff', ['My Problems', 'My Business Cases']),
            ('Manager', ['Department Overview', 'Team Performance']),
            ('BA', ['Assigned Cases', 'Requirements Management']),
            ('PM', ['Active Projects', 'Upcoming Milestones']),
            ('Director', ['Strategic Overview', 'Approval Queue']),
            ('Admin', ['System Health', 'User Management'])
        ]
        
        for role, expected_content in test_cases:
            user = self.test_users[role]
            
            # Login as specific role
            self.login_user(client, user.email)
            
            # Get role-specific dashboard
            response = client.get(f'/dashboard/{role.lower()}')
            assert response.status_code == 200
            
            content = response.data.decode()
            for expected_text in expected_content:
                assert expected_text in content, f"Missing '{expected_text}' in {role} dashboard"
    
    def test_dashboard_helper_functions(self, client):
        """Test that dashboard helper functions work correctly"""
        user = self.test_users['Manager']
        
        # Login as manager to test department KPIs
        self.login_user(client, user.email)
        
        response = client.get('/dashboard/manager')
        assert response.status_code == 200
        
        # Verify that KPI data is displayed (even if zeros for test data)
        content = response.data.decode()
        assert "Problems" in content
        assert "Cases" in content
        assert "Projects" in content
        assert "ROI" in content
    
    def test_login_redirect_to_dashboard(self, client):
        """Test that login redirects to appropriate dashboard"""
        user = self.test_users['Staff']
        
        # Test login redirect
        response = self.login_user(client, user.email)
        assert response.status_code == 302
        
        # Should redirect to dashboard home
        assert '/dashboard/' in response.location
        
        # Follow redirect to verify it goes to staff dashboard
        response = client.get('/dashboard/', follow_redirects=True)
        assert response.status_code == 200
        
        # Final URL should be staff dashboard
        content = response.data.decode()
        assert "Staff Dashboard" in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])