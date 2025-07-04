"""
Test suite for Organizational Structure functionality
Tests CSV import, hierarchy display, and editing operations
"""

import pytest
import json
import tempfile
import os
from io import StringIO
import pandas as pd

from app import app, db
from models import User, OrgUnit


class TestOrgStructure:
    
    @pytest.fixture
    def client(self):
        """Create test client with in-memory database"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                
                # Create test admin user
                admin_user = User(
                    email='admin@test.com',
                    first_name='Test',
                    last_name='Admin',
                    role='Admin',
                    is_active=True
                )
                admin_user.set_password('password123')
                db.session.add(admin_user)
                
                # Create test manager users
                manager1 = User(
                    email='manager1@test.com',
                    first_name='Manager',
                    last_name='One',
                    role='Manager',
                    is_active=True
                )
                manager1.set_password('password123')
                db.session.add(manager1)
                
                manager2 = User(
                    email='manager2@test.com',
                    first_name='Manager',
                    last_name='Two',
                    role='Manager',
                    is_active=True
                )
                manager2.set_password('password123')
                db.session.add(manager2)
                
                db.session.commit()
                
                yield client
    
    def get_auth_token(self, client, email='admin@test.com'):
        """Get JWT authentication token for testing"""
        response = client.post('/auth/login', json={
            'email': email,
            'password': 'password123'
        })
        return response.json.get('token')
    
    def test_csv_import_creates_org_units(self, client):
        """Test CSV import creates OrgUnit rows with correct parent and manager links"""
        
        # Create CSV data
        csv_data = """name,parent_name,manager_email
