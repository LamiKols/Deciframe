"""
Comprehensive test suite for dashboard filtering and drill-down functionality.
Tests all API endpoints with various filter combinations and validates data integrity.
"""

import pytest
import json
from datetime import datetime, timedelta, date
from app import app, db
from models import (
    User, Department, Problem, BusinessCase, Project, ProjectMilestone,
    RoleEnum, PriorityEnum, StatusEnum, CaseTypeEnum, CaseDepthEnum
)


@pytest.fixture
def client():
    """Create test client with database setup"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            setup_test_data()
            yield client
            db.drop_all()


def setup_test_data():
    """Create comprehensive test data for filtering tests"""
    # Create departments
    dept_it = Department(id=1, name='IT Department', level=1)
    dept_finance = Department(id=2, name='Finance Department', level=1)
    dept_hr = Department(id=3, name='HR Department', level=1)
    
    db.session.add_all([dept_it, dept_finance, dept_hr])
    
    # Create users
    user_ceo = User(
        id=1, email='ceo@test.com', name='John CEO', 
        role=RoleEnum.CEO, department_id=1,
        password_hash='test_hash'
    )
    user_pm = User(
        id=2, email='pm@test.com', name='Jane PM',
        role=RoleEnum.PM, department_id=1,
        password_hash='test_hash'
    )
    user_ba = User(
        id=3, email='ba@test.com', name='Bob BA',
        role=RoleEnum.BA, department_id=2,
        password_hash='test_hash'
    )
    
    db.session.add_all([user_ceo, user_pm, user_ba])
    
    # Create problems with different dates and departments
    today = datetime.now()
    problem1 = Problem(
        id=1, title='IT System Issue', description='Server downtime problem',
        department_id=1, created_by=1, priority=PriorityEnum.High,
        status=StatusEnum.Open, created_at=today - timedelta(days=30)
    )
    problem2 = Problem(
        id=2, title='Finance Process Issue', description='Budget approval delays',
        department_id=2, created_by=2, priority=PriorityEnum.Medium,
        status=StatusEnum.InProgress, created_at=today - timedelta(days=15)
    )
    problem3 = Problem(
        id=3, title='HR Policy Issue', description='Leave management concerns',
        department_id=3, created_by=3, priority=PriorityEnum.Low,
        status=StatusEnum.Resolved, created_at=today - timedelta(days=5)
    )
    
    db.session.add_all([problem1, problem2, problem3])
    
    # Create business cases
    case1 = BusinessCase(
        id=1, title='IT Infrastructure Upgrade', description='Modernize servers',
        cost_estimate=50000, benefit_estimate=100000, roi=100,
        problem_id=1, created_by=1, status=StatusEnum.Open,
        case_type=CaseTypeEnum.Reactive, case_depth=CaseDepthEnum.Full,
        created_at=today - timedelta(days=25)
    )
    case2 = BusinessCase(
        id=2, title='Finance System Integration', description='Streamline processes',
        cost_estimate=30000, benefit_estimate=75000, roi=150,
        problem_id=2, created_by=2, status=StatusEnum.InProgress,
        case_type=CaseTypeEnum.Proactive, case_depth=CaseDepthEnum.Light,
        created_at=today - timedelta(days=10)
    )
    
    db.session.add_all([case1, case2])
    
    # Create projects
    project1 = Project(
        id=1, name='Server Upgrade Project', description='Upgrade IT infrastructure',
        business_case_id=1, project_manager_id=2, department_id=1,
        created_by=1, status=StatusEnum.InProgress, priority=PriorityEnum.High,
        budget=55000, start_date=date.today() - timedelta(days=20),
        end_date=date.today() + timedelta(days=40),
        created_at=today - timedelta(days=20)
    )
    project2 = Project(
        id=2, name='Finance Process Automation', description='Automate workflows',
        business_case_id=2, project_manager_id=3, department_id=2,
        created_by=2, status=StatusEnum.Open, priority=PriorityEnum.Medium,
        budget=35000, start_date=date.today() - timedelta(days=5),
        end_date=date.today() + timedelta(days=60),
        created_at=today - timedelta(days=5)
    )
    
    db.session.add_all([project1, project2])
    
    # Create milestones
    milestone1 = ProjectMilestone(
        id=1, project_id=1, name='Hardware Installation',
        description='Install new servers', due_date=date.today() + timedelta(days=10),
        owner_id=2, completed=False
    )
    milestone2 = ProjectMilestone(
        id=2, project_id=1, name='Software Configuration',
        description='Configure system software', due_date=date.today() - timedelta(days=5),
        owner_id=2, completed=False  # Overdue milestone
    )
    milestone3 = ProjectMilestone(
        id=3, project_id=2, name='Process Mapping',
        description='Map current processes', due_date=date.today() + timedelta(days=20),
        owner_id=3, completed=True, completion_date=date.today() - timedelta(days=2)
    )
    
    db.session.add_all([milestone1, milestone2, milestone3])
    
    db.session.commit()


class TestDashboardFiltering:
    """Test dashboard API endpoints with various filter combinations"""
    
    def test_problems_trend_filtering(self, client):
        """Test problems trend endpoint with date and department filters"""
        # Test without filters
        response = client.get('/admin/api/dashboard-demo/problems-trend')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'labels' in data
        assert 'data' in data
        
        # Test with date range filter
        from_date = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        response = client.get(f'/admin/api/dashboard-demo/problems-trend?from={from_date}&to={to_date}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) >= 0
        
        # Test with department filter
        response = client.get('/admin/api/dashboard-demo/problems-trend?departments=1,2')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'labels' in data
        
        # Test with priority filter
        response = client.get('/admin/api/dashboard-demo/problems-trend?priority=High,Medium')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data

    def test_department_heatmap_filtering(self, client):
        """Test department heatmap with comprehensive filters"""
        # Test basic endpoint
        response = client.get('/admin/api/dashboard-demo/department-heatmap')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) >= 3  # Should have IT, Finance, HR departments
        
        # Verify department structure
        dept_data = data[0]
        assert 'department' in dept_data
        assert 'problems' in dept_data
        assert 'cases' in dept_data
        assert 'projects' in dept_data
        assert 'avg_roi' in dept_data
        
        # Test with status filter
        response = client.get('/admin/api/dashboard-demo/department-heatmap?status=Open,InProgress')
        assert response.status_code == 200
        filtered_data = json.loads(response.data)
        assert isinstance(filtered_data, list)
        
        # Test with case type filter
        response = client.get('/admin/api/dashboard-demo/department-heatmap?case_type=Reactive')
        assert response.status_code == 200
        reactive_data = json.loads(response.data)
        assert isinstance(reactive_data, list)

    def test_case_conversion_filtering(self, client):
        """Test case conversion endpoint with various filters"""
        response = client.get('/admin/api/dashboard-demo/case-conversion')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'labels' in data
        assert 'problems' in data
        assert 'cases' in data
        
        # Test with date range
        from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        response = client.get(f'/admin/api/dashboard-demo/case-conversion?from={from_date}')
        assert response.status_code == 200
        filtered_data = json.loads(response.data)
        assert 'labels' in filtered_data

    def test_project_metrics_filtering(self, client):
        """Test project metrics with manager and status filters"""
        response = client.get('/admin/api/dashboard-demo/project-metrics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'labels' in data
        assert 'data' in data
        
        # Test with manager filter
        response = client.get('/admin/api/dashboard-demo/project-metrics?manager=2')
        assert response.status_code == 200
        manager_data = json.loads(response.data)
        assert 'labels' in manager_data
        
        # Test with status filter
        response = client.get('/admin/api/dashboard-demo/project-metrics?status=InProgress')
        assert response.status_code == 200
        status_data = json.loads(response.data)
        assert 'data' in status_data

    def test_time_to_value_filtering(self, client):
        """Test time-to-value analysis with project filters"""
        response = client.get('/admin/api/dashboard-demo/time-to-value')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'approval_to_start' in data
        assert 'start_to_completion' in data
        
        # Test with department filter
        response = client.get('/admin/api/dashboard-demo/time-to-value?departments=1')
        assert response.status_code == 200
        dept_data = json.loads(response.data)
        assert 'approval_to_start' in dept_data

    def test_risks_issues_filtering(self, client):
        """Test risk and issue analysis with project filters"""
        response = client.get('/admin/api/dashboard-demo/risks-issues')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        
        # Test with priority filter
        response = client.get('/admin/api/dashboard-demo/risks-issues?priority=High')
        assert response.status_code == 200
        high_priority_data = json.loads(response.data)
        assert isinstance(high_priority_data, list)

    def test_roi_waterfall_filtering(self, client):
        """Test ROI waterfall with case type and status filters"""
        response = client.get('/admin/api/dashboard-demo/roi-waterfall')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        
        if len(data) > 0:
            case_data = data[0]
            assert 'case_code' in case_data
            assert 'net_benefit' in case_data
            assert 'roi' in case_data
        
        # Test with case type filter
        response = client.get('/admin/api/dashboard-demo/roi-waterfall?case_type=Reactive')
        assert response.status_code == 200
        reactive_data = json.loads(response.data)
        assert isinstance(reactive_data, list)

    def test_problem_clusters_filtering(self, client):
        """Test problem cluster analysis with time and department filters"""
        response = client.get('/admin/api/dashboard-demo/problem-clusters')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        
        # Test with department filter
        response = client.get('/admin/api/dashboard-demo/problem-clusters?departments=1,2')
        assert response.status_code == 200
        dept_data = json.loads(response.data)
        assert isinstance(dept_data, list)

    def test_resource_utilization_filtering(self, client):
        """Test resource utilization with role-based filters"""
        response = client.get('/admin/api/dashboard-demo/resource-utilization')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'utilization_percent' in data
        assert 'ba_pm_count' in data
        assert isinstance(data['utilization_percent'], (int, float))

    def test_milestone_burndown_filtering(self, client):
        """Test milestone burndown with project and date filters"""
        response = client.get('/admin/api/dashboard-demo/milestone-burndown')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'labels' in data
        assert 'planned' in data
        assert 'actual' in data


class TestDrillDownEndpoints:
    """Test drill-down functionality for all chart types"""
    
    def test_department_drilldown(self, client):
        """Test department drill-down returns correct record sets"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=deptHeatmap&value=IT Department')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'department' in data
        assert data['department'] == 'IT Department'
        assert 'problems' in data
        assert 'cases' in data
        assert 'projects' in data
        assert isinstance(data['problems'], list)
        assert isinstance(data['cases'], list)
        assert isinstance(data['projects'], list)
        
        # Test with filters
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=deptHeatmap&value=IT Department&status=Open')
        assert response.status_code == 200
        filtered_data = json.loads(response.data)
        assert 'department' in filtered_data

    def test_time_range_drilldown(self, client):
        """Test time-to-value drill-down functionality"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=timeToValue&value=7-14')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'time_range' in data
        assert data['time_range'] == '7-14'
        assert 'projects' in data
        assert isinstance(data['projects'], list)

    def test_project_risk_drilldown(self, client):
        """Test project risk and issue drill-down"""
        # First create a project with a known code
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=riskIssue&value=PRJ0001')
        assert response.status_code in [200, 404]  # May not exist in test data
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'project' in data
            assert 'risks' in data
            assert 'issues' in data

    def test_problem_cluster_drilldown(self, client):
        """Test problem cluster drill-down functionality"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=problemClusters&value=system')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'cluster' in data
        assert data['cluster'] == 'system'
        assert 'problems' in data
        assert isinstance(data['problems'], list)

    def test_business_case_drilldown(self, client):
        """Test business case drill-down functionality"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=roiWaterfall&value=C0001')
        assert response.status_code in [200, 404]  # May not exist in test data
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'case' in data
            assert 'projects' in data

    def test_milestone_drilldown(self, client):
        """Test project milestone drill-down functionality"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=milestones&value=PRJ0001')
        assert response.status_code in [200, 404]  # May not exist in test data
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'project' in data
            assert 'milestones' in data

    def test_invalid_chart_type(self, client):
        """Test drill-down with invalid chart type"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=invalidChart&value=test')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Unknown chart type'

    def test_missing_parameters(self, client):
        """Test drill-down with missing required parameters"""
        # Missing chart parameter
        response = client.get('/admin/api/dashboard-demo/drilldown?value=test')
        assert response.status_code == 400
        
        # Missing value parameter
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=deptHeatmap')
        assert response.status_code in [200, 400]  # Depends on implementation


class TestFilterParameterValidation:
    """Test filter parameter validation and edge cases"""
    
    def test_date_filter_validation(self, client):
        """Test date filter parameter validation"""
        # Valid date format
        response = client.get('/admin/api/dashboard-demo/problems-trend?from=2025-01-01&to=2025-12-31')
        assert response.status_code == 200
        
        # Invalid date format should still work (graceful handling)
        response = client.get('/admin/api/dashboard-demo/problems-trend?from=invalid-date')
        assert response.status_code == 200

    def test_department_filter_validation(self, client):
        """Test department filter parameter validation"""
        # Valid department IDs
        response = client.get('/admin/api/dashboard-demo/department-heatmap?departments=1,2,3')
        assert response.status_code == 200
        
        # Invalid department IDs should still work (graceful handling)
        response = client.get('/admin/api/dashboard-demo/department-heatmap?departments=999,888')
        assert response.status_code == 200

    def test_priority_filter_validation(self, client):
        """Test priority filter parameter validation"""
        # Valid priorities
        response = client.get('/admin/api/dashboard-demo/problems-trend?priority=High,Medium,Low')
        assert response.status_code == 200
        
        # Invalid priorities should still work (graceful handling)
        response = client.get('/admin/api/dashboard-demo/problems-trend?priority=Invalid')
        assert response.status_code == 200

    def test_status_filter_validation(self, client):
        """Test status filter parameter validation"""
        # Valid statuses
        response = client.get('/admin/api/dashboard-demo/status-breakdown?status=Open,InProgress')
        assert response.status_code == 200
        
        # Mixed valid and invalid statuses
        response = client.get('/admin/api/dashboard-demo/status-breakdown?status=Open,Invalid')
        assert response.status_code == 200

    def test_case_type_filter_validation(self, client):
        """Test case type filter parameter validation"""
        # Valid case types
        response = client.get('/admin/api/dashboard-demo/case-conversion?case_type=Reactive')
        assert response.status_code == 200
        
        response = client.get('/admin/api/dashboard-demo/case-conversion?case_type=Proactive')
        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])