"""
Test suite for AI Problem Refinement Assistant
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from models import User, Department, Problem
from extensions import db

class MockOpenAIResponse:
    def __init__(self, content):
        self.choices = [MagicMock()]
        self.choices[0].message.content = content

@pytest.fixture
def ai_test_client(app):
    """Create test client for AI tests"""
    with app.test_client() as client:
        with app.app_context():
            # Create test user and department
            dept = Department(name='Test Department', level=1)
            db.session.add(dept)
            db.session.commit()
            
            user = User(
                email='test@example.com',
                name='Test User',
                role='Staff',
                department_id=dept.id
            )
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            
            yield client

def test_refine_problem_endpoint_requires_auth(ai_test_client):
    """Test that AI refine endpoint requires authentication"""
    response = ai_test_client.post('/api/ai/refine-problem', 
                                  json={'text': 'Test problem'})
    assert response.status_code == 302  # Redirect to login

@patch('ai.routes.openai.ChatCompletion.create')
def test_refine_problem_success(mock_openai, ai_test_client):
    """Test successful problem refinement"""
    # Mock OpenAI response
    mock_response_text = """
**Option 1: System Performance Degradation**
Description: The application experiences significant slowdowns during peak usage hours, affecting user productivity and satisfaction.

**Option 2: Database Response Time Issues**
Description: Database queries are taking longer than expected, causing delays in data retrieval and system responsiveness.

**Option 3: Infrastructure Capacity Limitations**
Description: Current server infrastructure cannot handle the increased load, resulting in performance bottlenecks and potential downtime.
"""
    
    mock_openai.return_value = MockOpenAIResponse(mock_response_text)
    
    # Authenticate user
    with ai_test_client.session_transaction() as sess:
        user = User.query.filter_by(email='test@example.com').first()
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
    
    # Test API call
    response = ai_test_client.post('/api/ai/refine-problem', 
                                  json={'text': 'System is slow during busy times'})
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert 'variants' in data
    assert 'original' in data
    assert len(data['variants']) == 3
    
    # Check first variant structure
    variant1 = data['variants'][0]
    assert 'title' in variant1
    assert 'description' in variant1
    assert 'System Performance Degradation' in variant1['title']

@patch('ai.routes.openai.ChatCompletion.create')
def test_refine_problem_with_short_text(mock_openai, ai_test_client):
    """Test refinement with text that's too short"""
    # Authenticate user
    with ai_test_client.session_transaction() as sess:
        user = User.query.filter_by(email='test@example.com').first()
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
    
    # Test with short text
    response = ai_test_client.post('/api/ai/refine-problem', 
                                  json={'text': 'slow'})
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'too short' in data['error']

@patch('ai.routes.openai.ChatCompletion.create')
def test_refine_problem_no_text(mock_openai, ai_test_client):
    """Test refinement with no text provided"""
    # Authenticate user
    with ai_test_client.session_transaction() as sess:
        user = User.query.filter_by(email='test@example.com').first()
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
    
    # Test with no text
    response = ai_test_client.post('/api/ai/refine-problem', 
                                  json={'text': ''})
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'No text provided' in data['error']

@patch('ai.routes.openai.ChatCompletion.create')
def test_refine_problem_openai_error(mock_openai, ai_test_client):
    """Test handling of OpenAI API errors"""
    import openai
    
    # Mock OpenAI error
    mock_openai.side_effect = openai.error.RateLimitError("Rate limit exceeded")
    
    # Authenticate user
    with ai_test_client.session_transaction() as sess:
        user = User.query.filter_by(email='test@example.com').first()
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
    
    # Test API call
    response = ai_test_client.post('/api/ai/refine-problem', 
                                  json={'text': 'This is a test problem description that is long enough'})
    
    assert response.status_code == 429
    data = response.get_json()
    assert 'error' in data
    assert 'temporarily unavailable' in data['error']

def test_parse_variants_function():
    """Test the parse_variants function directly"""
    from ai.routes import parse_variants
    
    sample_response = """
**Option 1: Network Connectivity Issues**
Description: Users are experiencing intermittent network disconnections affecting their ability to access critical business applications.

**Option 2: Infrastructure Network Problems**
Description: The corporate network infrastructure shows signs of instability with frequent packet loss and connection timeouts.

**Option 3: Bandwidth Limitation Concerns**
Description: Current network bandwidth appears insufficient for the growing number of users and applications requiring connectivity.
"""
    
    variants = parse_variants(sample_response)
    
    assert len(variants) == 3
    assert variants[0]['title'] == 'Network Connectivity Issues'
    assert 'intermittent network disconnections' in variants[0]['description']
    assert variants[1]['title'] == 'Infrastructure Network Problems'
    assert variants[2]['title'] == 'Bandwidth Limitation Concerns'

def test_create_fallback_variants():
    """Test fallback variant creation"""
    from ai.routes import create_fallback_variants
    
    original_text = "This is an original problem description"
    variants = create_fallback_variants(original_text)
    
    assert len(variants) == 3
    assert all('title' in v and 'description' in v for v in variants)
    assert 'Enhanced Problem Statement' in variants[0]['title']
    assert 'Technical Problem Definition' in variants[1]['title']
    assert 'Business Impact Focus' in variants[2]['title']