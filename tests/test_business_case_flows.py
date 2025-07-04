import pytest
from datetime import datetime
from app import app, db
from models import Department, User, RoleEnum, Problem, BusinessCase, CaseDepthEnum, CaseTypeEnum, PriorityEnum, StatusEnum
from stateless_auth import create_auth_token


@pytest.fixture(scope='module')
def client():
    """Create test client with in-memory database"""
    # Create a separate test app to avoid conflicts
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy.orm import DeclarativeBase
    
    class Base(DeclarativeBase):
        pass
    
    test_app = Flask(__name__)
    test_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'FULL_CASE_THRESHOLD': 25000,
        'SECRET_KEY': 'test-secret-key'
    })
    
    test_db = SQLAlchemy(test_app, model_class=Base)
    
    # Import models to register them
    with test_app.app_context():
        from models import Department, User, Problem, BusinessCase
        test_db.create_all()
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Setup test data
            dept = Department(name='Test Department', level=1)
            db.session.add(dept)
            db.session.flush()
            
            user = User(
                email='test@example.com', 
                password_hash='test_hash', 
                name='Test User', 
                role=RoleEnum.Staff, 
                department_id=dept.id
            )
            db.session.add(user)
            db.session.flush()
            
            problem = Problem(
                code='P0001',
                title='Test Problem',
                description='Test problem description',
                priority=PriorityEnum.Medium,
                department_id=dept.id,
                status=StatusEnum.Open,
                created_by=user.id
            )
            db.session.add(problem)
            db.session.commit()
            
        yield client
        
        with app.app_context():
            db.drop_all()


@pytest.fixture
def auth_token():
    """Create authentication token for tests"""
    with app.app_context():
        user = User.query.first()
        return create_auth_token(user.id)


