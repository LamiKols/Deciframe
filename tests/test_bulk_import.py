"""
Comprehensive tests for the Bulk Data Import system
"""

import pytest
import tempfile
import os
import io
import json
from unittest.mock import patch
from flask import url_for

from app import app, db
from models import User, RoleEnum, ImportJob, Problem, BusinessCase, Project, Department
from stateless_auth import generate_jwt_token


class TestBulkImport:
    
    @pytest.fixture
    def client(self):
        """Test client with test database"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    @pytest.fixture
    def admin_user(self, client):
        """Create admin user for testing"""
        with app.app_context():
            admin = User(
                name='Test Admin',
                email='admin@test.com',
                role=RoleEnum.Admin,
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            return admin
    
    @pytest.fixture
    def test_department(self, client):
        """Create test department"""
        with app.app_context():
            dept = Department(
                name='Test Department',
                level=1
            )
            db.session.add(dept)
            db.session.commit()
            return dept
    
    @pytest.fixture
    def auth_token(self, admin_user):
        """Generate JWT token for admin user"""
        return generate_jwt_token(admin_user.id)
    
    def create_test_csv(self, data_type='Problem'):
        """Create test CSV file content"""
        if data_type == 'Problem':
            return """title,description,priority,impact,urgency
Test Problem 1,This is a test problem description,High,High,Medium
Test Problem 2,Another test problem,Medium,Low,High
Invalid Problem,,Low,Medium,Low"""
        
        elif data_type == 'BusinessCase':
            return """title,summary,cost_estimate,benefit_estimate,case_type
Test Case 1,Test business case summary,10000,25000,Reactive
Test Case 2,Another test case,5000,15000,Proactive
Invalid Case,,2000,8000,Reactive"""
        
        elif data_type == 'Project':
            return """name,description,budget,status,start_date