Test Corporation,,admin@test.com
IT Department,Test Corporation,manager1@test.com
Development Team,IT Department,manager2@test.com
Operations Team,IT Department,manager1@test.com"""
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_file.write(csv_data)
            temp_file_path = temp_file.name
        
        try:
            # Get authentication token
            token = self.get_auth_token(client)
            
            # Import CSV via POST request
            with open(temp_file_path, 'rb') as csv_file:
                response = client.post(
                    '/admin/org-structure/import',
                    data={'file': (csv_file, 'test_org.csv')},
                    headers={'Authorization': f'Bearer {token}'},
                    content_type='multipart/form-data'
                )
            
            # Verify successful import
            assert response.status_code in [200, 302], f"Import failed with status {response.status_code}"
            
            # Verify database records
            with app.app_context():
                # Check total units created
                total_units = OrgUnit.query.count()
                assert total_units == 4, f"Expected 4 units, got {total_units}"
                
                # Check root unit
                root_unit = OrgUnit.query.filter_by(name='Test Corporation', parent_id=None).first()
                assert root_unit is not None, "Root unit 'Test Corporation' not found"
                assert root_unit.manager.email == 'admin@test.com', "Root unit manager incorrect"
                
                # Check IT Department
                it_dept = OrgUnit.query.filter_by(name='IT Department').first()
                assert it_dept is not None, "IT Department not found"
                assert it_dept.parent == root_unit, "IT Department parent link incorrect"
                assert it_dept.manager.email == 'manager1@test.com', "IT Department manager incorrect"
                
                # Check Development Team
                dev_team = OrgUnit.query.filter_by(name='Development Team').first()
                assert dev_team is not None, "Development Team not found"
                assert dev_team.parent == it_dept, "Development Team parent link incorrect"
                assert dev_team.manager.email == 'manager2@test.com', "Development Team manager incorrect"
                
                # Check Operations Team
                ops_team = OrgUnit.query.filter_by(name='Operations Team').first()
                assert ops_team is not None, "Operations Team not found"
                assert ops_team.parent == it_dept, "Operations Team parent link incorrect"
                assert ops_team.manager.email == 'manager1@test.com', "Operations Team manager incorrect"
                
                # Verify hierarchy relationships
                assert len(root_unit.children) == 1, "Root unit should have 1 child"
                assert len(it_dept.children) == 2, "IT Department should have 2 children"
                assert len(dev_team.children) == 0, "Development Team should have no children"
                assert len(ops_team.children) == 0, "Operations Team should have no children"
        
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
    
    def test_org_structure_hierarchy_display(self, client):
        """Test GET /admin/org-structure returns nested JSON/HTML matching the hierarchy"""
        
        # Create test organizational structure
        with app.app_context():
            # Create users for managers
            admin_user = User.query.filter_by(email='admin@test.com').first()
            manager1 = User.query.filter_by(email='manager1@test.com').first()
            
            # Create organizational units
            root_unit = OrgUnit(name='Test Corp', manager=admin_user)
            db.session.add(root_unit)
            db.session.flush()  # Get ID for parent reference
            
            child_unit = OrgUnit(name='IT Division', parent=root_unit, manager=manager1)
            db.session.add(child_unit)
            db.session.flush()
            
            grandchild_unit = OrgUnit(name='Development', parent=child_unit, manager=manager1)
            db.session.add(grandchild_unit)
            
            db.session.commit()
        
        # Get authentication token
        token = self.get_auth_token(client)
        
        # Request org structure page
        response = client.get(
            '/admin/org-structure',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        # Verify successful response
        assert response.status_code == 200, f"Org structure page failed with status {response.status_code}"
        
        # Verify HTML content contains organizational units
        html_content = response.data.decode('utf-8')
        assert 'Test Corp' in html_content, "Root unit not found in HTML"
        assert 'IT Division' in html_content, "Child unit not found in HTML"
        assert 'Development' in html_content, "Grandchild unit not found in HTML"
        
        # Verify JavaScript data structure is present
        assert 'const roots =' in html_content, "JavaScript roots data not found"
        assert 'const allUnits =' in html_content, "JavaScript allUnits data not found"
        
        # Extract and validate JSON structure
        import re
        roots_match = re.search(r'const roots = (\[.*?\]);', html_content, re.DOTALL)
        assert roots_match, "Could not extract roots JSON from HTML"
        
        roots_json = json.loads(roots_match.group(1))
        assert len(roots_json) == 1, "Should have exactly one root unit"
        
        root_data = roots_json[0]
        assert root_data['name'] == 'Test Corp', "Root unit name incorrect in JSON"
        assert root_data['manager']['email'] == 'admin@test.com', "Root manager incorrect in JSON"
        assert len(root_data['children']) == 1, "Root should have one child in JSON"
        
        child_data = root_data['children'][0]
        assert child_data['name'] == 'IT Division', "Child unit name incorrect in JSON"
        assert child_data['manager']['email'] == 'manager1@test.com', "Child manager incorrect in JSON"
        assert len(child_data['children']) == 1, "Child should have one grandchild in JSON"
        
        grandchild_data = child_data['children'][0]
        assert grandchild_data['name'] == 'Development', "Grandchild unit name incorrect in JSON"
        assert len(grandchild_data['children']) == 0, "Grandchild should have no children in JSON"
    
    def test_edit_org_unit_updates_database(self, client):
        """Test editing a unit via the edit route updates the DB"""
        
        # Create test organizational structure
        with app.app_context():
            admin_user = User.query.filter_by(email='admin@test.com').first()
            manager1 = User.query.filter_by(email='manager1@test.com').first()
            manager2 = User.query.filter_by(email='manager2@test.com').first()
            
            # Create parent and child units
            parent_unit = OrgUnit(name='Parent Unit', manager=admin_user)
            db.session.add(parent_unit)
            db.session.flush()
            
            target_unit = OrgUnit(name='Target Unit', manager=manager1)
            db.session.add(target_unit)
            db.session.flush()
            
            new_parent_unit = OrgUnit(name='New Parent', manager=manager2)
            db.session.add(new_parent_unit)
            
            db.session.commit()
            
            # Store IDs for later use
            target_id = target_unit.id
            new_parent_id = new_parent_unit.id
            manager2_id = manager2.id
        
        # Get authentication token
        token = self.get_auth_token(client)
        
        # Edit the target unit
        response = client.post(
            f'/admin/org-structure/{target_id}/edit',
            data={
                'name': 'Updated Target Unit',
                'manager_id': str(manager2_id),
                'parent_id': str(new_parent_id)
            },
            headers={'Authorization': f'Bearer {token}'},
            content_type='application/x-www-form-urlencoded'
        )
        
        # Verify successful update
        assert response.status_code in [200, 302], f"Edit failed with status {response.status_code}"
        
        # Verify database changes
        with app.app_context():
            updated_unit = OrgUnit.query.get(target_id)
            assert updated_unit is not None, "Target unit not found after update"
            
            # Check updated name
            assert updated_unit.name == 'Updated Target Unit', "Unit name was not updated"
            
            # Check updated manager
            assert updated_unit.manager_id == manager2_id, "Unit manager was not updated"
            assert updated_unit.manager.email == 'manager2@test.com', "Manager relationship incorrect"
            
            # Check updated parent
            assert updated_unit.parent_id == new_parent_id, "Unit parent was not updated"
            assert updated_unit.parent.name == 'New Parent', "Parent relationship incorrect"
    
    def test_edit_prevents_circular_reference(self, client):
        """Test that editing prevents circular parent-child relationships"""
        
        # Create hierarchical structure: A -> B -> C
        with app.app_context():
            admin_user = User.query.filter_by(email='admin@test.com').first()
            
            unit_a = OrgUnit(name='Unit A', manager=admin_user)
            db.session.add(unit_a)
            db.session.flush()
            
            unit_b = OrgUnit(name='Unit B', parent=unit_a, manager=admin_user)
            db.session.add(unit_b)
            db.session.flush()
            
            unit_c = OrgUnit(name='Unit C', parent=unit_b, manager=admin_user)
            db.session.add(unit_c)
            db.session.commit()
            
            # Store IDs
            unit_a_id = unit_a.id
            unit_c_id = unit_c.id
        
        # Get authentication token
        token = self.get_auth_token(client)
        
        # Attempt to create circular reference: try to make A a child of C
        response = client.post(
            f'/admin/org-structure/{unit_a_id}/edit',
            data={
                'name': 'Unit A',
                'parent_id': str(unit_c_id)
            },
            headers={'Authorization': f'Bearer {token}'},
            content_type='application/x-www-form-urlencoded'
        )
        
        # Should redirect with error (or handle gracefully)
        assert response.status_code in [200, 302], "Edit request should complete"
        
        # Verify no circular reference was created
        with app.app_context():
            unit_a_updated = OrgUnit.query.get(unit_a_id)
            assert unit_a_updated.parent_id is None, "Circular reference was incorrectly allowed"
    
    def test_api_users_endpoint(self, client):
        """Test that /api/users endpoint returns user data for dropdowns"""
        
        # Get authentication token
        token = self.get_auth_token(client)
        
        # Request users API
        response = client.get(
            '/api/users',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        # Verify successful response
        assert response.status_code == 200, f"Users API failed with status {response.status_code}"
        
        # Verify JSON response
        users_data = response.get_json()
        assert isinstance(users_data, list), "Users API should return a list"
        assert len(users_data) >= 3, "Should have at least 3 test users"
        
        # Check user data structure
        admin_user = next((u for u in users_data if u['email'] == 'admin@test.com'), None)
        assert admin_user is not None, "Admin user not found in API response"
        assert 'id' in admin_user, "User ID missing from API response"
        assert 'first_name' in admin_user, "User first_name missing from API response"
        assert 'last_name' in admin_user, "User last_name missing from API response"
        assert admin_user['first_name'] == 'Test', "User first_name incorrect"
        assert admin_user['last_name'] == 'Admin', "User last_name incorrect"
    
    def test_org_structure_empty_state(self, client):
        """Test org structure page displays correctly when no units exist"""
        
        # Get authentication token
        token = self.get_auth_token(client)
        
        # Request org structure page with empty database
        response = client.get(
            '/admin/org-structure',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        # Verify successful response
        assert response.status_code == 200, f"Empty org structure page failed with status {response.status_code}"
        
        # Verify empty state handling
        html_content = response.data.decode('utf-8')
        assert 'const roots = []' in html_content, "Empty roots array not found"
        assert 'const allUnits = []' in html_content, "Empty allUnits array not found"
    
    def test_csv_import_validation(self, client):
        """Test CSV import handles missing and invalid data gracefully"""
        
        # Create CSV with missing parent and invalid manager
        csv_data = """name,parent_name,manager_email
