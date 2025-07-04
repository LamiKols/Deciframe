"""
Tests for Data Export & Retention System
"""
import pytest
from datetime import datetime, timedelta
import csv
import io
from flask import url_for
from app import app, db
from models import Problem, BusinessCase, Project, AuditLog, RetentionLog, ArchivedProblem, ArchivedBusinessCase, ArchivedProject, User, Department


@pytest.fixture
def client():
    """Test client fixture"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def admin_user():
    """Create admin user for testing"""
    with app.app_context():
        # Create test department
        dept = Department()
        dept.name = "Test Department"
        dept.code = "TEST"
        db.session.add(dept)
        db.session.flush()
        
        # Create admin user
        user = User()
        user.email = "admin@test.com"
        user.username = "admin"
        user.first_name = "Admin"
        user.last_name = "User"
        user.role = "Admin"
        user.dept_id = dept.id
        user.is_active = True
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_data(admin_user):
    """Create test data for export/retention testing"""
    with app.app_context():
        # Create old data (for retention testing)
        old_date = datetime.now() - timedelta(days=365)
        
        # Old Problem
        old_problem = Problem()
        old_problem.title = "Old Problem"
        old_problem.description = "Old problem description"
        old_problem.dept_id = admin_user.dept_id
        old_problem.submitted_by = admin_user.id
        old_problem.created_at = old_date
        db.session.add(old_problem)
        
        # Old Business Case
        old_case = BusinessCase()
        old_case.title = "Old Business Case"
        old_case.description = "Old business case description"
        old_case.problem_id = None
        old_case.submitted_by = admin_user.id
        old_case.created_at = old_date
        db.session.add(old_case)
        
        # Old Project
        old_project = Project()
        old_project.name = "Old Project"
        old_project.description = "Old project description"
        old_project.case_id = None
        old_project.created_by = admin_user.id
        old_project.created_at = old_date
        db.session.add(old_project)
        
        # Recent data
        recent_date = datetime.now() - timedelta(days=30)
        
        # Recent Problem
        recent_problem = Problem()
        recent_problem.title = "Recent Problem"
        recent_problem.description = "Recent problem description"
        recent_problem.dept_id = admin_user.dept_id
        recent_problem.submitted_by = admin_user.id
        recent_problem.created_at = recent_date
        db.session.add(recent_problem)
        
        # Recent Business Case
        recent_case = BusinessCase()
        recent_case.title = "Recent Business Case"
        recent_case.description = "Recent business case description"
        recent_case.problem_id = None
        recent_case.submitted_by = admin_user.id
        recent_case.created_at = recent_date
        db.session.add(recent_case)
        
        # Recent Project
        recent_project = Project()
        recent_project.name = "Recent Project"
        recent_project.description = "Recent project description"
        recent_project.case_id = None
        recent_project.created_by = admin_user.id
        recent_project.created_at = recent_date
        db.session.add(recent_project)
        
        # Audit Log
        audit_log = AuditLog()
        audit_log.user_id = admin_user.id
        audit_log.action = "CREATE"
        audit_log.module = "problems"
        audit_log.target = "Problem"
        audit_log.target_id = "1"
        audit_log.details = "Test audit log"
        audit_log.timestamp = recent_date
        db.session.add(audit_log)
        
        db.session.commit()
        
        return {
            'old_problem': old_problem,
            'old_case': old_case,
            'old_project': old_project,
            'recent_problem': recent_problem,
            'recent_case': recent_case,
            'recent_project': recent_project,
            'audit_log': audit_log
        }


def login_admin(client, admin_user):
    """Helper to login admin user"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(admin_user.id)
        sess['_user_id'] = str(admin_user.id)


