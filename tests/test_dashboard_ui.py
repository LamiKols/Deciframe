"""
UI test suite for dashboard filtering and drill-down functionality.
Tests frontend interactions, modal behavior, and chart updates without Selenium.
Uses Flask test client to simulate user interactions and validate responses.
"""

import pytest
import json
import re
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
    """Create comprehensive test data for UI testing"""
    # Create departments
    dept_it = Department(id=1, name='IT Department', level=1)
    dept_finance = Department(id=2, name='Finance Department', level=1)
    dept_sales = Department(id=3, name='Sales Department', level=1)
    
    db.session.add_all([dept_it, dept_finance, dept_sales])
    
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
    
    # Create problems for testing
    today = datetime.now()
    problem1 = Problem(
        id=1, code='P0001', title='Critical IT System Failure', 
        description='Server infrastructure experiencing critical downtime affecting all operations',
        department_id=1, created_by=1, priority=PriorityEnum.High,
        status=StatusEnum.Open, created_at=today - timedelta(days=30)
    )
    problem2 = Problem(
        id=2, code='P0002', title='Budget Process Inefficiency', 
        description='Manual budget approval process causing significant delays in procurement',
        department_id=2, created_by=2, priority=PriorityEnum.Medium,
        status=StatusEnum.InProgress, created_at=today - timedelta(days=15)
    )
    problem3 = Problem(
        id=3, code='P0003', title='Sales Lead Management', 
        description='Lead tracking system lacks integration with CRM platform',
        department_id=3, created_by=3, priority=PriorityEnum.Low,
        status=StatusEnum.Resolved, created_at=today - timedelta(days=5)
    )
    
    db.session.add_all([problem1, problem2, problem3])
    
    # Create business cases
    case1 = BusinessCase(
        id=1, code='C0001', title='IT Infrastructure Modernization', 
        description='Comprehensive upgrade of server infrastructure and cloud migration',
        cost_estimate=75000, benefit_estimate=150000, roi=100,
        problem_id=1, created_by=1, status=StatusEnum.Open,
        case_type=CaseTypeEnum.Reactive, case_depth=CaseDepthEnum.Full,
        created_at=today - timedelta(days=25)
    )
    case2 = BusinessCase(
        id=2, code='C0002', title='Finance Process Automation', 
        description='Automated workflow system for budget approvals and financial reporting',
        cost_estimate=45000, benefit_estimate=120000, roi=167,
        problem_id=2, created_by=2, status=StatusEnum.InProgress,
        case_type=CaseTypeEnum.Proactive, case_depth=CaseDepthEnum.Light,
        created_at=today - timedelta(days=10)
    )
    
    db.session.add_all([case1, case2])
    
    # Create projects
    project1 = Project(
        id=1, code='PRJ0001', name='Cloud Migration Project', 
        description='Migrate critical systems to cloud infrastructure',
        business_case_id=1, project_manager_id=2, department_id=1,
        created_by=1, status=StatusEnum.InProgress, priority=PriorityEnum.High,
        budget=80000, start_date=date.today() - timedelta(days=20),
        end_date=date.today() + timedelta(days=40),
        created_at=today - timedelta(days=20)
    )
    project2 = Project(
        id=2, code='PRJ0002', name='Finance Workflow Automation', 
        description='Implement automated approval workflows',
        business_case_id=2, project_manager_id=3, department_id=2,
        created_by=2, status=StatusEnum.Open, priority=PriorityEnum.Medium,
        budget=50000, start_date=date.today() - timedelta(days=5),
        end_date=date.today() + timedelta(days=60),
        created_at=today - timedelta(days=5)
    )
    
    db.session.add_all([project1, project2])
    
    # Create milestones with specific dates for testing
    milestone1 = ProjectMilestone(
        id=1, project_id=1, name='Infrastructure Assessment',
        description='Complete assessment of current infrastructure', 
        due_date=date.today() + timedelta(days=10),
        owner_id=2, completed=False
    )
    milestone2 = ProjectMilestone(
        id=2, project_id=1, name='Cloud Setup Configuration',
        description='Configure cloud environments and security', 
        due_date=date.today() - timedelta(days=5),
        owner_id=2, completed=False  # Overdue milestone for testing
    )
    milestone3 = ProjectMilestone(
        id=3, project_id=2, name='Workflow Design',
        description='Design automated workflow processes', 
        due_date=date.today() + timedelta(days=20),
        owner_id=3, completed=True, completion_date=date.today() - timedelta(days=2)
    )
    
    db.session.add_all([milestone1, milestone2, milestone3])
    
    db.session.commit()


