"""
Comprehensive test suite for AI requirements endpoint
Tests OpenAI integration, fallback mechanisms, and database persistence
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
sys.path.append('/home/runner/workspace')

from app import app, db
from models import (
    User, Department, Problem, BusinessCase, Epic, Story,
    UserRoleEnum, StatusEnum, CaseTypeEnum, CaseDepthEnum
)
from stateless_auth import create_auth_token


@pytest.fixture
def test_app():
    """Configure Flask app for testing with in-memory SQLite database"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(test_app):
    """Create test client"""
    return test_app.test_client()


@pytest.fixture
def test_users(test_app):
    """Create test users with different roles"""
    # Create department first
    dept = Department(
        name="Technology",
        description="IT Department",
        level=1
    )
    db.session.add(dept)
    db.session.flush()
    
    # Create users
    ba_user = User(
        name="Business Analyst",
        email="ba@test.com",
        role=UserRoleEnum.BA,
        dept_id=dept.id
    )
    
    manager_user = User(
        name="Test Manager",
        email="manager@test.com", 
        role=UserRoleEnum.Manager,
        dept_id=dept.id
    )
    
    db.session.add_all([ba_user, manager_user])
    db.session.commit()
    
    return {
        'ba': ba_user,
        'manager': manager_user,
        'dept': dept
    }


@pytest.fixture
def test_business_case(test_app, test_users):
    """Create test business case with linked problem"""
    # Create problem first
    problem = Problem(
        code="P0001",
        title="System Performance Issues",
        description="Database queries are running slowly affecting user experience",
        status=StatusEnum.Open,
        reported_by=test_users['ba'].id,
        dept_id=test_users['dept'].id,
        created_at=datetime.utcnow()
    )
    db.session.add(problem)
    db.session.flush()
    
    # Create business case
    business_case = BusinessCase(
        code="C0001",
        title="Digital Tender Management System Implementation",
        description="Implement comprehensive digital tender management system to streamline procurement processes",
        status=StatusEnum.Open,
        case_type=CaseTypeEnum.Reactive,
        case_depth=CaseDepthEnum.Full,
        cost_estimate=150000.0,
        benefit_estimate=400000.0,
        roi=166.67,
        problem_id=problem.id,
        created_by=test_users['ba'].id,
        dept_id=test_users['dept'].id,
        created_at=datetime.utcnow()
    )
    db.session.add(business_case)
    db.session.commit()
    
    return business_case


def get_auth_headers(user):
    """Generate authentication headers for test requests"""
    token = create_auth_token(user.id)
    return {'Cookie': f'auth_token={token}'}


def test_ai_requirements_endpoint_success_with_openai_mock(client, test_users, test_business_case):
    """Test successful AI requirements generation with mocked OpenAI response"""
    
    # Mock OpenAI response with known data structure
    mock_openai_response = {
        "epics": [
            {
                "title": "User Authentication & Authorization",
                "description": "Comprehensive user management system with role-based access control",
                "stories": [
                    {
                        "title": "User Login System",
                        "description": "As a user, I want to securely log into the system so that I can access tender management features",
                        "acceptance_criteria": [
                            "Email/username login with password",
                            "Password strength validation",
                            "Account lockout after failed attempts"
                        ],
                        "priority": "High",
                        "effort_estimate": "8 story points"
                    }
                ]
            },
            {
                "title": "Tender Management Core",
                "description": "Essential tender creation, modification, and lifecycle management functionality",
                "stories": [
                    {
                        "title": "Create Tender Specification",
                        "description": "As a procurement officer, I want to create detailed tender specifications so that vendors understand requirements clearly",
                        "acceptance_criteria": [
                            "Tender details form with validation",
                            "Requirements specification editor",
                            "Document attachment capability"
                        ],
                        "priority": "High", 
                        "effort_estimate": "13 story points"
                    }
                ]
            }
        ]
    }
    
    with patch('ai.routes.OpenAI') as mock_openai_class:
        # Setup OpenAI mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(mock_openai_response)
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock environment variable for OpenAI API key
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            # Test data
            test_answers = {
                "q1": "Core tender management functionality with document handling",
                "q2": "Admin, Manager, Officer, Vendor roles with hierarchical permissions",
                "q3": "Integration with ERP, email systems, and document storage",
                "q4": "Support 200+ concurrent users with sub-2s response times",
                "q5": "Real-time dashboards, compliance reports, audit trails",
                "q6": "Input validation, error handling, data integrity checks",
                "q7": "Responsive web design, accessibility compliance",
                "q8": "Role-based security, data encryption, audit logging"
            }
            
            # Make request with authentication
            response = client.post(
                '/api/ai/suggest-requirements-answers',
                json={'case_id': test_business_case.id},
                headers=get_auth_headers(test_users['ba'])
            )
            
            # Assertions
            assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.get_data(as_text=True)}"
            
            response_data = response.get_json()
            assert response_data['success'] is True
            assert 'answers' in response_data
            assert len(response_data['answers']) == 8
            
            # Verify all 8 questions have answers
            for i in range(1, 9):
                assert f'q{i}' in response_data['answers']
                assert len(response_data['answers'][f'q{i}']) > 10  # Reasonable answer length
            
            print("✅ AI requirements answers generated successfully")


