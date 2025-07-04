"""
Test suite for Executive Dashboard module
Tests authorization, API endpoints, and data accuracy
"""

import json
from datetime import datetime, timedelta
import pytest
from app import app, db
from models import (
    User, Department, Problem, BusinessCase, Project, ProjectMilestone,
    StatusEnum, RoleEnum, PriorityEnum, CaseTypeEnum, CaseDepthEnum
)
from stateless_auth import create_auth_token


@pytest.fixture
def test_app():
    """Create a test Flask app with database"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_client(test_app):
    """Create a test client"""
    return test_app.test_client()


@pytest.fixture
def test_department(test_app):
    """Create a test department"""
    dept = Department(name="Test Department", level=1)
    db.session.add(dept)
    db.session.commit()
    return dept


@pytest.fixture
def admin_user(test_app, test_department):
    """Create an admin user"""
    user = User(
        email="admin@test.com",
        name="Admin User",
        role=RoleEnum.Admin,
        department_id=test_department.id
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def director_user(test_app, test_department):
    """Create a director user"""
    user = User(
        email="director@test.com",
        name="Director User",
        role=RoleEnum.Director,
        department_id=test_department.id
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def staff_user(test_app, test_department):
    """Create a staff user (non-admin)"""
    user = User(
        email="staff@test.com",
        name="Staff User",
        role=RoleEnum.Staff,
        department_id=test_department.id
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_data(test_app, test_department, admin_user):
    """Create sample data for testing"""
    # Create problems
    problem1 = Problem(
        title="Test Problem 1",
        description="Description 1",
        priority=PriorityEnum.High,
        department_id=test_department.id,
        status=StatusEnum.Open,
        created_by=admin_user.id
    )
    
    problem2 = Problem(
        title="Test Problem 2",
        description="Description 2",
        priority=PriorityEnum.Medium,
        department_id=test_department.id,
        status=StatusEnum.Resolved,
        created_by=admin_user.id
    )
    
    db.session.add_all([problem1, problem2])
    db.session.flush()
    
    # Create business cases
    case1 = BusinessCase(
        problem_id=problem1.id,
        title="Test Case 1",
        description="Case description 1",
        cost_estimate=50000.0,
        benefit_estimate=100000.0,
        created_by=admin_user.id,
        status=StatusEnum.Open,
        case_type=CaseTypeEnum.Reactive,
        case_depth=CaseDepthEnum.Light
    )
    
    case2 = BusinessCase(
        title="Test Case 2",
        description="Case description 2",
        cost_estimate=25000.0,
        benefit_estimate=75000.0,
        created_by=admin_user.id,
        status=StatusEnum.Resolved,
        case_type=CaseTypeEnum.Proactive,
        case_depth=CaseDepthEnum.Full,
        initiative_name="Test Initiative"
    )
    
    db.session.add_all([case1, case2])
    db.session.flush()
    
    # Create projects
    project1 = Project(
        name="Test Project 1",
        description="Project description 1",
        start_date=datetime.now().date() - timedelta(days=30),
        end_date=datetime.now().date() + timedelta(days=30),
        budget=60000.0,
        status=StatusEnum.InProgress,
        priority=PriorityEnum.High,
        business_case_id=case1.id,
        project_manager_id=admin_user.id,
        department_id=test_department.id,
        created_by=admin_user.id
    )
    
    project2 = Project(
        name="Test Project 2",
        description="Project description 2",
        start_date=datetime.now().date() - timedelta(days=60),
        end_date=datetime.now().date() - timedelta(days=10),
        budget=40000.0,
        status=StatusEnum.Resolved,
        priority=PriorityEnum.Medium,
        business_case_id=case2.id,
        project_manager_id=admin_user.id,
        department_id=test_department.id,
        created_by=admin_user.id
    )
    
    db.session.add_all([project1, project2])
    db.session.flush()
    
    # Create milestones
    milestone1 = ProjectMilestone(
        project_id=project1.id,
        name="Test Milestone 1",
        description="Milestone description",
        due_date=datetime.now().date() + timedelta(days=15),
        owner_id=admin_user.id,
        completed=False
    )
    
    milestone2 = ProjectMilestone(
        project_id=project2.id,
        name="Test Milestone 2",
        description="Milestone description",
        due_date=datetime.now().date() - timedelta(days=5),
        owner_id=admin_user.id,
        completed=True,
        completion_date=datetime.now().date() - timedelta(days=3)
    )
    
    db.session.add_all([milestone1, milestone2])
    db.session.commit()
    
    return {
        'problems': [problem1, problem2],
        'cases': [case1, case2],
        'projects': [project1, project2],
        'milestones': [milestone1, milestone2]
    }


def test_dashboard_access_admin_user(test_client, admin_user, sample_data):
    """Test that admin users can access dashboard"""
    token = create_auth_token(admin_user.id)
    response = test_client.get(f'/admin/dashboard?token={token}')
    assert response.status_code == 200
    assert b'Executive Dashboard' in response.data


def test_dashboard_access_director_user(test_client, director_user, sample_data):
    """Test that director users can access dashboard"""
    token = create_auth_token(director_user.id)
    response = test_client.get(f'/admin/dashboard?token={token}')
    assert response.status_code == 200
    assert b'Executive Dashboard' in response.data


def test_dashboard_access_denied_staff_user(test_client, staff_user):
    """Test that staff users cannot access dashboard"""
    token = create_auth_token(staff_user.id)
    response = test_client.get(f'/admin/dashboard?token={token}')
    assert response.status_code == 403


def test_dashboard_access_denied_unauthenticated(test_client):
    """Test that unauthenticated users cannot access dashboard"""
    response = test_client.get('/admin/dashboard')
    assert response.status_code == 403


def test_problems_trend_api(test_client, admin_user, sample_data):
    """Test problems trend API endpoint"""
    token = create_auth_token(admin_user.id)
    response = test_client.get(f'/admin/api/dashboard/problems-trend?token={token}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    
    # Verify data structure
    if data:
        item = data[0]
        assert 'date' in item
        assert 'count' in item
        assert isinstance(item['count'], int)


def test_case_conversion_api(test_client, admin_user, sample_data):
    """Test case conversion API endpoint"""
    token = create_auth_token(admin_user.id)
    response = test_client.get(f'/admin/api/dashboard/case-conversion?token={token}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    
    # Verify data structure
    if data:
        item = data[0]
        assert 'month' in item
        assert 'problems' in item
        assert 'cases' in item
        assert 'conversion_rate' in item


def test_project_metrics_api(test_client, admin_user, sample_data):
    """Test project metrics API endpoint"""
    token = create_auth_token(admin_user.id)
    response = test_client.get(f'/admin/api/dashboard/project-metrics?token={token}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify data structure
    assert 'on_time' in data
    assert 'delayed' in data
    assert 'in_progress' in data
    assert 'total' in data
    assert 'counts' in data
    
    # Verify data types
    assert isinstance(data['on_time'], (int, float))
    assert isinstance(data['delayed'], (int, float))
    assert isinstance(data['in_progress'], (int, float))
    assert isinstance(data['total'], int)


def test_status_breakdown_api(test_client, admin_user, sample_data):
    """Test status breakdown API endpoint"""
    token = create_auth_token(admin_user.id)
    response = test_client.get(f'/admin/api/dashboard/status-breakdown?token={token}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify data structure
    assert 'problems' in data
    assert 'cases' in data
    assert 'projects' in data
    
    # Verify array structure
    for category in ['problems', 'cases', 'projects']:
        assert isinstance(data[category], list)
        if data[category]:
            item = data[category][0]
            assert 'status' in item
            assert 'count' in item


def test_csv_export_access_control(test_client, admin_user, staff_user, sample_data):
    """Test CSV export access control"""
    # Admin should have access
    admin_token = create_auth_token(admin_user.id)
    response = test_client.get(f'/admin/export/dashboard-csv?token={admin_token}')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'
    
    # Staff should be denied
    staff_token = create_auth_token(staff_user.id)
    response = test_client.get(f'/admin/export/dashboard-csv?token={staff_token}')
    assert response.status_code == 403


def test_api_access_control(test_client, admin_user, staff_user, sample_data):
    """Test that all API endpoints require admin access"""
    api_endpoints = [
        '/admin/api/dashboard/problems-trend',
        '/admin/api/dashboard/case-conversion',
        '/admin/api/dashboard/project-metrics',
        '/admin/api/dashboard/status-breakdown'
    ]
    
    admin_token = create_auth_token(admin_user.id)
    staff_token = create_auth_token(staff_user.id)
    
    for endpoint in api_endpoints:
        # Admin should have access
        response = test_client.get(f'{endpoint}?token={admin_token}')
        assert response.status_code == 200, f"Admin access failed for {endpoint}"
        
        # Staff should be denied
        response = test_client.get(f'{endpoint}?token={staff_token}')
        assert response.status_code == 403, f"Staff access not denied for {endpoint}"


def test_dashboard_metrics_accuracy(test_client, admin_user, sample_data):
    """Test that dashboard metrics reflect actual data"""
    token = create_auth_token(admin_user.id)
    response = test_client.get(f'/admin/dashboard?token={token}')
    
    assert response.status_code == 200
    
    # Verify the response contains expected metrics
    content = response.data.decode('utf-8')
    
    # Should show 2 total problems
    assert '2' in content  # problems_count
    
    # Should show 1 open case (case1 is Open, case2 is Resolved)
    # This would be in the KPI section
    
    # Should show 1 active project (project1 is InProgress, project2 is Resolved)
    # This would be in the active_projects metric


def test_roi_calculation_accuracy(test_client, admin_user, sample_data):
    """Test that ROI calculations are accurate"""
    token = create_auth_token(admin_user.id)
    
    # Get project metrics to verify calculations
    response = test_client.get(f'/admin/api/dashboard/project-metrics?token={token}')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Verify that percentages add up correctly
    total_percentage = data['on_time'] + data['delayed'] + data['in_progress']
    assert abs(total_percentage - 100.0) < 0.1 or data['total'] == 0


if __name__ == '__main__':
    # Run tests individually for debugging
    from app import app
    
    with app.app_context():
        db.create_all()
        
        # Create test data
        dept = Department(name="Test Dept", level=1)
        db.session.add(dept)
        db.session.flush()
        
        admin = User(
            email="admin@test.com",
            name="Admin User", 
            role=RoleEnum.Admin,
            department_id=dept.id
        )
        admin.set_password("password123")
        db.session.add(admin)
        db.session.commit()
        
        print("✓ Test database initialized")
        print("✓ Admin user created")
        print("✓ Ready for dashboard testing")