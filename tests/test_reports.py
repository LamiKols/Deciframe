"""
Comprehensive Test Suite for Automated Reporting Module
Tests report generation, scheduling, email dispatch, and admin interface
"""

import pytest
import json
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from extensions import db
from models import ReportTemplate, ReportRun, User, RoleEnum, ReportFrequencyEnum, ReportTypeEnum, Department
from reports.service import ReportService
from reports.scheduler import ReportScheduler

class TestReportModels:
    """Test report model functionality"""
    
    def test_report_template_creation(self, app):
        """Test creating a report template"""
        with app.app_context():
            # Create test user
            user = User()
            user.email = "test@example.com"
            user.name = "Test User"
            user.role = RoleEnum.Admin
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
            
            # Create report template
            template = ReportTemplate()
            template.name = "Daily Executive Summary"
            template.description = "Daily overview of key metrics"
            template.frequency = ReportFrequencyEnum.Daily
            template.template_type = ReportTypeEnum.DashboardSummary
            template.mailing_list = json.dumps([user.id])
            template.filters = json.dumps({"departments": [1, 2]})
            template.created_by = user.id
            template.active = True
            
            db.session.add(template)
            db.session.commit()
            
            # Verify template
            assert template.id is not None
            assert template.name == "Daily Executive Summary"
            assert template.frequency == ReportFrequencyEnum.Daily
            assert template.template_type == ReportTypeEnum.DashboardSummary
            assert template.active is True
            assert template.creator == user
    
    def test_report_run_creation(self, app):
        """Test creating a report run"""
        with app.app_context():
            # Create test user and template
            user = User()
            user.email = "test@example.com"
            user.name = "Test User"
            user.role = RoleEnum.Admin
            user.set_password("password")
            db.session.add(user)
            
            template = ReportTemplate()
            template.name = "Test Report"
            template.frequency = ReportFrequencyEnum.Daily
            template.template_type = ReportTypeEnum.DashboardSummary
            template.created_by = user.id
            template.active = True
            db.session.add(template)
            db.session.commit()
            
            # Create report run
            run = ReportRun()
            run.template_id = template.id
            run.status = 'completed'
            run.emails_sent = 5
            run.run_at = datetime.utcnow()
            run.completed_at = datetime.utcnow()
            
            db.session.add(run)
            db.session.commit()
            
            # Verify run
            assert run.id is not None
            assert run.template == template
            assert run.status == 'completed'
            assert run.emails_sent == 5