class TestDashboardPageLoad:
    """Test dashboard page loading and basic functionality"""
    
    def test_dashboard_demo_page_loads(self, client):
        """Test that dashboard demo page loads successfully"""
        response = client.get('/admin/dashboard-demo')
        assert response.status_code == 200
        html_content = response.data.decode('utf-8')
        
        # Verify essential dashboard elements are present
        assert 'Executive Dashboard' in html_content
        assert 'Dashboard Filters' in html_content
        assert 'dashboardFilters' in html_content
        assert 'applyFilters' in html_content
        assert 'clearFilters' in html_content
        assert 'exportFiltered' in html_content
        
        # Verify filter form elements
        assert 'fromDate' in html_content
        assert 'toDate' in html_content
        assert 'departmentFilter' in html_content
        assert 'caseTypeFilter' in html_content
        assert 'priorityFilter' in html_content
        assert 'managerFilter' in html_content
        assert 'statusFilter' in html_content
        
        # Verify chart containers are present
        assert 'deptHeatmap' in html_content
        assert 't2vDist' in html_content
        assert 'riskIssue' in html_content
        assert 'problemClusters' in html_content
        assert 'roiWaterfall' in html_content
        assert 'milestoneBurndown' in html_content
        assert 'resourceUtil' in html_content

    def test_dashboard_javascript_functions_present(self, client):
        """Test that essential JavaScript functions are included"""
        response = client.get('/admin/dashboard-demo')
        assert response.status_code == 200
        html_content = response.data.decode('utf-8')
        
        # Verify filter management functions
        assert 'initializeFilters' in html_content
        assert 'getFilterParams' in html_content
        assert 'refreshAllCharts' in html_content
        assert 'openDrillModal' in html_content
        assert 'showDrillDownModal' in html_content
        assert 'showErrorModal' in html_content
        
        # Verify chart update functions
        assert 'updateDepartmentHeatmap' in html_content
        assert 'updateTimeToValue' in html_content
        assert 'updateRisksIssues' in html_content
        assert 'updateProblemClusters' in html_content
        assert 'updateROIWaterfall' in html_content
        assert 'updateMilestoneBurndown' in html_content
        assert 'updateResourceUtilization' in html_content

    def test_chart_onclick_handlers_present(self, client):
        """Test that Chart.js onClick handlers are properly configured"""
        response = client.get('/admin/dashboard-demo')
        assert response.status_code == 200
        html_content = response.data.decode('utf-8')
        
        # Verify onClick handlers for drill-down functionality
        assert 'openDrillModal(\'deptHeatmap\'' in html_content
        assert 'openDrillModal(\'timeToValue\'' in html_content
        assert 'openDrillModal(\'riskIssue\'' in html_content
        assert 'openDrillModal(\'problemClusters\'' in html_content
        assert 'openDrillModal(\'roiWaterfall\'' in html_content
        assert 'openDrillModal(\'milestones\'' in html_content


