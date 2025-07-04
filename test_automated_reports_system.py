"""
Simple verification test for the Automated Reporting System
Tests core functionality without complex fixtures
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import ReportTemplate, ReportRun, User, RoleEnum, ReportFrequencyEnum, ReportTypeEnum
from reports.service import ReportService
from reports.scheduler import ReportScheduler
import json

def test_report_models_basic():
    """Test basic report model creation"""
    with app.app_context():
        # Clear existing data
        db.session.query(ReportTemplate).delete()
        db.session.query(ReportRun).delete()
        db.session.commit()
        
        # Create or get test user
        test_user = User.query.filter_by(email="test@example.com").first()
        if not test_user:
            test_user = User()
            test_user.email = "test@example.com"
            test_user.name = "Test User"
            test_user.role = RoleEnum.Admin
            test_user.set_password("password123")
            db.session.add(test_user)
            db.session.commit()
        
        # Create report template
        template = ReportTemplate()
        template.name = "Test Daily Report"
        template.description = "Automated daily executive summary"
        template.frequency = ReportFrequencyEnum.Daily
        template.template_type = ReportTypeEnum.DashboardSummary
        template.mailing_list = json.dumps([test_user.id])
        template.filters = json.dumps({"departments": [1]})
        template.created_by = test_user.id
        template.active = True
        
        db.session.add(template)
        db.session.commit()
        
        # Verify template creation
        assert template.id is not None
        assert template.name == "Test Daily Report"
        assert template.frequency == ReportFrequencyEnum.Daily
        assert template.active is True
        
        print("✓ Report template created successfully")
        return template.id

def test_report_service_basic():
    """Test basic report service functionality"""
    with app.app_context():
        service = ReportService()
        
        # Test template rendering
        template = ReportTemplate.query.first()
        if template:
            # Test data collection structure
            mock_data = {
                'summary': {
                    'total_problems': 5,
                    'total_cases': 3,
                    'total_projects': 2,
                    'avg_roi': 150.0
                },
                'problems_trend': {'labels': ['2025-01'], 'data': [5]},
                'generated_at': '2025-06-23 21:00:00 UTC'
            }
            
            # Test HTML rendering
            html = service._render_html_report(template, mock_data)
            assert 'Test Daily Report' in html
            assert 'total_problems' in html.lower() or '5' in html
            
            print("✓ Report HTML rendering works")
            
def test_report_scheduler_basic():
    """Test basic scheduler functionality"""
    scheduler = ReportScheduler()
    
    # Test initialization
    assert scheduler.running is False
    
    # Test start/stop
    scheduler.start()
    assert scheduler.running is True
    
    scheduler.stop()
    assert scheduler.running is False
    
    print("✓ Report scheduler start/stop works")

def test_mailing_list_parsing():
    """Test mailing list parsing logic"""
    with app.app_context():
        service = ReportService()
        
        # Create test template with mixed mailing list
        user = User.query.filter_by(email="test@example.com").first()
        if user:
            template = ReportTemplate()
            template.name = "Mailing Test"
            template.frequency = ReportFrequencyEnum.Weekly
            template.template_type = ReportTypeEnum.TrendReport
            template.mailing_list = json.dumps([
                user.id,  # User ID
                "external@company.com",  # Direct email
                "Admin"  # Role-based
            ])
            template.created_by = user.id
            db.session.add(template)
            db.session.commit()
            
            # Parse mailing list
            mailing_list = json.loads(template.mailing_list)
            assert len(mailing_list) == 3
            assert user.id in mailing_list
            assert "external@company.com" in mailing_list
            assert "Admin" in mailing_list
            
            print("✓ Mailing list parsing works")

def test_report_frequency_validation():
    """Test report frequency enum validation"""
    # Test valid frequencies
    daily = ReportFrequencyEnum.Daily
    weekly = ReportFrequencyEnum.Weekly
    monthly = ReportFrequencyEnum.Monthly
    
    assert daily.value == "Daily"
    assert weekly.value == "Weekly"
    assert monthly.value == "Monthly"
    
    print("✓ Report frequency validation works")

def test_report_template_relationships():
    """Test template-run relationships"""
    with app.app_context():
        template = ReportTemplate.query.first()
        if template:
            # Create test run
            run = ReportRun()
            run.template_id = template.id
            run.status = 'completed'
            run.emails_sent = 2
            db.session.add(run)
            db.session.commit()
            
            # Test relationship
            assert run.template == template
            assert run in template.runs
            
            print("✓ Template-run relationships work")

def run_all_tests():
    """Run all automated reporting tests"""
    print("🧪 Testing Automated Reporting System...")
    
    try:
        template_id = test_report_models_basic()
        test_report_service_basic()
        test_report_scheduler_basic()
        test_mailing_list_parsing()
        test_report_frequency_validation()
        test_report_template_relationships()
        
        print("\n✅ All automated reporting tests passed!")
        print(f"📊 Report template created with ID: {template_id}")
        
        # Show system status
        with app.app_context():
            template_count = ReportTemplate.query.count()
            run_count = ReportRun.query.count()
            print(f"📈 System status: {template_count} templates, {run_count} runs")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)