class TestReportService:
    """Test report generation service"""
    
    @patch('requests.get')
    def test_collect_dashboard_data(self, mock_get, app):
        """Test collecting dashboard data from API endpoints"""
        with app.app_context():
            # Mock API responses
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"labels": ["2025-01"], "data": [10]}
            mock_get.return_value = mock_response
            
            # Create test template
            user = User()
            user.email = "test@example.com"
            user.name = "Test User"
            user.role = RoleEnum.Admin
            user.set_password("password")
            db.session.add(user)
            
            template = ReportTemplate()
            template.name = "Test Report"
            template.frequency = ReportFrequencyEnum.Daily
            template.template_type = ReportTypeEnum.DashboardSummary
            template.created_by = user.id
            template.filters = json.dumps({"departments": [1]})
            db.session.add(template)
            db.session.commit()
            
            # Test data collection
            service = ReportService()
            data = service._collect_dashboard_data(template)
            
            # Verify data structure
            assert 'problems_trend' in data
            assert 'case_conversion' in data
            assert 'summary' in data
            assert 'generated_at' in data
            assert 'template' in data
            
            # Verify API calls were made
            assert mock_get.call_count >= 10  # Should call multiple endpoints
    
    def test_render_dashboard_summary_template(self, app):
        """Test HTML template rendering for dashboard summary"""
        with app.app_context():
            user = User()
            user.email = "test@example.com"
            user.name = "Test User"
            user.role = RoleEnum.Admin
            user.set_password("password")
            db.session.add(user)
            
            template = ReportTemplate()
            template.name = "Dashboard Summary"
            template.template_type = ReportTypeEnum.DashboardSummary
            template.description = "Test description"
            template.created_by = user.id
            db.session.add(template)
            db.session.commit()
            
            # Test data
            data = {
                'summary': {
                    'total_problems': 15,
                    'total_cases': 8,
                    'total_projects': 3,
                    'avg_roi': 125.5,
                    'high_risk_projects': 1,
                    'overdue_milestones': 2
                },
                'problems_trend': {'labels': ['2025-01'], 'data': [10]},
                'project_metrics': {'on_time': 75, 'delayed': 25}
            }
            
            service = ReportService()
            html = service._render_html_report(template, data)
            
            # Verify HTML content
            assert 'Dashboard Summary' in html
            assert 'Total Problems' in html
            assert '15' in html  # Problem count
            assert '125.5%' in html  # ROI
            assert 'Test description' in html
    
    @patch('weasyprint.HTML')
    def test_pdf_generation(self, mock_weasyprint, app):
        """Test PDF generation from HTML"""
        with app.app_context():
            # Mock WeasyPrint
            mock_html = MagicMock()
            mock_weasyprint.return_value = mock_html
            
            user = User()
            user.email = "test@example.com"
            user.name = "Test User"
            user.role = RoleEnum.Admin
            user.set_password("password")
            db.session.add(user)
            
            template = ReportTemplate()
            template.name = "Test Report"
            template.template_type = ReportTypeEnum.DashboardSummary
            template.created_by = user.id
            db.session.add(template)
            db.session.commit()
            
            service = ReportService()
            html_content = "<html><body><h1>Test Report</h1></body></html>"
            
            # Test PDF generation
            pdf_path = service._generate_pdf(template, html_content, 1)
            
            # Verify PDF creation
            assert pdf_path is not None
            assert pdf_path.endswith('.pdf')
            assert 'report_' in pdf_path
            mock_html.write_pdf.assert_called_once()
    
    @patch('reports.service.ReportService._send_report_emails')
    @patch('reports.service.ReportService._generate_pdf')
    @patch('reports.service.ReportService._collect_dashboard_data')
    def test_generate_report_success(self, mock_collect, mock_pdf, mock_email, app):
        """Test successful report generation end-to-end"""
        with app.app_context():
            # Setup mocks
            mock_collect.return_value = {'summary': {'total_problems': 5}}
            mock_pdf.return_value = '/tmp/test_report.pdf'
            mock_email.return_value = 3
            
            # Create test template
            user = User()
            user.email = "test@example.com"
            user.name = "Test User"
            user.role = RoleEnum.Admin
            user.set_password("password")
            db.session.add(user)
            
            template = ReportTemplate()
            template.name = "Test Report"
            template.frequency = ReportFrequencyEnum.Daily
            template.template_type = ReportTypeEnum.DashboardSummary
            template.created_by = user.id
            template.active = True
            db.session.add(template)
            db.session.commit()
            
            # Generate report
            service = ReportService()
            result = service.generate_report(template.id)
            
            # Verify success
            assert result['success'] is True
            assert result['emails_sent'] == 3
            assert result['pdf_path'] == '/tmp/test_report.pdf'
            
            # Verify database updates
            template = ReportTemplate.query.get(template.id)
            assert template.last_run_at is not None
            
            run = ReportRun.query.filter_by(template_id=template.id).first()
            assert run is not None
            assert run.status == 'completed'
            assert run.emails_sent == 3

