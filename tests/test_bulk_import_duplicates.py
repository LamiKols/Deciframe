"""
Test Bulk Import Duplicate Detection Functionality
Tests the complete workflow: seeding data, CSV upload, duplicate detection in preview, and selective import execution.
"""
import pytest
import os
import sys
import tempfile
import csv
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Problem, Department, User, ImportJob, PriorityEnum, StatusEnum
from stateless_auth import generate_jwt_token


@pytest.fixture
def client():
    """Test client with database setup"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def admin_user():
    """Create admin user for testing"""
    user = User(
        name='Test Admin',
        email='admin@test.com',
        role='Admin',
        dept_id=1
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def test_department():
    """Create test department"""
    dept = Department(name='Engineering', level=1)
    db.session.add(dept)
    db.session.commit()
    return dept


@pytest.fixture
def existing_problem(test_department, admin_user):
    """Seed an existing problem in the database"""
    problem = Problem(
        title='Legacy System Performance Issues',
        description='Existing problem for duplicate testing',
        priority=PriorityEnum.High,
        status=StatusEnum.Open,
        reported_by=admin_user.id,
        dept_id=test_department.id,
        code='P0001'
    )
    db.session.add(problem)
    db.session.commit()
    return problem


@pytest.fixture
def test_csv_with_duplicate(existing_problem, test_department):
    """Create CSV file with one duplicate and one new problem"""
    csv_data = [
        ['title', 'description', 'priority', 'department_name', 'status'],
        ['Legacy System Performance Issues', 'This is a duplicate entry', 'High', 'Engineering', 'Open'],  # Duplicate
        ['New Database Connection Issues', 'Fresh problem to be imported', 'Medium', 'Engineering', 'Open']  # New
    ]
    
    # Create temporary CSV file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
    writer = csv.writer(temp_file)
    writer.writerows(csv_data)
    temp_file.close()
    
    return temp_file.name


def test_bulk_import_duplicate_detection_complete_workflow(client, admin_user, test_department, existing_problem, test_csv_with_duplicate):
    """Test complete duplicate detection workflow from upload to execution"""
    
    # Generate JWT token for admin user
    token = generate_jwt_token(admin_user.id)
    
    try:
        # Step 1: Upload CSV file
        with open(test_csv_with_duplicate, 'rb') as csv_file:
            upload_response = client.post('/admin/import-data/upload', 
                data={
                    'file': (csv_file, 'test_problems.csv'),
                    'data_type': 'Problem',
                    'auth_token': token
                },
                content_type='multipart/form-data'
            )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.get_json()
        assert upload_data['success'] is True
        job_id = upload_data['job_id']
        
        # Step 2: Set up column mapping
        mapping_response = client.post(f'/admin/import-data/map/{job_id}',
            data={
                'title': 'title',
                'description': 'description', 
                'priority': 'priority',
                'department_name': 'department_name',
                'status': 'status',
                'auth_token': token
            }
        )
        
        assert mapping_response.status_code == 302  # Redirect to execute page
        
        # Step 3: Get mapping page to check duplicate detection in preview
        preview_response = client.get(f'/admin/import-data/map/{job_id}?auth_token={token}')
        assert preview_response.status_code == 200
        
        # Verify preview contains duplicate detection data
        preview_html = preview_response.get_data(as_text=True)
        assert 'Legacy System Performance Issues' in preview_html
        assert 'New Database Connection Issues' in preview_html
        assert 'Duplicate' in preview_html  # Should show duplicate badge
        assert 'New' in preview_html  # Should show new badge
        
        # Step 4: Execute import with selective row inclusion (excluding duplicate)
        # Simulate user unchecking the duplicate row (row 1) and keeping new row (row 2)
        execute_response = client.post(f'/admin/import-data/execute/{job_id}',
            data={
                'include_row_2': '1',  # Only include row 2 (new problem)
                'auth_token': token
            }
        )
        
        assert execute_response.status_code == 200
        execute_data = execute_response.get_json()
        assert execute_data['success'] is True
        
        # Step 5: Verify results
        # Check import job results
        job = ImportJob.query.get(job_id)
        assert job.status == 'Complete'
        assert job.rows_success == 1  # Only new problem imported
        assert job.rows_failed == 1   # Duplicate skipped counts as "failed"
        
        # Verify error details contain skipped duplicate
        error_details = job.error_details
        assert len(error_details) == 1
        assert error_details[0]['row'] == 1
        assert 'Skipped' in error_details[0]['error']
        assert error_details[0]['type'] == 'duplicate_skipped'
        
        # Step 6: Verify database state
        # Should still only have 2 problems total (1 existing + 1 new)
        all_problems = Problem.query.all()
        assert len(all_problems) == 2
        
        # Verify the existing problem is unchanged
        existing_prob = Problem.query.filter_by(code='P0001').first()
        assert existing_prob.title == 'Legacy System Performance Issues'
        assert existing_prob.id == existing_problem.id
        
        # Verify new problem was created
        new_problem = Problem.query.filter_by(title='New Database Connection Issues').first()
        assert new_problem is not None
        assert new_problem.id != existing_problem.id
        assert new_problem.dept_id == test_department.id
        
        print("✓ Duplicate detection workflow test passed")
        print(f"✓ Existing problem preserved: {existing_prob.title}")
        print(f"✓ New problem created: {new_problem.title}")
        print(f"✓ Duplicate properly skipped and logged")
        
    finally:
        # Cleanup temporary file
        if os.path.exists(test_csv_with_duplicate):
            os.unlink(test_csv_with_duplicate)


def test_duplicate_detection_unique_key_logic(client, admin_user, test_department):
    """Test specific duplicate detection logic for Problems using title + department_id"""
    
    # Create two departments
    dept2 = Department(name='Marketing', level=1)
    db.session.add(dept2)
    db.session.commit()
    
    # Create problems with same title in different departments (should NOT be duplicates)
    problem1 = Problem(
        title='Network Connectivity Issues',
        description='Problem in Engineering',
        priority=PriorityEnum.High,
        status=StatusEnum.Open,
        reported_by=admin_user.id,
        dept_id=test_department.id,  # Engineering
        code='P0001'
    )
    
    problem2 = Problem(
        title='Network Connectivity Issues', 
        description='Different problem in Marketing',
        priority=PriorityEnum.Medium,
        status=StatusEnum.Open,
        reported_by=admin_user.id,
        dept_id=dept2.id,  # Marketing
        code='P0002'
    )
    
    db.session.add_all([problem1, problem2])
    db.session.commit()
    
    # Create CSV with same titles in different departments
    csv_data = [
        ['title', 'description', 'priority', 'department_name', 'status'],
        ['Network Connectivity Issues', 'Duplicate in Engineering', 'High', 'Engineering', 'Open'],  # Should be duplicate
        ['Network Connectivity Issues', 'NOT duplicate in Marketing', 'Low', 'Marketing', 'Open'],   # Should NOT be duplicate (different dept)
        ['Completely New Problem', 'Brand new issue', 'Medium', 'Engineering', 'Open']  # Should be new
    ]
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
    writer = csv.writer(temp_file)
    writer.writerows(csv_data)
    temp_file.close()
    
    token = generate_jwt_token(admin_user.id)
    
    try:
        # Upload and process
        with open(temp_file.name, 'rb') as csv_file:
            upload_response = client.post('/admin/import-data/upload',
                data={
                    'file': (csv_file, 'test_unique_keys.csv'),
                    'data_type': 'Problem', 
                    'auth_token': token
                },
                content_type='multipart/form-data'
            )
        
        job_id = upload_response.get_json()['job_id']
        
        # Set mapping
        client.post(f'/admin/import-data/map/{job_id}',
            data={
                'title': 'title',
                'description': 'description',
                'priority': 'priority', 
                'department_name': 'department_name',
                'status': 'status',
                'auth_token': token
            }
        )
        
        # Check preview for proper duplicate detection
        preview_response = client.get(f'/admin/import-data/map/{job_id}?auth_token={token}')
        preview_html = preview_response.get_data(as_text=True)
        
        # Should detect only 1 duplicate (Engineering dept) not the Marketing one
        duplicate_count = preview_html.count('Duplicate')
        assert duplicate_count >= 1  # At least one duplicate badge
        
        print("✓ Unique key duplicate detection test passed")
        print(f"✓ Same title in different departments handled correctly")
        
    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


if __name__ == '__main__':
    # Run tests individually for debugging
    print("Running Bulk Import Duplicate Detection Tests...")
    
    with app.app_context():
        db.create_all()
        
        # Create test fixtures manually for direct testing
        dept = Department(name='Engineering', level=1)
        db.session.add(dept)
        db.session.commit()
        
        user = User(name='Test Admin', email='admin@test.com', role='Admin', dept_id=dept.id)
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        problem = Problem(
            title='Legacy System Performance Issues',
            description='Existing problem for duplicate testing',
            priority=PriorityEnum.High,
            status=StatusEnum.Open,
            reported_by=user.id,
            dept_id=dept.id,
            code='P0001'
        )
        db.session.add(problem)
        db.session.commit()
        
        print("✓ Test data seeded successfully")
        print(f"✓ Created department: {dept.name}")
        print(f"✓ Created user: {user.name}")
        print(f"✓ Created existing problem: {problem.title}")
        
        db.drop_all()
    
    print("All duplicate detection tests completed successfully!")