def test_ai_requirements_endpoint_fallback_without_openai(client, test_users, test_business_case):
    """Test fallback mechanism when OpenAI is unavailable"""
    
    # Test without OpenAI API key
    with patch.dict(os.environ, {}, clear=True):
        response = client.post(
            '/api/ai/suggest-requirements-answers',
            json={'case_id': test_business_case.id},
            headers=get_auth_headers(test_users['ba'])
        )
        
        # Assertions
        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data['success'] is True
        assert 'answers' in response_data
        assert len(response_data['answers']) == 8
        assert 'OpenAI unavailable' in response_data['message']
        
        print("✅ Fallback requirements generation working")


def test_epic_generation_endpoint_with_contextual_analysis(client, test_users, test_business_case):
    """Test epic generation with contextual analysis"""
    
    test_answers = {
        "q1": "Document management, workflow automation, approval processes",
        "q2": "Administrator, Manager, Officer, Vendor user roles",
        "q3": "ERP system integration, email notifications, API connectivity", 
        "q4": "High availability, 500+ concurrent users, sub-2s response",
        "q5": "Executive dashboards, compliance reporting, audit trails",
        "q6": "Data validation, error handling, graceful degradation",
        "q7": "Responsive design, accessibility, mobile compatibility",
        "q8": "Role-based security, encryption, compliance standards"
    }
    
    response = client.post(
        f'/api/ai/generate-requirements/{test_business_case.id}',
        json={'answers': test_answers},
        headers=get_auth_headers(test_users['ba'])
    )
    
    # Assertions
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.get_data(as_text=True)}"
    
    response_data = response.get_json()
    assert response_data['success'] is True
    assert 'epics' in response_data
    assert len(response_data['epics']) >= 2  # Should generate multiple epics
    
    # Verify epic structure
    for epic in response_data['epics']:
        assert 'title' in epic
        assert 'description' in epic  
        assert 'stories' in epic
        assert len(epic['stories']) >= 1
        
        # Verify story structure
        for story in epic['stories']:
            assert 'title' in story
            assert 'description' in story
            assert 'acceptance_criteria' in story
            assert 'priority' in story
            assert 'effort_estimate' in story
    
    # Verify database persistence for BA user
    saved_epics = Epic.query.filter_by(case_id=test_business_case.id).all()
    assert len(saved_epics) >= 2, "Epics should be saved to database for BA users"
    
    total_stories = sum(len(epic.stories) for epic in saved_epics)
    assert total_stories >= 2, "Stories should be saved to database"
    
    print(f"✅ Generated {len(response_data['epics'])} epics with {total_stories} stories")


def test_epic_generation_contextual_adaptation(client, test_users, test_business_case):
    """Test that epic generation adapts to different requirement contexts"""
    
    # Test with integration-heavy requirements
    integration_answers = {
        "q1": "Basic CRUD operations",
        "q2": "Single admin user",
        "q3": "Multiple API integrations, ERP connectivity, real-time sync",
        "q4": "Standard performance",
        "q5": "Basic reporting",
        "q6": "Standard validation",
        "q7": "Simple interface",
        "q8": "Basic security"
    }
    
    response = client.post(
        f'/api/ai/generate-requirements/{test_business_case.id}',
        json={'answers': integration_answers},
        headers=get_auth_headers(test_users['ba'])
    )
    
    assert response.status_code == 200
    response_data = response.get_json()
    
    # Should include integration-focused epic due to q3 content
    epic_titles = [epic['title'] for epic in response_data['epics']]
    integration_epic_found = any('integration' in title.lower() or 'api' in title.lower() for title in epic_titles)
    assert integration_epic_found, f"Should generate integration epic. Found: {epic_titles}"
    
    print("✅ Contextual epic adaptation working")


def test_authentication_required(client, test_business_case):
    """Test that endpoints require authentication"""
    
    # Test without authentication
    response = client.post(
        '/api/ai/suggest-requirements-answers',
        json={'case_id': test_business_case.id}
    )
    
    assert response.status_code == 401
    response_data = response.get_json()
    assert 'error' in response_data
    assert 'Authentication required' in response_data['error']
    
    print("✅ Authentication requirement enforced")


def test_invalid_case_id_handling(client, test_users):
    """Test handling of invalid case IDs"""
    
    response = client.post(
        '/api/ai/suggest-requirements-answers',
        json={'case_id': 99999},  # Non-existent case ID
        headers=get_auth_headers(test_users['ba'])
    )
    
    assert response.status_code == 404  # Should return 404 for non-existent case
    
    print("✅ Invalid case ID handling working")


def test_malformed_request_handling(client, test_users, test_business_case):
    """Test handling of malformed requests"""
    
    # Test missing case_id
    response = client.post(
        '/api/ai/suggest-requirements-answers',
        json={},  # Missing case_id
        headers=get_auth_headers(test_users['ba'])
    )
    
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data['success'] is False
    assert 'case ID' in response_data['error']
    
    # Test missing answers for epic generation
    response = client.post(
        f'/api/ai/generate-requirements/{test_business_case.id}',
        json={},  # Missing answers
        headers=get_auth_headers(test_users['ba'])
    )
    
    assert response.status_code == 400
    
    print("✅ Malformed request handling working")


if __name__ == '__main__':
    """Run tests with detailed output"""
    try:
        # Run specific tests
        pytest.main([
            __file__,
            '-v',
            '--tb=short',
            '--capture=no'
        ])
    except Exception as e:
        print(f"Test execution failed: {e}")
        import traceback
        traceback.print_exc()