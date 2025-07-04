"""
Tests for AI Write Summary feature
"""

import pytest
from app import app, db
from models import User, BusinessCase, Problem, Department, RoleEnum, StatusEnum, CaseTypeEnum, CaseDepthEnum
from datetime import datetime


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def auth_client(client):
    """Create authenticated test client"""
    # Create test user
    dept = Department(name='Test Department', level=1)
    db.session.add(dept)
    db.session.flush()
    
    user = User(
        name='Test User',
        email='test@example.com',
        role=RoleEnum.BA,
        dept_id=dept.id
    )
    user.set_password('password')
    db.session.add(user)
    db.session.flush()
    
    # Create test problem
    problem = Problem(
        title='Test Problem',
        description='This is a test problem requiring resolution',
        reported_by=user.id,
        dept_id=dept.id
    )
    db.session.add(problem)
    db.session.flush()
    problem.code = f'P{problem.id:04d}'
    
    # Create test business case
    business_case = BusinessCase(
        title='Test Business Case',
        description='This is a test business case description',
        cost_estimate=50000.0,
        benefit_estimate=100000.0,
        created_by=user.id,
        dept_id=dept.id,
        problem_id=problem.id,
        case_type=CaseTypeEnum.Reactive,
        case_depth=CaseDepthEnum.Light
    )
    db.session.add(business_case)
    db.session.flush()
    business_case.code = f'C{business_case.id:04d}'
    business_case.calculate_roi()
    
    db.session.commit()
    
    # Login user
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password'
    }, follow_redirects=True)
    
    return client, user, business_case


def test_write_summary_endpoint(auth_client, monkeypatch):
    """Test AI write summary endpoint with mocked OpenAI"""
    client, user, business_case = auth_client
    
    # Mock OpenAI response
    class FakeMessage:
        content = 'Executive Summary: This test business case presents a strategic initiative to address operational inefficiencies through systematic process improvements. With an estimated investment of $50,000 and projected benefits of $100,000, this initiative delivers a strong ROI of 100%. Implementation will require careful stakeholder coordination and phased execution to ensure successful delivery and realization of anticipated benefits.'
    
    class FakeChoice:
        message = FakeMessage()
    
    class FakeResponse:
        choices = [FakeChoice()]
    
    # Mock the OpenAI client
    def mock_chat_create(**kwargs):
        return FakeResponse()
    
    # Patch the OpenAI client creation and chat completion
    import ai.routes
    monkeypatch.setattr('ai.routes.OpenAI', lambda api_key: type('Client', (), {
        'chat': type('Chat', (), {
            'completions': type('Completions', (), {
                'create': mock_chat_create
            })()
        })()
    })())
    
    # Test the endpoint
    response = client.post('/api/ai/write-summary', 
                          json={'case_id': business_case.id},
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'summary' in data
    assert 'Executive Summary' in data['summary']
    
    # Verify summary was saved to database
    updated_case = BusinessCase.query.get(business_case.id)
    assert updated_case.summary is not None
    assert 'Executive Summary' in updated_case.summary


def test_write_summary_missing_case_id(auth_client):
    """Test endpoint with missing case_id"""
    client, user, business_case = auth_client
    
    response = client.post('/api/ai/write-summary', 
                          json={},
                          content_type='application/json')
    
    assert response.status_code == 404  # get_or_404 behavior


def test_write_summary_invalid_case_id(auth_client):
    """Test endpoint with invalid case_id"""
    client, user, business_case = auth_client
    
    response = client.post('/api/ai/write-summary', 
                          json={'case_id': 99999},
                          content_type='application/json')
    
    assert response.status_code == 404


def test_write_summary_fallback_no_openai(auth_client, monkeypatch):
    """Test fallback behavior when OpenAI is not available"""
    client, user, business_case = auth_client
    
    # Mock environment to simulate no OpenAI key
    monkeypatch.setenv('OPENAI_API_KEY', '')
    
    response = client.post('/api/ai/write-summary', 
                          json={'case_id': business_case.id},
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'summary' in data
    assert 'Executive Summary' in data['summary']
    assert 'strategic business initiative' in data['summary']
    
    # Verify fallback summary was saved
    updated_case = BusinessCase.query.get(business_case.id)
    assert updated_case.summary is not None
    assert 'strategic business initiative' in updated_case.summary


def test_write_summary_openai_error(auth_client, monkeypatch):
    """Test error handling when OpenAI API fails"""
    client, user, business_case = auth_client
    
    # Mock OpenAI to raise an exception
    def mock_openai_error(**kwargs):
        raise Exception("API rate limit exceeded")
    
    import ai.routes
    monkeypatch.setattr('ai.routes.OpenAI', lambda api_key: type('Client', (), {
        'chat': type('Chat', (), {
            'completions': type('Completions', (), {
                'create': mock_openai_error
            })()
        })()
    })())
    
    response = client.post('/api/ai/write-summary', 
                          json={'case_id': business_case.id},
                          content_type='application/json')
    
    assert response.status_code == 500
    data = response.get_json()
    assert 'error' in data
    assert 'AI service error' in data['error']


def test_write_summary_unauthenticated(client):
    """Test endpoint requires authentication"""
    response = client.post('/api/ai/write-summary', 
                          json={'case_id': 1},
                          content_type='application/json')
    
    # Should redirect to login or return 401/403
    assert response.status_code in [302, 401, 403]


def test_write_summary_with_solution_data(auth_client, monkeypatch):
    """Test summary generation with solution data included"""
    client, user, business_case = auth_client
    
    # Add solution data to business case
    business_case.solution_description = "Implement automated workflow system"
    db.session.commit()
    
    # Mock OpenAI with solution-aware response
    class FakeMessage:
        content = 'Executive Summary: This business case proposes implementing an automated workflow system to address operational inefficiencies. The solution will streamline processes, reduce manual errors, and improve overall productivity. With a $50,000 investment and $100,000 in projected benefits, this initiative offers excellent ROI and strategic value for organizational growth.'
    
    class FakeChoice:
        message = FakeMessage()
    
    class FakeResponse:
        choices = [FakeChoice()]
    
    def mock_chat_create(**kwargs):
        return FakeResponse()
    
    import ai.routes
    monkeypatch.setattr('ai.routes.OpenAI', lambda api_key: type('Client', (), {
        'chat': type('Chat', (), {
            'completions': type('Completions', (), {
                'create': mock_chat_create
            })()
        })()
    })())
    
    response = client.post('/api/ai/write-summary', 
                          json={'case_id': business_case.id},
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'automated workflow system' in data['summary']