Valid Unit,,admin@test.com
Invalid Manager Unit,,nonexistent@test.com
Missing Parent Unit,Nonexistent Parent,manager1@test.com"""
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_file.write(csv_data)
            temp_file_path = temp_file.name
        
        try:
            # Get authentication token
            token = self.get_auth_token(client)
            
            # Import CSV via POST request
            with open(temp_file_path, 'rb') as csv_file:
                response = client.post(
                    '/admin/org-structure/import',
                    data={'file': (csv_file, 'test_validation.csv')},
                    headers={'Authorization': f'Bearer {token}'},
                    content_type='multipart/form-data'
                )
            
            # Should handle errors gracefully
            assert response.status_code in [200, 302], "Import should handle validation errors gracefully"
            
            # Verify that valid unit was created
            with app.app_context():
                valid_unit = OrgUnit.query.filter_by(name='Valid Unit').first()
                assert valid_unit is not None, "Valid unit should have been created"
                assert valid_unit.manager.email == 'admin@test.com', "Valid unit manager should be set"
                
                # Invalid units should either be skipped or created without invalid relationships
                invalid_units = OrgUnit.query.filter(
                    OrgUnit.name.in_(['Invalid Manager Unit', 'Missing Parent Unit'])
                ).all()
                
                # Check that invalid relationships weren't created
                for unit in invalid_units:
                    if unit.name == 'Invalid Manager Unit':
                        assert unit.manager is None, "Invalid manager should not be assigned"
                    elif unit.name == 'Missing Parent Unit':
                        assert unit.parent is None, "Invalid parent should not be assigned"
        
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])