class TestDataExport:
    """Test data export functionality"""
    
    def test_export_page_renders(self, client, admin_user):
        """Test export page renders correctly"""
        login_admin(client, admin_user)
        response = client.get('/admin/data-management/export')
        assert response.status_code == 200
        assert b'Data Export' in response.data
        assert b'Select Data Type' in response.data
        assert b'problems' in response.data
        assert b'cases' in response.data
        assert b'projects' in response.data
        assert b'audit' in response.data
    
    def test_problems_csv_export(self, client, admin_user, test_data):
        """Test Problems CSV export"""
        login_admin(client, admin_user)
        response = client.get('/admin/data-management/download-direct?type=problems')
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'
        assert 'problems_export_' in response.headers['Content-Disposition']
        
        # Parse CSV content
        csv_content = response.data.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        assert len(rows) == 2  # Old and recent problems
        assert any(row['title'] == 'Old Problem' for row in rows)
        assert any(row['title'] == 'Recent Problem' for row in rows)
    
    def test_business_cases_csv_export(self, client, admin_user, test_data):
        """Test Business Cases CSV export"""
        login_admin(client, admin_user)
        response = client.get('/admin/data-management/download-direct?type=cases')
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'
        assert 'cases_export_' in response.headers['Content-Disposition']
        
        # Parse CSV content
        csv_content = response.data.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        assert len(rows) == 2  # Old and recent cases
        assert any(row['title'] == 'Old Business Case' for row in rows)
        assert any(row['title'] == 'Recent Business Case' for row in rows)
    
    def test_projects_csv_export(self, client, admin_user, test_data):
        """Test Projects CSV export"""
        login_admin(client, admin_user)
        response = client.get('/admin/data-management/download-direct?type=projects')
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'
        assert 'projects_export_' in response.headers['Content-Disposition']
        
        # Parse CSV content
        csv_content = response.data.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        assert len(rows) == 2  # Old and recent projects
        assert any(row['name'] == 'Old Project' for row in rows)
        assert any(row['name'] == 'Recent Project' for row in rows)
    
    def test_audit_logs_csv_export(self, client, admin_user, test_data):
        """Test Audit Logs CSV export"""
        login_admin(client, admin_user)
        response = client.get('/admin/data-management/download-direct?type=audit')
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'
        assert 'audit_export_' in response.headers['Content-Disposition']
        
        # Parse CSV content
        csv_content = response.data.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        assert len(rows) >= 1  # At least our test audit log
        assert any(row['action'] == 'CREATE' for row in rows)
        assert any(row['module'] == 'problems' for row in rows)
    
    def test_export_with_date_range(self, client, admin_user, test_data):
        """Test export with date range filtering"""
        login_admin(client, admin_user)
        
        # Export only recent data (last 60 days)
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        response = client.get(f'/admin/data-management/download-direct?type=problems&start={start_date}&end={end_date}')
        
        assert response.status_code == 200
        
        # Parse CSV content
        csv_content = response.data.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        # Should only have recent problem, not old one
        assert len(rows) == 1
        assert rows[0]['title'] == 'Recent Problem'
    
    def test_invalid_export_type(self, client, admin_user):
        """Test invalid export type returns error"""
        login_admin(client, admin_user)
        response = client.get('/admin/data-management/download-direct?type=invalid')
        
        assert response.status_code == 400
        assert b'Invalid data type' in response.data