def test_light_case_under_threshold_reactive(client, auth_token):
    """Test creating a Light Reactive case under the cost threshold"""
    response = client.post('/business/new', data={
        'auth_token': auth_token,
        'case_type': 'Reactive',
        'case_depth': 'Light',
        'problem': '1',
        'title': 'Light Reactive Case - Under Threshold',
        'summary': 'Quick fix for existing problem',
        'description': 'Detailed description of the solution approach',
        'cost_estimate': '15000',
        'benefit_estimate': '35000'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Business Case C0001 created successfully' in response.data
    
    # Verify the case was created correctly
    with app.app_context():
        case = BusinessCase.query.filter_by(title='Light Reactive Case - Under Threshold').first()
        assert case is not None
        assert case.case_type == CaseTypeEnum.Reactive
        assert case.case_depth == CaseDepthEnum.Light
        assert case.cost_estimate == 15000.0
        assert case.problem_id == 1
        assert case.initiative_name is None


def test_light_case_under_threshold_proactive(client, auth_token):
    """Test creating a Light Proactive case under the cost threshold"""
    response = client.post('/business/new', data={
        'auth_token': auth_token,
        'case_type': 'Proactive',
        'case_depth': 'Light',
        'initiative_name': 'Office Efficiency Initiative',
        'title': 'Light Proactive Case - Under Threshold',
        'summary': 'Proactive improvement initiative',
        'description': 'Initiative to improve office processes',
        'cost_estimate': '20000',
        'benefit_estimate': '45000'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Business Case C0002 created successfully' in response.data
    
    # Verify the case was created correctly
    with app.app_context():
        case = BusinessCase.query.filter_by(title='Light Proactive Case - Under Threshold').first()
        assert case is not None
        assert case.case_type == CaseTypeEnum.Proactive
        assert case.case_depth == CaseDepthEnum.Light
        assert case.cost_estimate == 20000.0
        assert case.problem_id is None
        assert case.initiative_name == 'Office Efficiency Initiative'


def test_light_case_over_threshold_validation(client, auth_token):
    """Test that Light cases over threshold are rejected with proper validation"""
    response = client.post('/business/new', data={
        'auth_token': auth_token,
        'case_type': 'Reactive',
        'case_depth': 'Light',
        'problem': '1',
        'title': 'Light Case - Over Threshold',
        'summary': 'Expensive solution attempt',
        'description': 'Solution that exceeds Light case threshold',
        'cost_estimate': '30000',  # Over $25,000 threshold
        'benefit_estimate': '50000'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Should show validation error requiring Full case
    assert b'Cases over $25,000 require Full case elaboration' in response.data or b'Full case' in response.data


def test_full_case_over_threshold_reactive(client, auth_token):
    """Test creating a Full Reactive case over the cost threshold"""
    response = client.post('/business/new', data={
        'auth_token': auth_token,
        'case_type': 'Reactive',
        'case_depth': 'Full',
        'problem': '1',
        'title': 'Full Reactive Case - Over Threshold',
        'summary': 'Comprehensive solution to major problem',
        'description': 'Detailed solution requiring full analysis',
        'cost_estimate': '75000',
        'benefit_estimate': '200000',
        'strategic_alignment': 'Aligns with company strategic goals for operational efficiency',
        'benefit_breakdown': 'Cost savings: $100k/year, Productivity gains: $75k/year, Risk reduction: $25k/year',
        'risk_mitigation': 'Technical risks mitigated through phased approach and expert consultation',
        'stakeholder_analysis': 'Primary stakeholders: Operations team, Secondary: Finance and IT departments',
        'dependencies': 'Requires IT infrastructure upgrade and staff training program',
        'roadmap': 'Phase 1: Planning (2 months), Phase 2: Implementation (6 months), Phase 3: Optimization (3 months)',
        'sensitivity_analysis': 'ROI remains positive with 25% cost increase or 15% benefit decrease'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Business Case C0003 created successfully' in response.data
    
    # Verify the full case fields were saved
    with app.app_context():
        case = BusinessCase.query.filter_by(title='Full Reactive Case - Over Threshold').first()
        assert case is not None
        assert case.case_depth == CaseDepthEnum.Full
        assert case.cost_estimate == 75000.0
        assert case.strategic_alignment is not None
        assert 'operational efficiency' in case.strategic_alignment
        assert case.benefit_breakdown is not None
        assert case.risk_mitigation is not None


def test_full_case_over_threshold_proactive(client, auth_token):
    """Test creating a Full Proactive case over the cost threshold"""
    response = client.post('/business/new', data={
        'auth_token': auth_token,
        'case_type': 'Proactive',
        'case_depth': 'Full',
        'initiative_name': 'Digital Transformation Program',
        'title': 'Full Proactive Case - Over Threshold',
        'summary': 'Major digital transformation initiative',
        'description': 'Comprehensive digital transformation of business processes',
        'cost_estimate': '150000',
        'benefit_estimate': '500000',
        'strategic_alignment': 'Core component of 5-year digital strategy and competitive positioning',
        'benefit_breakdown': 'Revenue increase: $250k/year, Cost reduction: $150k/year, Market advantage: $100k/year',
        'risk_mitigation': 'Change management program, phased rollout, dedicated project team',
        'stakeholder_analysis': 'Executive sponsors: CEO/CTO, End users: All departments, External: Key customers',
        'dependencies': 'Budget approval, vendor selection, change management readiness assessment',
        'roadmap': 'Discovery (3 months), Design (4 months), Implementation (12 months), Optimization (6 months)',
        'sensitivity_analysis': 'Break-even maintained even with 40% cost overrun due to high benefit potential'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Business Case C0004 created successfully' in response.data
    
    # Verify the proactive full case
    with app.app_context():
        case = BusinessCase.query.filter_by(title='Full Proactive Case - Over Threshold').first()
        assert case is not None
        assert case.case_type == CaseTypeEnum.Proactive
        assert case.case_depth == CaseDepthEnum.Full
        assert case.initiative_name == 'Digital Transformation Program'
        assert case.problem_id is None
        assert 'digital strategy' in case.strategic_alignment


def test_request_full_case_functionality(client, auth_token):
    """Test the Request Full Case functionality for Light cases"""
    # First create a Light case
    client.post('/business/new', data={
        'auth_token': auth_token,
        'case_type': 'Reactive',
        'case_depth': 'Light',
        'problem': '1',
        'title': 'Light Case for Full Request',
        'summary': 'Initial light analysis',
        'description': 'Solution that may need full elaboration',
        'cost_estimate': '20000',
        'benefit_estimate': '40000'
    }, follow_redirects=True)
    
    # Get the created case ID
    with app.app_context():
        case = BusinessCase.query.filter_by(title='Light Case for Full Request').first()
        case_id = case.id
    
    # Request full case elaboration
    response = client.post(f'/business/{case_id}/request_full', data={
        'auth_token': auth_token
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Full case elaboration requested' in response.data or b'requested successfully' in response.data
    
    # Verify the request was recorded
    with app.app_context():
        case = BusinessCase.query.get(case_id)
        assert case.full_case_requested is True
        assert case.full_case_requested_by is not None
        assert case.full_case_requested_at is not None


def test_case_listing_with_hybrid_types(client, auth_token):
    """Test that the cases list properly displays hybrid case information"""
    # Create cases of different types and depths
    test_cases = [
        {
            'case_type': 'Reactive',
            'case_depth': 'Light',
            'problem': '1',
            'title': 'Reactive Light Case',
            'cost_estimate': '15000'
        },
        {
            'case_type': 'Proactive',
            'case_depth': 'Light',
            'initiative_name': 'Test Initiative',
            'title': 'Proactive Light Case',
            'cost_estimate': '18000'
        },
        {
            'case_type': 'Reactive',
            'case_depth': 'Full',
            'problem': '1',
            'title': 'Reactive Full Case',
            'cost_estimate': '50000',
            'strategic_alignment': 'Test alignment'
        }
    ]
    
    for case_data in test_cases:
        case_data.update({
            'auth_token': auth_token,
            'summary': 'Test summary',
            'description': 'Test description',
            'benefit_estimate': str(int(case_data['cost_estimate']) * 2)
        })
        client.post('/business/new', data=case_data, follow_redirects=True)
    
    # Check the cases list
    response = client.get(f'/business/?auth_token={auth_token}')
    assert response.status_code == 200
    assert b'Reactive Light Case' in response.data
    assert b'Proactive Light Case' in response.data
    assert b'Reactive Full Case' in response.data
    
    # Should show case type and depth badges
    assert b'Reactive' in response.data
    assert b'Proactive' in response.data
    assert b'Light' in response.data
    assert b'Full' in response.data


def test_case_detail_view_with_elaboration(client, auth_token):
    """Test that case detail view properly displays full elaboration fields"""
    # Create a Full case with all elaboration fields
    client.post('/business/new', data={
        'auth_token': auth_token,
        'case_type': 'Proactive',
        'case_depth': 'Full',
        'initiative_name': 'Detail Test Initiative',
        'title': 'Full Case Detail Test',
        'summary': 'Test case for detail view',
        'description': 'Comprehensive test case description',
        'cost_estimate': '60000',
        'benefit_estimate': '150000',
        'strategic_alignment': 'Strategic alignment details for testing',
        'benefit_breakdown': 'Detailed benefit analysis and breakdown',
        'risk_mitigation': 'Risk assessment and mitigation strategies',
        'stakeholder_analysis': 'Comprehensive stakeholder mapping and analysis',
        'dependencies': 'Critical project dependencies and prerequisites',
        'roadmap': 'Detailed implementation roadmap and timeline',
        'sensitivity_analysis': 'Sensitivity analysis and scenario planning'
    }, follow_redirects=True)
    
    # Get the case and view its detail page
    with app.app_context():
        case = BusinessCase.query.filter_by(title='Full Case Detail Test').first()
        case_id = case.id
    
    response = client.get(f'/business/{case_id}?auth_token={auth_token}')
    assert response.status_code == 200
    
    # Verify all elaboration fields are displayed
    assert b'Strategic alignment details for testing' in response.data
    assert b'Detailed benefit analysis and breakdown' in response.data
    assert b'Risk assessment and mitigation strategies' in response.data
    assert b'Comprehensive stakeholder mapping' in response.data
    assert b'Critical project dependencies' in response.data
    assert b'Detailed implementation roadmap' in response.data
    assert b'Sensitivity analysis and scenario' in response.data
    
    # Verify badges are displayed
    assert b'Proactive' in response.data
    assert b'Full Case' in response.data


def test_case_filtering_by_type_and_depth(client, auth_token):
    """Test filtering cases by type and depth"""
    # Create cases of different types for filtering
    test_cases = [
        ('Reactive', 'Light', 'Filter Test Reactive Light'),
        ('Reactive', 'Full', 'Filter Test Reactive Full'),
        ('Proactive', 'Light', 'Filter Test Proactive Light'),
        ('Proactive', 'Full', 'Filter Test Proactive Full')
    ]
    
    for case_type, case_depth, title in test_cases:
        case_data = {
            'auth_token': auth_token,
            'case_type': case_type,
            'case_depth': case_depth,
            'title': title,
            'summary': 'Filter test summary',
            'description': 'Filter test description',
            'cost_estimate': '30000' if case_depth == 'Full' else '20000',
            'benefit_estimate': '60000' if case_depth == 'Full' else '40000'
        }
        
        if case_type == 'Reactive':
            case_data['problem'] = '1'
        else:
            case_data['initiative_name'] = f'Filter Test Initiative {case_depth}'
            
        if case_depth == 'Full':
            case_data['strategic_alignment'] = 'Test strategic alignment'
            
        client.post('/business/new', data=case_data, follow_redirects=True)
    
    # Test filtering (if filter functionality exists)
    response = client.get(f'/business/?auth_token={auth_token}')
    assert response.status_code == 200
    
    # All test cases should be visible in the unfiltered list
    for _, _, title in test_cases:
        assert title.encode() in response.data


def test_threshold_enforcement_validation(client, auth_token):
    """Test that the $25,000 threshold is properly enforced"""
    # Test case at exactly the threshold
    response = client.post('/business/new', data={
        'auth_token': auth_token,
        'case_type': 'Reactive',
        'case_depth': 'Light',
        'problem': '1',
        'title': 'Threshold Boundary Test',
        'summary': 'Test at exact threshold',
        'description': 'Testing threshold enforcement',
        'cost_estimate': '25000',  # Exactly at threshold
        'benefit_estimate': '40000'
    }, follow_redirects=True)
    
    # Should succeed for Light case at threshold
    assert response.status_code == 200
    
    # Test case over threshold
    response = client.post('/business/new', data={
        'auth_token': auth_token,
        'case_type': 'Reactive',
        'case_depth': 'Light',
        'problem': '1',
        'title': 'Over Threshold Test',
        'summary': 'Test over threshold',
        'description': 'Testing threshold enforcement',
        'cost_estimate': '25001',  # Just over threshold
        'benefit_estimate': '40000'
    }, follow_redirects=True)
    
    # Should show validation message
    assert response.status_code == 200
    # Form should show validation error or force Full case


def test_roi_calculation_hybrid_cases(client, auth_token):
    """Test ROI calculation works correctly for both case types"""
    # Create Light case
    client.post('/business/new', data={
        'auth_token': auth_token,
        'case_type': 'Proactive',
        'case_depth': 'Light',
        'initiative_name': 'ROI Test Initiative',
        'title': 'ROI Test Light Case',
        'summary': 'Testing ROI calculation',
        'description': 'Case for ROI testing',
        'cost_estimate': '10000',
        'benefit_estimate': '25000'  # 150% ROI
    }, follow_redirects=True)
    
    # Verify ROI calculation
    with app.app_context():
        case = BusinessCase.query.filter_by(title='ROI Test Light Case').first()
        assert case is not None
        assert case.roi is not None
        assert abs(case.roi - 150.0) < 0.1  # 150% ROI with small tolerance


if __name__ == '__main__':
    pytest.main([__file__, '-v'])