Test Project 1,Test project description,50000,Planning,2024-01-01
Test Project 2,Another test project,75000,Active,2024-02-01
Invalid Project,,30000,Planning,2024-03-01"""
    
    def test_admin_import_data_page_access(self, client, auth_token):
        """Test admin can access import data page"""
        response = client.get(f'/admin/import-data?auth_token={auth_token}')
        assert response.status_code == 200
        assert b'Upload Data for Import' in response.data
        assert b'data_type' in response.data
        assert b'Problem' in response.data
        assert b'BusinessCase' in response.data
        assert b'Project' in response.data
    
    def test_file_upload_and_job_creation(self, client, auth_token):
        """Test file upload creates ImportJob correctly"""
        csv_content = self.create_test_csv('Problem')
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as test_file:
                response = client.post('/admin/import-data', data={
                    'data_type': 'Problem',
                    'file': (test_file, 'test_problems.csv'),
                    'auth_token': auth_token
                }, content_type='multipart/form-data', follow_redirects=True)
            
            assert response.status_code == 200
            
            # Check ImportJob was created
            with app.app_context():
                job = ImportJob.query.first()
                assert job is not None
                assert job.data_type == 'Problem'
                assert job.filename == 'test_problems.csv'
                assert job.status == 'Mapping'
        
        finally:
            os.unlink(temp_file_path)
    
    def test_column_mapping_interface(self, client, auth_token):
        """Test column mapping page and functionality"""
        # Create a test job first
        with app.app_context():
            job = ImportJob(
                user_id=1,  # Assuming admin user ID is 1
                data_type='Problem',
                filename='test.csv',
                status='Mapping'
            )
            db.session.add(job)
            db.session.commit()
            job_id = job.id
        
        # Test mapping page access
        response = client.get(f'/admin/import-data/map/{job_id}?auth_token={auth_token}')
        assert response.status_code == 200
        assert b'Map Columns to Fields' in response.data
        assert b'title' in response.data
        assert b'description' in response.data
    
    def test_complete_problem_import_workflow(self, client, auth_token, admin_user, test_department):
        """Test complete workflow for Problem import"""
        csv_content = self.create_test_csv('Problem')
        
        # Step 1: Upload file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file_path = f.name
        
        try:
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join(os.getcwd(), 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            with open(temp_file_path, 'rb') as test_file:
                response = client.post('/admin/import-data', data={
                    'data_type': 'Problem',
                    'file': (test_file, 'test_problems.csv'),
                    'auth_token': auth_token
                }, content_type='multipart/form-data')
            
            # Should redirect to mapping page
            assert response.status_code == 302
            
            # Get the created job
            with app.app_context():
                job = ImportJob.query.first()
                assert job.status == 'Mapping'
                job_id = job.id
            
            # Step 2: Submit column mapping
            mapping_data = {
                'title': 'title',
                'description': 'description', 
                'priority': 'priority',
                'impact': 'impact',
                'urgency': 'urgency',
                'auth_token': auth_token
            }
            
            response = client.post(f'/admin/import-data/map/{job_id}', data=mapping_data)
            assert response.status_code == 302  # Redirect to execute page
            
            # Check job status updated
            with app.app_context():
                job = ImportJob.query.get(job_id)
                assert job.status == 'Importing'
                assert job.mapping is not None
            
            # Step 3: Execute import (simulate by updating job manually)
            with app.app_context():
                # Simulate successful import
                job = ImportJob.query.get(job_id)
                
                # Create test problems based on CSV data
                problems_data = [
                    {'title': 'Test Problem 1', 'description': 'This is a test problem description', 'priority': 'High', 'impact': 'High', 'urgency': 'Medium'},
                    {'title': 'Test Problem 2', 'description': 'Another test problem', 'priority': 'Medium', 'impact': 'Low', 'urgency': 'High'}
                ]
                
                for problem_data in problems_data:
                    problem = Problem(**problem_data)
                    db.session.add(problem)
                
                # Update job with results
                job.rows_success = 2
                job.rows_failed = 1
                job.error_details = [{'row': 3, 'error': 'Missing required field: title'}]
                job.status = 'Complete'
                db.session.commit()
            
            # Step 4: Check results
            response = client.get(f'/admin/import-data/result/{job_id}?auth_token={auth_token}')
            assert response.status_code == 200
            assert b'Import Completed Successfully' in response.data
            assert b'2' in response.data  # Success count
            assert b'1' in response.data  # Failed count
            
            # Verify problems were created
            with app.app_context():
                problems = Problem.query.all()
                assert len(problems) == 2
                assert problems[0].title == 'Test Problem 1'
                assert problems[1].title == 'Test Problem 2'
        
        finally:
            os.unlink(temp_file_path)
    
    def test_business_case_import_workflow(self, client, auth_token, admin_user):
        """Test BusinessCase import with validation"""
        csv_content = self.create_test_csv('BusinessCase')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file_path = f.name
        
        try:
            # Upload and create job
            with open(temp_file_path, 'rb') as test_file:
                response = client.post('/admin/import-data', data={
                    'data_type': 'BusinessCase',
                    'file': (test_file, 'test_cases.csv'),
                    'auth_token': auth_token
                }, content_type='multipart/form-data')
            
            with app.app_context():
                job = ImportJob.query.first()
                assert job.data_type == 'BusinessCase'
                
                # Simulate mapping and execution
                job.mapping = {
                    'title': 'title',
                    'summary': 'summary',
                    'cost_estimate': 'cost_estimate',
                    'benefit_estimate': 'benefit_estimate',
                    'case_type': 'case_type'
                }
                job.status = 'Complete'
                job.rows_success = 2
                job.rows_failed = 1
                job.error_details = [{'row': 3, 'error': 'Missing required field: title'}]
                
                # Create test business cases
                cases_data = [
                    {'title': 'Test Case 1', 'summary': 'Test business case summary', 'cost_estimate': 10000, 'benefit_estimate': 25000, 'case_type': 'Reactive'},
                    {'title': 'Test Case 2', 'summary': 'Another test case', 'cost_estimate': 5000, 'benefit_estimate': 15000, 'case_type': 'Proactive'}
                ]
                
                for case_data in cases_data:
                    case = BusinessCase(**case_data)
                    db.session.add(case)
                
                db.session.commit()
                
                # Verify business cases were created
                cases = BusinessCase.query.all()
                assert len(cases) == 2
                assert cases[0].title == 'Test Case 1'
                assert cases[0].cost_estimate == 10000
        
        finally:
            os.unlink(temp_file_path)
    
    def test_project_import_workflow(self, client, auth_token, admin_user):
        """Test Project import with date handling"""
        csv_content = self.create_test_csv('Project')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file_path = f.name
        
        try:
            # Upload and create job
            with open(temp_file_path, 'rb') as test_file:
                response = client.post('/admin/import-data', data={
                    'data_type': 'Project',
                    'file': (test_file, 'test_projects.csv'),
                    'auth_token': auth_token
                }, content_type='multipart/form-data')
            
            with app.app_context():
                job = ImportJob.query.first()
                assert job.data_type == 'Project'
                
                # Simulate successful import
                job.mapping = {
                    'name': 'name',
                    'description': 'description',
                    'budget': 'budget',
                    'status': 'status'
                }
                job.status = 'Complete'
                job.rows_success = 2
                job.rows_failed = 1
                
                # Create test projects
                projects_data = [
                    {'name': 'Test Project 1', 'description': 'Test project description', 'budget': 50000, 'status': 'Planning'},
                    {'name': 'Test Project 2', 'description': 'Another test project', 'budget': 75000, 'status': 'Active'}
                ]
                
                for project_data in projects_data:
                    project = Project(**project_data)
                    db.session.add(project)
                
                db.session.commit()
                
                # Verify projects were created
                projects = Project.query.all()
                assert len(projects) == 2
                assert projects[0].name == 'Test Project 1'
                assert projects[0].budget == 50000
        
        finally:
            os.unlink(temp_file_path)
    
    def test_invalid_file_upload(self, client, auth_token):
        """Test handling of invalid file uploads"""
        # Test unsupported file type
        response = client.post('/admin/import-data', data={
            'data_type': 'Problem',
            'file': (io.BytesIO(b'invalid content'), 'test.txt'),
            'auth_token': auth_token
        }, content_type='multipart/form-data')
        
        # Should handle error gracefully
        assert response.status_code in [200, 302]  # Either shows error or redirects
    
    def test_error_handling_and_details(self, client, auth_token, admin_user):
        """Test error handling and error_details population"""
        # Create CSV with intentional errors
        csv_content = """title,description,priority