class TestReportScheduler:
    """Test report scheduling functionality"""
    
    def test_scheduler_initialization(self):
        """Test scheduler can be initialized"""
        scheduler = ReportScheduler()
        assert scheduler.running is False
        assert scheduler.scheduler_thread is None
    
    @patch('time.sleep')
    def test_scheduler_start_stop(self, mock_sleep):
        """Test scheduler start and stop"""
        scheduler = ReportScheduler()
        
        # Start scheduler
        scheduler.start()
        assert scheduler.running is True
        assert scheduler.scheduler_thread is not None
        
        # Stop scheduler
        scheduler.stop()
        assert scheduler.running is False
    
    def test_should_run_report_logic(self, app):
        """Test report scheduling logic"""
        with app.app_context():
            scheduler = ReportScheduler()
            
            # Create test template
            user = User()
            user.email = "test@example.com"
            user.name = "Test User"
            user.role = RoleEnum.Admin
            user.set_password("password")
            db.session.add(user)
            
            template = ReportTemplate()
            template.name = "Daily Report"
            template.frequency = ReportFrequencyEnum.Daily
            template.template_type = ReportTypeEnum.DashboardSummary
            template.created_by = user.id
            template.last_run_at = None  # Never run
            db.session.add(template)
            db.session.commit()
            
            # Should run if never executed
            assert scheduler._should_run_report(template, ReportFrequencyEnum.Daily) is True
            
            # Update last run to recent
            template.last_run_at = datetime.utcnow()
            db.session.commit()
            
            # Should not run if recently executed
            assert scheduler._should_run_report(template, ReportFrequencyEnum.Daily) is False
            
            # Update last run to old
            template.last_run_at = datetime.utcnow() - timedelta(days=2)
            db.session.commit()
            
            # Should run if old execution
            assert scheduler._should_run_report(template, ReportFrequencyEnum.Daily) is True
    
    @patch('reports.scheduler.ReportService.generate_report')
    def test_manual_report_execution(self, mock_generate, app):
        """Test manual report execution"""
        with app.app_context():
            # Mock successful generation
            mock_generate.return_value = {
                'success': True,
                'emails_sent': 2,
                'pdf_path': '/tmp/report.pdf'
            }
            
            # Create test template
            user = User()
            user.email = "test@example.com"
            user.name = "Test User"
            user.role = RoleEnum.Admin
            user.set_password("password")
            db.session.add(user)
            
            template = ReportTemplate()
            template.name = "Manual Report"
            template.frequency = ReportFrequencyEnum.Daily
            template.template_type = ReportTypeEnum.DashboardSummary
            template.created_by = user.id
            template.active = True
            db.session.add(template)
            db.session.commit()
            
            # Execute report manually
            scheduler = ReportScheduler()
            result = scheduler.run_report_now(template.id)
            
            # Verify execution
            assert result['success'] is True
            assert result['emails_sent'] == 2
            mock_generate.assert_called_once_with(template.id, manual_run=True)

class TestReportEmailIntegration:
    """Test email functionality with reports"""
    
    @patch('notifications.service.NotificationService._send_email_with_attachment')
    def test_email_with_pdf_attachment(self, mock_send, app):
        """Test sending emails with PDF attachments"""
        with app.app_context():
            # Mock successful email send
            mock_send.return_value = True
            
            # Create test template with mailing list
            user = User()
            user.email = "test@example.com"
            user.name = "Test User"
            user.role = RoleEnum.Admin
            user.set_password("password")
            db.session.add(user)
            
            template = ReportTemplate()
            template.name = "Email Test Report"
            template.frequency = ReportFrequencyEnum.Daily
            template.template_type = ReportTypeEnum.DashboardSummary
            template.mailing_list = json.dumps([user.id, "manager@example.com"])
            template.created_by = user.id
            db.session.add(template)
            db.session.commit()
            
            # Test email sending
            service = ReportService()
            
            # Create temporary PDF file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(b'%PDF-1.4 fake pdf content')
                tmp_path = tmp.name
            
            try:
                emails_sent = service._send_report_emails(template, tmp_path)
                
                # Verify emails sent
                assert emails_sent == 2  # Should send to 2 recipients
                assert mock_send.call_count == 2
                
                # Verify email parameters
                call_args = mock_send.call_args_list[0][1]
                assert 'DeciFrame Report' in call_args['subject']
                assert call_args['attachment_path'] == tmp_path
                
            finally:
                # Clean up
                os.unlink(tmp_path)
    
    def test_mailing_list_parsing(self, app):
        """Test parsing different mailing list formats"""
        with app.app_context():
            # Create test users
            admin = User()
            admin.email = "admin@example.com"
            admin.name = "Admin User"
            admin.role = RoleEnum.Admin
            admin.set_password("password")
            db.session.add(admin)
            
            director = User()
            director.email = "director@example.com"
            director.name = "Director User"
            director.role = RoleEnum.Director
            director.set_password("password")
            db.session.add(director)
            db.session.commit()
            
            # Create template with mixed mailing list
            template = ReportTemplate()
            template.name = "Mixed Mailing Test"
            template.frequency = ReportFrequencyEnum.Weekly
            template.template_type = ReportTypeEnum.TrendReport
            template.mailing_list = json.dumps([
                admin.id,  # User ID
                "external@example.com",  # Direct email
                "Director"  # Role-based
            ])
            template.created_by = admin.id
            db.session.add(template)
            db.session.commit()
            
            service = ReportService()
            
            # Mock email sending to test parsing logic
            with patch.object(service.notification_service, '_send_email_with_attachment', return_value=True):
                emails_sent = service._send_report_emails(template, '/fake/path.pdf')
                
                # Should send to admin, external email, and director (role-based)
                assert emails_sent >= 2  # At least admin and external email