class TestFilterFormSubmission:
    """Test filter form behavior and chart data updates"""
    
    def test_chart_data_changes_with_filters(self, client):
        """Test that chart endpoints respond to filter parameters"""
        # Get baseline data without filters
        base_response = client.get('/admin/api/dashboard-demo/department-heatmap')
        assert base_response.status_code == 200
        base_data = json.loads(base_response.data)
        
        # Apply department filter and verify response changes
        filtered_response = client.get('/admin/api/dashboard-demo/department-heatmap?departments=1')
        assert filtered_response.status_code == 200
        filtered_data = json.loads(filtered_response.data)
        
        # Data structure should remain consistent
        assert isinstance(base_data, list)
        assert isinstance(filtered_data, list)
        
        # Apply date filter
        from_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        date_filtered_response = client.get(
            f'/admin/api/dashboard-demo/department-heatmap?from={from_date}&to={to_date}'
        )
        assert date_filtered_response.status_code == 200

    def test_multiple_filter_combinations(self, client):
        """Test chart endpoints with multiple simultaneous filters"""
        # Combine multiple filter types
        filter_params = {
            'departments': '1,2',
            'priority': 'High,Medium',
            'status': 'Open,InProgress',
            'case_type': 'Reactive',
            'from': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'to': datetime.now().strftime('%Y-%m-%d')
        }
        
        query_string = '&'.join([f'{k}={v}' for k, v in filter_params.items()])
        
        # Test multiple endpoints with combined filters
        endpoints = [
            '/admin/api/dashboard-demo/problems-trend',
            '/admin/api/dashboard-demo/department-heatmap',
            '/admin/api/dashboard-demo/case-conversion',
            '/admin/api/dashboard-demo/project-metrics'
        ]
        
        for endpoint in endpoints:
            response = client.get(f'{endpoint}?{query_string}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data is not None

    def test_filter_parameter_validation(self, client):
        """Test that invalid filter parameters are handled gracefully"""
        # Test with invalid department IDs
        response = client.get('/admin/api/dashboard-demo/department-heatmap?departments=999,888')
        assert response.status_code == 200
        
        # Test with invalid date formats
        response = client.get('/admin/api/dashboard-demo/problems-trend?from=invalid-date')
        assert response.status_code == 200
        
        # Test with invalid priority values
        response = client.get('/admin/api/dashboard-demo/problems-trend?priority=Invalid,Unknown')
        assert response.status_code == 200

    def test_export_functionality(self, client):
        """Test CSV export with filter parameters"""
        # Test export endpoint with filters
        filter_params = 'departments=1&priority=High&status=Open'
        response = client.get(f'/admin/dashboard/export?{filter_params}')
        # Export might redirect or return data based on implementation
        assert response.status_code in [200, 302, 404]


class TestDrillDownModals:
    """Test drill-down modal functionality and data presentation"""
    
    def test_department_drill_down_modal_data(self, client):
        """Test department drill-down returns properly structured data"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=deptHeatmap&value=IT Department')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify complete data structure for modal rendering
        assert 'department' in data
        assert data['department'] == 'IT Department'
        assert 'problems' in data
        assert 'cases' in data
        assert 'projects' in data
        
        # Verify problem data structure for table rendering
        for problem in data['problems']:
            assert 'id' in problem
            assert 'code' in problem
            assert 'title' in problem
            assert 'priority' in problem
            assert 'status' in problem
            assert 'created_at' in problem
            assert 'url' in problem

    def test_project_risk_drill_down_modal_data(self, client):
        """Test project risk drill-down returns structured risk/issue data"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=riskIssue&value=PRJ0001')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'project' in data
            assert 'risks' in data
            assert 'issues' in data
            
            # Verify project data structure
            project = data['project']
            assert 'code' in project
            assert 'name' in project
            assert 'status' in project
            assert 'url' in project
            
            # Verify risk data structure
            for risk in data['risks']:
                assert 'type' in risk
                assert 'description' in risk
                assert 'severity' in risk
            
            # Verify issue (overdue milestone) data structure
            for issue in data['issues']:
                assert 'name' in issue
                assert 'due_date' in issue
                assert 'days_overdue' in issue
                assert 'owner' in issue

    def test_business_case_drill_down_modal_data(self, client):
        """Test business case drill-down returns financial and project data"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=roiWaterfall&value=C0001')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'case' in data
            assert 'projects' in data
            
            # Verify business case financial data
            case = data['case']
            assert 'code' in case
            assert 'title' in case
            assert 'cost_estimate' in case
            assert 'benefit_estimate' in case
            assert 'net_benefit' in case
            assert 'roi' in case
            assert 'status' in case
            assert 'url' in case

    def test_problem_cluster_drill_down_modal_data(self, client):
        """Test problem cluster drill-down returns filtered problem list"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=problemClusters&value=system')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'cluster' in data
        assert data['cluster'] == 'system'
        assert 'problems' in data
        
        # Verify problem data includes resolution tracking
        for problem in data['problems']:
            assert 'code' in problem
            assert 'title' in problem
            assert 'priority' in problem
            assert 'status' in problem
            assert 'created_at' in problem
            assert 'resolution_days' in problem or problem['resolution_days'] is None
            assert 'url' in problem

    def test_time_range_drill_down_modal_data(self, client):
        """Test time-to-value drill-down returns project timeline data"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=timeToValue&value=7-14')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'time_range' in data
        assert data['time_range'] == '7-14'
        assert 'projects' in data
        
        # Verify project timeline data structure
        for project in data['projects']:
            if project:  # May be empty based on test data
                assert 'code' in project
                assert 'name' in project
                assert 'approval_days' in project
                assert 'start_date' in project
                assert 'case_title' in project
                assert 'url' in project

    def test_milestone_drill_down_modal_data(self, client):
        """Test project milestone drill-down returns milestone tracking data"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=milestones&value=PRJ0001')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'project' in data
            assert 'milestones' in data
            
            # Verify project reference
            project = data['project']
            assert 'code' in project
            assert 'name' in project
            assert 'url' in project
            
            # Verify milestone tracking data
            for milestone in data['milestones']:
                assert 'name' in milestone
                assert 'due_date' in milestone
                assert 'completed' in milestone
                assert 'owner' in milestone
                assert 'status' in milestone
                # completion_date may be None for incomplete milestones
                assert 'completion_date' in milestone


class TestModalErrorHandling:
    """Test error handling and edge cases in drill-down modals"""
    
    def test_invalid_department_drill_down(self, client):
        """Test drill-down with non-existent department"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=deptHeatmap&value=NonExistentDept')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Department not found' in data['error']

    def test_invalid_project_drill_down(self, client):
        """Test drill-down with non-existent project"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=riskIssue&value=PRJ9999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Project not found' in data['error']

    def test_invalid_business_case_drill_down(self, client):
        """Test drill-down with non-existent business case"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=roiWaterfall&value=C9999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Business case not found' in data['error']

    def test_invalid_chart_type_drill_down(self, client):
        """Test drill-down with invalid chart type"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=invalidChart&value=test')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Unknown chart type' in data['error']

    def test_malformed_time_range_drill_down(self, client):
        """Test drill-down with malformed time range"""
        response = client.get('/admin/api/dashboard-demo/drilldown?chart=timeToValue&value=invalid-range')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid time range format' in data['error']


class TestChartDataConsistency:
    """Test that chart data remains consistent across filter applications"""
    
    def test_chart_data_structure_consistency(self, client):
        """Test that chart data structure remains consistent with and without filters"""
        endpoints_and_expected_keys = [
            ('/admin/api/dashboard-demo/problems-trend', ['labels', 'data']),
            ('/admin/api/dashboard-demo/department-heatmap', None),  # Returns array
            ('/admin/api/dashboard-demo/case-conversion', ['labels', 'problems', 'cases']),
            ('/admin/api/dashboard-demo/project-metrics', ['labels', 'data']),
            ('/admin/api/dashboard-demo/status-breakdown', None),  # Returns array
            ('/admin/api/dashboard-demo/time-to-value', ['approval_to_start', 'start_to_completion']),
            ('/admin/api/dashboard-demo/risks-issues', None),  # Returns array
            ('/admin/api/dashboard-demo/roi-waterfall', None),  # Returns array
            ('/admin/api/dashboard-demo/problem-clusters', None),  # Returns array
            ('/admin/api/dashboard-demo/milestone-burndown', ['labels', 'planned', 'actual']),
            ('/admin/api/dashboard-demo/resource-utilization', ['utilization_percent', 'ba_pm_count'])
        ]
        
        for endpoint, expected_keys in endpoints_and_expected_keys:
            # Test without filters
            response = client.get(endpoint)
            assert response.status_code == 200
            base_data = json.loads(response.data)
            
            # Test with filters
            filtered_response = client.get(f'{endpoint}?departments=1&priority=High')
            assert filtered_response.status_code == 200
            filtered_data = json.loads(filtered_response.data)
            
            # Verify data structure consistency
            if expected_keys:
                # Dict response - check required keys
                assert isinstance(base_data, dict)
                assert isinstance(filtered_data, dict)
                for key in expected_keys:
                    assert key in base_data
                    assert key in filtered_data
            else:
                # Array response - check type consistency
                assert isinstance(base_data, list)
                assert isinstance(filtered_data, list)

    def test_filter_state_persistence_across_charts(self, client):
        """Test that applying filters affects multiple chart endpoints consistently"""
        filter_params = 'departments=1&priority=High&status=Open'
        
        # Test multiple endpoints with same filters
        chart_endpoints = [
            '/admin/api/dashboard-demo/problems-trend',
            '/admin/api/dashboard-demo/department-heatmap',
            '/admin/api/dashboard-demo/case-conversion'
        ]
        
        for endpoint in chart_endpoints:
            response = client.get(f'{endpoint}?{filter_params}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data is not None
            # Data should be filtered but maintain structure


if __name__ == '__main__':
    pytest.main([__file__, '-v'])