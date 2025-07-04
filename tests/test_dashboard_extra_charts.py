"""
Test suite for Executive Dashboard advanced analytics charts
Tests all seven new chart endpoints and template integration
"""

import pytest
import json
from datetime import datetime, timedelta, date
from app import app, db
from models import (
    User, Department, Problem, BusinessCase, Project, ProjectMilestone,
    RoleEnum, StatusEnum, PriorityEnum
)


@pytest.fixture
def test_app():
    """Create a test Flask app"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def test_client(test_app):
    """Create a test client"""
    return test_app.test_client()


@pytest.fixture
def sample_data(test_app):
    """Create comprehensive sample data for testing"""
    with test_app.app_context():
        # Create departments
        dept1 = Department(name='Engineering', level=1)
        dept2 = Department(name='Marketing', level=1)
        dept3 = Department(name='Finance', level=1)
        db.session.add_all([dept1, dept2, dept3])
        db.session.commit()
        
        # Create users
        ceo = User(
            email='ceo@test.com',
            password_hash='test',
            name='CEO User',
            role=RoleEnum.CEO,
            department_id=dept1.id
        )
        pm = User(
            email='pm@test.com',
            password_hash='test',
            name='PM User',
            role=RoleEnum.PM,
            department_id=dept1.id
        )
        ba = User(
            email='ba@test.com',
            password_hash='test',
            name='BA User',
            role=RoleEnum.BA,
            department_id=dept2.id
        )
        db.session.add_all([ceo, pm, ba])
        db.session.commit()
        
        # Create problems
        problem1 = Problem(
            title='System Performance Issue',
            description='Database queries are slow and affecting user experience',
            priority=PriorityEnum.High,
            department_id=dept1.id,
            created_by=ceo.id,
            status=StatusEnum.Resolved,
            created_at=datetime.now() - timedelta(days=20)
        )
        problem2 = Problem(
            title='Marketing Efficiency Problem',
            description='Marketing campaigns lack proper tracking and ROI measurement',
            priority=PriorityEnum.Medium,
            department_id=dept2.id,
            created_by=pm.id,
            status=StatusEnum.Open,
            created_at=datetime.now() - timedelta(days=10)
        )
        db.session.add_all([problem1, problem2])
        db.session.commit()
        
        # Create business cases
        case1 = BusinessCase(
            problem_id=problem1.id,
            title='Database Optimization Initiative',
            description='Implement database indexing and query optimization',
            cost_estimate=50000,
            benefit_estimate=120000,
            created_by=ceo.id,
            status=StatusEnum.Resolved,
            created_at=datetime.now() - timedelta(days=15),
            updated_at=datetime.now() - timedelta(days=10)
        )
        case1.calculate_roi()
        
        case2 = BusinessCase(
            problem_id=problem2.id,
            title='Marketing Analytics Platform',
            description='Deploy comprehensive marketing analytics solution',
            cost_estimate=30000,
            benefit_estimate=80000,
            created_by=ba.id,
            status=StatusEnum.Open,
            created_at=datetime.now() - timedelta(days=8),
            updated_at=datetime.now() - timedelta(days=5)
        )
        case2.calculate_roi()
        
        db.session.add_all([case1, case2])
        db.session.commit()
        
        # Create projects
        project1 = Project(
            name='Database Performance Upgrade',
            description='Optimize database performance',
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=30),
            budget=50000,
            status=StatusEnum.InProgress,
            business_case_id=case1.id,
            project_manager_id=pm.id,
            department_id=dept1.id,
            created_by=ceo.id
        )
        
        project2 = Project(
            name='Marketing Analytics Implementation',
            description='Deploy marketing analytics platform',
            start_date=date.today() - timedelta(days=15),
            end_date=date.today() + timedelta(days=45),
            budget=30000,
            status=StatusEnum.Open,
            business_case_id=case2.id,
            project_manager_id=pm.id,
            department_id=dept2.id,
            created_by=ba.id
        )
        
        db.session.add_all([project1, project2])
        db.session.commit()
        
        # Create milestones
        milestone1 = ProjectMilestone(
            project_id=project1.id,
            name='Database Analysis Complete',
            description='Complete database performance analysis',
            due_date=date.today() - timedelta(days=10),
            owner_id=pm.id,
            completed=True,
            completion_date=date.today() - timedelta(days=12)
        )
        
        milestone2 = ProjectMilestone(
            project_id=project1.id,
            name='Performance Optimization',
            description='Implement optimization strategies',
            due_date=date.today() + timedelta(days=15),
            owner_id=pm.id,
            completed=False
        )
        
        milestone3 = ProjectMilestone(
            project_id=project2.id,
            name='Analytics Platform Setup',
            description='Set up marketing analytics platform',
            due_date=date.today() - timedelta(days=5),
            owner_id=ba.id,
            completed=False
        )
        
        db.session.add_all([milestone1, milestone2, milestone3])
        db.session.commit()
        
        return {
            'departments': [dept1, dept2, dept3],
            'users': [ceo, pm, ba],
            'problems': [problem1, problem2],
            'cases': [case1, case2],
            'projects': [project1, project2],
            'milestones': [milestone1, milestone2, milestone3]
        }


def test_department_heatmap_endpoint(test_client, sample_data):
    """Test department heat-map API endpoint"""
    response = test_client.get('/admin/api/dashboard-demo/department-heatmap')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check data structure
    for item in data:
        assert 'department' in item
        assert 'problems' in item
        assert 'cases' in item
        assert 'projects' in item
        assert 'avg_roi' in item
        assert isinstance(item['problems'], int)
        assert isinstance(item['cases'], int)
        assert isinstance(item['projects'], int)
        assert isinstance(item['avg_roi'], (int, float))


def test_time_to_value_endpoint(test_client, sample_data):
    """Test time-to-value distribution API endpoint"""
    response = test_client.get('/admin/api/dashboard-demo/time-to-value')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert isinstance(data, dict)
    assert 'approval_to_start' in data
    assert 'start_to_completion' in data
    
    # Check bucket structure
    for category in ['approval_to_start', 'start_to_completion']:
        assert 'labels' in data[category]
        assert 'data' in data[category]
        assert isinstance(data[category]['labels'], list)
        assert isinstance(data[category]['data'], list)


def test_risks_issues_endpoint(test_client, sample_data):
    """Test risk and issue backlog API endpoint"""
    response = test_client.get('/admin/api/dashboard-demo/risks-issues')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert isinstance(data, list)
    
    for item in data:
        assert 'project_code' in item
        assert 'risk_count' in item
        assert 'issue_count' in item
        assert 'highest_severity' in item
        assert isinstance(item['risk_count'], int)
        assert isinstance(item['issue_count'], int)
        assert item['highest_severity'] in ['Low', 'Medium', 'High']


def test_milestone_burndown_endpoint(test_client, sample_data):
    """Test milestone burn-down API endpoint"""
    response = test_client.get('/admin/api/dashboard-demo/milestone-burndown')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert isinstance(data, list)
    
    for project_data in data:
        assert 'project' in project_data
        assert 'timeline' in project_data
        assert isinstance(project_data['timeline'], list)
        
        for point in project_data['timeline']:
            assert 'date' in point
            assert 'planned' in point
            assert 'actual' in point
            assert isinstance(point['planned'], (int, float))
            assert isinstance(point['actual'], int)


def test_roi_waterfall_endpoint(test_client, sample_data):
    """Test ROI waterfall API endpoint"""
    response = test_client.get('/admin/api/dashboard-demo/roi-waterfall')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert isinstance(data, list)
    
    for item in data:
        assert 'case_code' in item
        assert 'net_benefit' in item
        assert 'cost' in item
        assert 'benefit' in item
        assert isinstance(item['net_benefit'], (int, float))
        assert isinstance(item['cost'], (int, float))
        assert isinstance(item['benefit'], (int, float))


def test_problem_clusters_endpoint(test_client, sample_data):
    """Test problem clusters API endpoint"""
    response = test_client.get('/admin/api/dashboard-demo/problem-clusters')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert isinstance(data, list)
    assert len(data) <= 5  # Should return top 5 clusters
    
    for cluster in data:
        assert 'cluster_label' in cluster
        assert 'count' in cluster
        assert 'avg_resolution_days' in cluster
        assert isinstance(cluster['count'], int)
        assert isinstance(cluster['avg_resolution_days'], (int, float))


def test_resource_utilization_endpoint(test_client, sample_data):
    """Test resource utilization API endpoint"""
    response = test_client.get('/admin/api/dashboard-demo/resource-utilization')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert isinstance(data, dict)
    assert 'total_capacity_hours' in data
    assert 'assigned_hours' in data
    assert 'utilization_pct' in data
    assert 'available_hours' in data
    assert 'ba_pm_count' in data
    
    assert isinstance(data['total_capacity_hours'], int)
    assert isinstance(data['assigned_hours'], int)
    assert isinstance(data['utilization_pct'], (int, float))
    assert isinstance(data['available_hours'], int)
    assert isinstance(data['ba_pm_count'], int)
    
    # Utilization percentage should be between 0 and 100
    assert 0 <= data['utilization_pct'] <= 100


def test_dashboard_template_contains_charts(test_client):
    """Test that dashboard template contains all seven chart canvas elements"""
    response = test_client.get('/admin/dashboard-demo')
    
    assert response.status_code == 200
    html_content = response.data.decode('utf-8')
    
    # Check for all seven chart canvas IDs
    required_chart_ids = [
        'deptHeatmap',
        't2vDist', 
        'riskIssue',
        'burnDown',
        'roiWaterfall',
        'probClusters',
        'utilGauge'
    ]
    
    for chart_id in required_chart_ids:
        assert f'id="{chart_id}"' in html_content, f"Chart canvas '{chart_id}' not found in template"


def test_all_endpoints_return_json(test_client, sample_data):
    """Test that all advanced analytics endpoints return valid JSON"""
    endpoints = [
        '/admin/api/dashboard-demo/department-heatmap',
        '/admin/api/dashboard-demo/time-to-value',
        '/admin/api/dashboard-demo/risks-issues',
        '/admin/api/dashboard-demo/milestone-burndown',
        '/admin/api/dashboard-demo/roi-waterfall',
        '/admin/api/dashboard-demo/problem-clusters',
        '/admin/api/dashboard-demo/resource-utilization'
    ]
    
    for endpoint in endpoints:
        response = test_client.get(endpoint)
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        # Ensure it's valid JSON
        try:
            json.loads(response.data)
        except json.JSONDecodeError:
            pytest.fail(f"Endpoint {endpoint} did not return valid JSON")


def test_protected_endpoints_require_auth(test_client, sample_data):
    """Test that protected dashboard endpoints require authentication"""
    protected_endpoints = [
        '/admin/api/dashboard/department-heatmap',
        '/admin/api/dashboard/time-to-value',
        '/admin/api/dashboard/risks-issues',
        '/admin/api/dashboard/milestone-burndown',
        '/admin/api/dashboard/roi-waterfall',
        '/admin/api/dashboard/problem-clusters',
        '/admin/api/dashboard/resource-utilization'
    ]
    
    for endpoint in protected_endpoints:
        response = test_client.get(endpoint)
        # Should redirect to login or return 401/403
        assert response.status_code in [302, 401, 403]


def run_advanced_analytics_tests():
    """Run all advanced analytics tests"""
    print("🧪 Running Executive Dashboard Advanced Analytics Tests...")
    
    import subprocess
    import sys
    
    # Run pytest on this specific test file
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'tests/test_dashboard_extra_charts.py', 
        '-v', '--tb=short'
    ], capture_output=True, text=True)
    
    print("Test Results:")
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    return result.returncode == 0


if __name__ == '__main__':
    run_advanced_analytics_tests()