class TestReportIntegration:
    """Integration tests for complete report workflow"""
    
    @patch('requests.get')
    @patch('weasyprint.HTML')
    @patch('notifications.service.NotificationService._send_email_with_attachment')
    def test_complete_report_workflow(self, mock_email, mock_weasyprint, mock_requests, app):
        """Test complete report generation workflow"""
        with app.app_context():
            # Setup mocks
            mock_requests.return_value.status_code = 200
            mock_requests.return_value.json.return_value = {"labels": ["2025-01"], "data": [5]}
            
            mock_html = MagicMock()
            mock_weasyprint.return_value = mock_html
            
            mock_email.return_value = True
            
            # Create test data
            user = User()
            user.email = "test@example.com"
            user.name = "Test User"
            user.role = RoleEnum.CEO
            user.set_password("password")
            db.session.add(user)
            
            template = ReportTemplate()
            template.name = "Complete Workflow Test"
            template.description = "End-to-end test report"
            template.frequency = ReportFrequencyEnum.Daily
            template.template_type = ReportTypeEnum.DashboardSummary
            template.mailing_list = json.dumps([user.id])
            template.filters = json.dumps({"departments": [1]})
            template.created_by = user.id
            template.active = True
            db.session.add(template)
            db.session.commit()
            
            # Generate report
            service = ReportService()
            result = service.generate_report(template.id)
            
            # Verify complete workflow
            assert result['success'] is True
            assert 'pdf_path' in result
            assert result['emails_sent'] >= 1
            
            # Verify database state
            updated_template = ReportTemplate.query.get(template.id)
            assert updated_template.last_run_at is not None
            
            run = ReportRun.query.filter_by(template_id=template.id).first()
            assert run is not None
            assert run.status == 'completed'
            assert run.completed_at is not None
            
            # Verify external calls
            assert mock_requests.call_count >= 10  # Dashboard API calls
            mock_html.write_pdf.assert_called_once()  # PDF generation
            mock_email.assert_called()  # Email sending

def test_report_template_validation():
    """Test report template field validation"""
    template = ReportTemplate()
    
    # Test enum validation
    with pytest.raises(ValueError):
        template.frequency = "InvalidFrequency"
    
    with pytest.raises(ValueError):
        template.template_type = "InvalidType"
    
    # Valid enums should work
    template.frequency = ReportFrequencyEnum.Daily
    template.template_type = ReportTypeEnum.DashboardSummary
    assert template.frequency == ReportFrequencyEnum.Daily
    assert template.template_type == ReportTypeEnum.DashboardSummary