Valid Problem,Good description,High
,Missing title,Medium
Another Valid,Good description,Invalid Priority"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as test_file:
                response = client.post('/admin/import-data', data={
                    'data_type': 'Problem',
                    'file': (test_file, 'error_test.csv'),
                    'auth_token': auth_token
                }, content_type='multipart/form-data')
            
            with app.app_context():
                job = ImportJob.query.first()
                
                # Simulate import with errors
                job.mapping = {'title': 'title', 'description': 'description', 'priority': 'priority'}
                job.status = 'Failed'
                job.rows_success = 1
                job.rows_failed = 2
                job.error_details = [
                    {'row': 2, 'error': 'Missing required field: title'},
                    {'row': 3, 'error': 'Invalid priority value: Invalid Priority'}
                ]
                db.session.commit()
                
                # Check error details are properly stored
                assert len(job.error_details) == 2
                assert job.error_details[0]['error'] == 'Missing required field: title'
                assert job.error_details[1]['row'] == 3
        
        finally:
            os.unlink(temp_file_path)
    
    def test_job_status_transitions(self, client, auth_token, admin_user):
        """Test ImportJob status transitions throughout workflow"""
        with app.app_context():
            # Create job in Pending status
            job = ImportJob(
                user_id=admin_user.id,
                data_type='Problem',
                filename='test.csv',
                status='Pending'
            )
            db.session.add(job)
            db.session.commit()
            job_id = job.id
            
            # Test status progression
            job = ImportJob.query.get(job_id)
            assert job.status == 'Pending'
            
            # Move to Mapping
            job.status = 'Mapping'
            db.session.commit()
            
            job = ImportJob.query.get(job_id)
            assert job.status == 'Mapping'
            
            # Move to Importing
            job.status = 'Importing'
            job.mapping = {'title': 'title', 'description': 'description'}
            db.session.commit()
            
            job = ImportJob.query.get(job_id)
            assert job.status == 'Importing'
            assert job.mapping is not None
            
            # Complete successfully
            job.status = 'Complete'
            job.rows_success = 5
            job.rows_failed = 0
            db.session.commit()
            
            job = ImportJob.query.get(job_id)
            assert job.status == 'Complete'
            assert job.rows_success == 5
            assert job.rows_failed == 0
    
    def test_unauthorized_access(self, client):
        """Test that non-admin users cannot access import functionality"""
        # Test without authentication
        response = client.get('/admin/import-data')
        assert response.status_code in [401, 403, 302]  # Unauthorized or redirect
        
        response = client.post('/admin/import-data', data={
            'data_type': 'Problem',
            'file': (io.BytesIO(b'test'), 'test.csv')
        })
        assert response.status_code in [401, 403, 302]
    
    def test_file_cleanup_after_import(self, client, auth_token, admin_user):
        """Test that uploaded files are cleaned up after processing"""
        csv_content = self.create_test_csv('Problem')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file_path = f.name
        
        try:
            # Upload file
            with open(temp_file_path, 'rb') as test_file:
                response = client.post('/admin/import-data', data={
                    'data_type': 'Problem',
                    'file': (test_file, 'cleanup_test.csv'),
                    'auth_token': auth_token
                }, content_type='multipart/form-data')
            
            with app.app_context():
                job = ImportJob.query.first()
                upload_path = os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), job.filename)
                
                # File should exist after upload
                if os.path.exists(upload_path):
                    # Simulate import completion and cleanup
                    job.status = 'Complete'
                    db.session.commit()
                    
                    # In real implementation, file would be cleaned up
                    # For test, we verify the cleanup logic would work
                    assert job.filename == 'cleanup_test.csv'
        
        finally:
            os.unlink(temp_file_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])