class TestDataRetention:
    """Test data retention functionality"""
    
    def test_retention_page_renders(self, client, admin_user):
        """Test retention page renders correctly"""
        login_admin(client, admin_user)
        response = client.get('/admin/data-management/retention')
        
        assert response.status_code == 200
        assert b'Data Retention' in response.data
        assert b'Archive & Purge' in response.data
        assert b'Select Table' in response.data
        assert b'problems' in response.data
        assert b'cases' in response.data
        assert b'projects' in response.data
    
    def test_problems_retention(self, client, admin_user, test_data):
        """Test Problems retention archives and purges correctly"""
        login_admin(client, admin_user)
        
        # Archive problems older than 6 months
        cutoff_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        
        response = client.post('/admin/data-management/retention', data={
            'table': 'problems',
            'cutoff': cutoff_date
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'archived and purged' in response.data
        
        # Check old problem was archived and removed
        old_problem = Problem.query.filter_by(title='Old Problem').first()
        assert old_problem is None
        
        archived_problem = ArchivedProblem.query.filter_by(title='Old Problem').first()
        assert archived_problem is not None
        
        # Check recent problem still exists
        recent_problem = Problem.query.filter_by(title='Recent Problem').first()
        assert recent_problem is not None
        
        # Check retention log was created
        retention_log = RetentionLog.query.filter_by(table_name='problems').first()
        assert retention_log is not None
        assert retention_log.archived_count == 1
        assert retention_log.performed_by == admin_user.id
    
    def test_business_cases_retention(self, client, admin_user, test_data):
        """Test Business Cases retention archives and purges correctly"""
        login_admin(client, admin_user)
        
        # Archive cases older than 6 months
        cutoff_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        
        response = client.post('/admin/data-management/retention', data={
            'table': 'cases',
            'cutoff': cutoff_date
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'archived and purged' in response.data
        
        # Check old case was archived and removed
        old_case = BusinessCase.query.filter_by(title='Old Business Case').first()
        assert old_case is None
        
        archived_case = ArchivedBusinessCase.query.filter_by(title='Old Business Case').first()
        assert archived_case is not None
        
        # Check recent case still exists
        recent_case = BusinessCase.query.filter_by(title='Recent Business Case').first()
        assert recent_case is not None
        
        # Check retention log was created
        retention_log = RetentionLog.query.filter_by(table_name='business_cases').first()
        assert retention_log is not None
        assert retention_log.archived_count == 1
    
    def test_projects_retention(self, client, admin_user, test_data):
        """Test Projects retention archives and purges correctly"""
        login_admin(client, admin_user)
        
        # Archive projects older than 6 months
        cutoff_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        
        response = client.post('/admin/data-management/retention', data={
            'table': 'projects',
            'cutoff': cutoff_date
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'archived and purged' in response.data
        
        # Check old project was archived and removed
        old_project = Project.query.filter_by(name='Old Project').first()
        assert old_project is None
        
        archived_project = ArchivedProject.query.filter_by(name='Old Project').first()
        assert archived_project is not None
        
        # Check recent project still exists
        recent_project = Project.query.filter_by(name='Recent Project').first()
        assert recent_project is not None
        
        # Check retention log was created
        retention_log = RetentionLog.query.filter_by(table_name='projects').first()
        assert retention_log is not None
        assert retention_log.archived_count == 1
    
    def test_invalid_table_retention(self, client, admin_user):
        """Test invalid table returns error"""
        login_admin(client, admin_user)
        
        response = client.post('/admin/data-management/retention', data={
            'table': 'invalid',
            'cutoff': '2023-01-01'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid table' in response.data or b'error' in response.data.lower()
    
    def test_missing_cutoff_retention(self, client, admin_user):
        """Test missing cutoff date returns error"""
        login_admin(client, admin_user)
        
        response = client.post('/admin/data-management/retention', data={
            'table': 'problems'
            # Missing cutoff date
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show validation error or flash message
        assert b'required' in response.data.lower() or b'error' in response.data.lower()
    
    def test_no_data_to_archive(self, client, admin_user, test_data):
        """Test retention with no data to archive"""
        login_admin(client, admin_user)
        
        # Use future date so no data gets archived
        cutoff_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        response = client.post('/admin/data-management/retention', data={
            'table': 'problems',
            'cutoff': cutoff_date
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should indicate no data was archived
        assert b'0 records' in response.data or b'No records' in response.data


class TestDataManagementSecurity:
    """Test security and access control"""
    
    def test_export_requires_admin(self, client):
        """Test export requires admin authentication"""
        response = client.get('/admin/data-management/export')
        # Should redirect to login or return 401/403
        assert response.status_code in [302, 401, 403]
    
    def test_retention_requires_admin(self, client):
        """Test retention requires admin authentication"""
        response = client.get('/admin/data-management/retention')
        # Should redirect to login or return 401/403
        assert response.status_code in [302, 401, 403]
    
    def test_download_requires_admin(self, client):
        """Test download endpoint requires admin authentication"""
        response = client.get('/admin/data-management/download-direct?type=problems')
        # Should redirect to login or return 401/403
        assert response.status_code in [302, 401, 403]


if __name__ == '__main__':
    pytest.main([__file__])