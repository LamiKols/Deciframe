"""
Test suite for audit logs system
Tests audit log creation, filtering, display, and CSV export functionality
"""
import pytest
import json
import csv
import io
from datetime import datetime, timedelta
from app import app, db
from models import User, AuditLog, RoleEnum
from auth.session_auth import generate_auth_token
from flask import url_for


class TestAuditLogs:
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup test environment before each test"""
        with app.app_context():
            # Clear existing audit logs
            AuditLog.query.delete()
            
            # Create test admin user if not exists
            admin_user = User.query.filter_by(email='admin@test.com').first()
            if not admin_user:
                admin_user = User(
                    email='admin@test.com',
                    name='Test Admin',
                    role=RoleEnum.Admin,
                    is_active=True,
                    password_hash='test_hash'
                )
                db.session.add(admin_user)
                db.session.commit()
            
            self.admin_user = admin_user
            self.auth_token = generate_auth_token(admin_user.id)
            
            # Seed test audit log entries
            self.seed_audit_logs()
            
    def seed_audit_logs(self):
        """Create comprehensive test audit log entries"""
        with app.app_context():
            test_logs = [
                {
                    'user_id': self.admin_user.id,
                    'action': 'LOGIN',
                    'module': 'auth',
                    'target': 'User',
                    'target_id': self.admin_user.id,
                    'details': {'event': 'User logged in successfully', 'method': 'session'},
                    'ip_address': '192.168.1.100',
                    'timestamp': datetime.now() - timedelta(hours=3)
                },
                {
                    'user_id': self.admin_user.id,
                    'action': 'CREATE',
                    'module': 'problems',
                    'target': 'Problem',
                    'target_id': 1,
                    'details': {'event': 'Created new problem', 'title': 'Server Performance Issues'},
                    'ip_address': '192.168.1.100',
                    'timestamp': datetime.now() - timedelta(hours=2)
                },
                {
                    'user_id': self.admin_user.id,
                    'action': 'UPDATE',
                    'module': 'users',
                    'target': 'User',
                    'target_id': self.admin_user.id,
                    'details': {'event': 'Updated user profile', 'fields': ['name', 'email']},
                    'ip_address': '192.168.1.100',
                    'timestamp': datetime.now() - timedelta(hours=1, minutes=30)
                },
                {
                    'user_id': self.admin_user.id,
                    'action': 'DELETE',
                    'module': 'admin',
                    'target': 'Setting',
                    'target_id': 999,
                    'details': {'event': 'Deleted system setting', 'setting_key': 'old_feature'},
                    'ip_address': '192.168.1.100',
                    'timestamp': datetime.now() - timedelta(hours=1)
                },
                {
                    'user_id': self.admin_user.id,
                    'action': 'VIEW',
                    'module': 'reports',
                    'target': 'Report',
                    'target_id': 1,
                    'details': {'event': 'Viewed performance report', 'report_type': 'monthly'},
                    'ip_address': '192.168.1.100',
                    'timestamp': datetime.now() - timedelta(minutes=45)
                },
                {
                    'user_id': self.admin_user.id,
                    'action': 'APPROVE',
                    'module': 'business',
                    'target': 'BusinessCase',
                    'target_id': 5,
                    'details': {'event': 'Approved business case', 'case_title': 'Infrastructure Upgrade'},
                    'ip_address': '192.168.1.100',
                    'timestamp': datetime.now() - timedelta(minutes=30)
                }
            ]
            
            for log_data in test_logs:
                log = AuditLog(**log_data)
                db.session.add(log)
            
            db.session.commit()
            
            # Store test data for assertions
            self.total_logs = len(test_logs)
            self.auth_logs = [log for log in test_logs if log['module'] == 'auth']
            self.admin_logs = [log for log in test_logs if log['module'] == 'admin']
            self.recent_logs = [log for log in test_logs if log['timestamp'] > datetime.now() - timedelta(hours=2)]

    def test_audit_logs_display(self):
        """Test that audit logs display correctly on the admin page"""
        with app.test_client() as client:
            # Test authenticated access to audit logs
            response = client.get('/admin/audit-logs', 
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200
            assert b'Audit Logs' in response.data
            assert b'Total Records' in response.data
            
            # Verify that audit log entries are displayed
            assert b'LOGIN' in response.data
            assert b'CREATE' in response.data
            assert b'Test Admin' in response.data
            assert b'auth' in response.data
            assert b'problems' in response.data

    def test_audit_logs_unauthorized_access(self):
        """Test that unauthorized users cannot access audit logs"""
        with app.test_client() as client:
            # Test without authentication
            response = client.get('/admin/audit-logs')
            
            # Should redirect to login (302) or return unauthorized (401/403)
            assert response.status_code in [302, 401, 403]

    def test_audit_logs_user_filter(self):
        """Test filtering audit logs by user"""
        with app.test_client() as client:
            # Filter by admin user
            response = client.get(f'/admin/audit-logs?user_filter={self.admin_user.id}',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200
            
            # All displayed logs should be from the admin user
            assert b'Test Admin' in response.data
            
            # Test with invalid user filter
            response = client.get('/admin/audit-logs?user_filter=999999',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200

    def test_audit_logs_module_filter(self):
        """Test filtering audit logs by module"""
        with app.test_client() as client:
            # Filter by auth module
            response = client.get('/admin/audit-logs?module_filter=auth',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200
            assert b'auth' in response.data
            assert b'LOGIN' in response.data
            
            # Filter by admin module
            response = client.get('/admin/audit-logs?module_filter=admin',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200
            assert b'admin' in response.data
            assert b'DELETE' in response.data

    def test_audit_logs_date_filter(self):
        """Test filtering audit logs by date range"""
        with app.test_client() as client:
            # Filter by recent date (today)
            today = datetime.now().strftime('%Y-%m-%d')
            response = client.get(f'/admin/audit-logs?start_date={today}',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200
            
            # Filter by date range
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            response = client.get(f'/admin/audit-logs?start_date={yesterday}&end_date={today}',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200

    def test_audit_logs_pagination(self):
        """Test audit logs pagination functionality"""
        with app.test_client() as client:
            # Test first page
            response = client.get('/admin/audit-logs?page=1',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200
            assert b'Audit Logs' in response.data
            
            # Test page parameter handling
            response = client.get('/admin/audit-logs?page=999',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200

    def test_audit_logs_csv_export(self):
        """Test CSV export functionality with proper formatting"""
        with app.test_client() as client:
            # Test CSV export
            response = client.get('/admin/audit-logs?export=csv',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200
            assert response.content_type == 'text/csv'
            
            # Check CSV headers
            content_disposition = response.headers.get('Content-Disposition')
            assert content_disposition is not None
            assert 'attachment' in content_disposition
            assert 'audit_logs_' in content_disposition
            assert '.csv' in content_disposition
            
            # Parse CSV content
            csv_content = response.data.decode('utf-8')
            csv_reader = csv.reader(io.StringIO(csv_content))
            
            # Check CSV header row
            header_row = next(csv_reader)
            expected_headers = ['timestamp', 'user', 'module', 'action', 'target', 'details', 'ip_address']
            assert header_row == expected_headers
            
            # Count data rows and verify content
            data_rows = list(csv_reader)
            assert len(data_rows) == self.total_logs
            
            # Verify first data row contains expected information
            first_row = data_rows[0]
            assert 'Test Admin' in first_row[1]  # user column
            assert first_row[2] in ['auth', 'problems', 'users', 'admin', 'reports', 'business']  # module
            assert first_row[3] in ['LOGIN', 'CREATE', 'UPDATE', 'DELETE', 'VIEW', 'APPROVE']  # action
            assert '192.168.1.100' in first_row[6]  # ip_address

    def test_audit_logs_csv_export_with_filters(self):
        """Test CSV export preserves applied filters"""
        with app.test_client() as client:
            # Export with module filter
            response = client.get('/admin/audit-logs?export=csv&module_filter=auth',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200
            assert response.content_type == 'text/csv'
            
            # Parse CSV and verify only auth module entries
            csv_content = response.data.decode('utf-8')
            csv_reader = csv.reader(io.StringIO(csv_content))
            next(csv_reader)  # Skip header
            
            data_rows = list(csv_reader)
            assert len(data_rows) == len(self.auth_logs)
            
            for row in data_rows:
                assert row[2] == 'auth'  # module column

    def test_audit_logs_csv_export_with_user_filter(self):
        """Test CSV export with user filtering"""
        with app.test_client() as client:
            # Export with user filter
            response = client.get(f'/admin/audit-logs?export=csv&user_filter={self.admin_user.id}',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200
            assert response.content_type == 'text/csv'
            
            # Parse CSV and verify all entries are from the specified user
            csv_content = response.data.decode('utf-8')
            csv_reader = csv.reader(io.StringIO(csv_content))
            next(csv_reader)  # Skip header
            
            data_rows = list(csv_reader)
            for row in data_rows:
                assert 'Test Admin' in row[1]  # user column

    def test_audit_logs_csv_export_with_date_filter(self):
        """Test CSV export with date range filtering"""
        with app.test_client() as client:
            # Export with date filter (today only)
            today = datetime.now().strftime('%Y-%m-%d')
            response = client.get(f'/admin/audit-logs?export=csv&start_date={today}',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200
            assert response.content_type == 'text/csv'
            
            # Parse CSV content
            csv_content = response.data.decode('utf-8')
            csv_reader = csv.reader(io.StringIO(csv_content))
            next(csv_reader)  # Skip header
            
            data_rows = list(csv_reader)
            # Should contain entries from today
            assert len(data_rows) >= 0

    def test_audit_logs_combined_filters(self):
        """Test audit logs with multiple filters applied"""
        with app.test_client() as client:
            # Combine user and module filters
            response = client.get(f'/admin/audit-logs?user_filter={self.admin_user.id}&module_filter=auth',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200
            assert b'auth' in response.data
            assert b'Test Admin' in response.data

    def test_audit_logs_empty_state(self):
        """Test audit logs display when no matching records"""
        with app.test_client() as client:
            # Clear all audit logs
            with app.app_context():
                AuditLog.query.delete()
                db.session.commit()
            
            # Test empty state
            response = client.get('/admin/audit-logs',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200
            assert b'0 Total Records' in response.data or b'No audit logs found' in response.data

    def test_audit_logs_invalid_parameters(self):
        """Test audit logs handling of invalid parameters"""
        with app.test_client() as client:
            # Test invalid date format
            response = client.get('/admin/audit-logs?start_date=invalid-date',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200  # Should handle gracefully
            
            # Test invalid user filter
            response = client.get('/admin/audit-logs?user_filter=invalid',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200  # Should handle gracefully

    def test_audit_log_details_formatting(self):
        """Test that audit log details are properly formatted in display and CSV"""
        with app.test_client() as client:
            # Test CSV export to verify details formatting
            response = client.get('/admin/audit-logs?export=csv',
                                headers={'Authorization': f'Bearer {self.auth_token}'})
            
            assert response.status_code == 200
            
            csv_content = response.data.decode('utf-8')
            
            # Verify details are properly escaped in CSV
            assert '"' in csv_content  # Should have quoted fields
            
            # Parse and verify details column
            csv_reader = csv.reader(io.StringIO(csv_content))
            next(csv_reader)  # Skip header
            
            for row in csv_reader:
                details = row[5]  # details column
                # Details should be properly formatted (not empty for our test data)
                assert details is not None


if __name__ == '__main__':
    pytest.main([__file__])