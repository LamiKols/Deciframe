"""
Comprehensive test for AI Solution to Business Case workflow
Tests the complete flow from problem creation through AI solution generation to business case pre-population
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from flask import url_for
from app import app, db
from models import User, Problem, Solution, BusinessCase, Department, PriorityEnum, ImpactEnum, UrgencyEnum, StatusEnum


@pytest.fixture
def test_client():
    """Create a test client with in-memory SQLite database"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Create test department
            test_dept = Department(
                name='IT Department',
                code='IT'
            )
            db.session.add(test_dept)
            db.session.commit()
            
            # Create test user
            test_user = User(
                username='testuser',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                role='Staff',
                dept_id=test_dept.id,
                is_active=True
            )
            test_user.set_password('testpass')
            db.session.add(test_user)
            db.session.commit()
            
            yield client, test_user, test_dept
            
            db.session.remove()
            db.drop_all()


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response with 3 solution variants"""
    return {
        'choices': [{
            'message': {
                'content': json.dumps({
                    'solutions': [
                        {
                            'title': 'Process Automation Solution',
                            'description': 'Implement automated workflows to address Manual process for updating tickets by reducing manual intervention and improving efficiency.',
                            'effort': 'Medium',
                            'impact': 'High',
                            'timeline': '3-6 months'
                        },
                        {
                            'title': 'Technology Integration',
                            'description': 'Deploy integrated systems to resolve Manual process for updating tickets through better data flow and centralized management.',
                            'effort': 'High',
                            'impact': 'High',
                            'timeline': '6-12 months'
                        },
                        {
                            'title': 'Training & Documentation',
                            'description': 'Develop comprehensive training programs to mitigate Manual process for updating tickets through improved knowledge transfer.',
                            'effort': 'Low',
                            'impact': 'Medium',
                            'timeline': '1-3 months'
                        }
                    ]
                })
            }
        }]
    }


def login_user(client, user):
    """Helper function to login a user and get JWT token"""
    response = client.post('/auth/login', data={
        'email': user.email,
        'password': 'testpass'
    }, follow_redirects=True)
    
    # Extract JWT token from cookies
    jwt_cookie = None
    for cookie in client.cookie_jar:
        if cookie.name == 'auth_token':
            jwt_cookie = cookie.value
            break
    
    return jwt_cookie


def test_complete_ai_solution_to_case_flow(test_client, mock_openai_response):
    """Test the complete workflow from problem creation to business case pre-population"""
    client, test_user, test_dept = test_client
    
    # Login user
    jwt_token = login_user(client, test_user)
    assert jwt_token is not None, "User should be logged in successfully"
    
    # Step 1: Create a new Problem (so P0001 exists)
    with app.app_context():
        problem_data = {
            'title': 'Manual process for updating tickets',
            'description': 'Current ticket update process requires manual intervention causing delays',
            'priority': PriorityEnum.High.value,
            'impact': ImpactEnum.High.value,
            'urgency': UrgencyEnum.High.value,
            'org_unit_id': None,
            'reported_by': test_user.id,
            'created_by': test_user.id,
            'dept_id': test_dept.id
        }
        
        response = client.post('/problems/create', data=problem_data, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify problem was created with code P0001
        problem = Problem.query.filter_by(title='Manual process for updating tickets').first()
        assert problem is not None, "Problem should be created in database"
        assert problem.code == 'P0001', "Problem should have auto-generated code P0001"
        problem_id = problem.id
    
    # Step 2: GET problem view page and assert AI Suggest Solutions button is present
    response = client.get(f'/problems/{problem_id}')
    assert response.status_code == 200
    assert b'AI Suggest Solutions' in response.data, "AI Suggest Solutions button should be present"
    assert b'onclick="aiSolutions.generateSolutions(' in response.data, "JavaScript handler should be present"
    
    # Step 3: Mock OpenAI and POST to AI suggest solutions endpoint
    with patch('openai.ChatCompletion.create') as mock_openai:
        mock_openai.return_value = mock_openai_response
        
        response = client.post('/api/ai/suggest-solutions', 
                              json={'problem_id': problem_id},
                              headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True, "AI suggestions should succeed"
        assert len(data['solutions']) == 3, "Should return 3 solution variants"
        
        # Verify solution structure
        solution = data['solutions'][0]
        assert 'title' in solution
        assert 'description' in solution
        assert solution['title'] == 'Process Automation Solution'
        assert 'automated workflows' in solution['description']
    
    # Step 4: Simulate clicking "Create Solution" for variant #1
    solution_data = {
        'problem_id': problem_id,
        'title': 'Process Automation Solution',
        'description': 'Implement automated workflows to address Manual process for updating tickets by reducing manual intervention and improving efficiency.'
    }
    
    response = client.post('/api/solutions', 
                          json=solution_data,
                          headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 201, f"Solution creation should succeed, got: {response.get_json()}"
    response_data = response.get_json()
    assert 'solution_id' in response_data, "Response should include solution_id"
    assert 'redirect_url' in response_data, "Response should include redirect URL"
    
    solution_id = response_data['solution_id']
    redirect_url = response_data['redirect_url']
    assert f'/cases/new?solution_id={solution_id}' in redirect_url, "Should redirect to case creation with solution_id"
    
    # Step 5: Verify Solution was created in database
    with app.app_context():
        created_solution = Solution.query.filter_by(id=solution_id).first()
        assert created_solution is not None, "Solution should exist in database"
        assert created_solution.problem_id == problem_id, "Solution should be linked to correct problem"
        assert created_solution.title == 'Process Automation Solution', "Solution should have correct title"
        assert created_solution.created_by == test_user.id, "Solution should be created by test user"
        assert created_solution.status == StatusEnum.Open, "Solution should have Open status"
    
    # Step 6: GET the business case creation URL and verify pre-population
    response = client.get(f'/cases/new?solution_id={solution_id}')
    assert response.status_code == 200
    
    # Check that form fields are pre-populated
    response_text = response.data.decode('utf-8')
    assert 'Process Automation Solution' in response_text, "Solution name should be pre-filled"
    assert 'Implement automated workflows' in response_text, "Solution description should be pre-filled"
    assert problem.title in response_text, "Problem title should be referenced"
    
    # Verify the form has the correct values in input fields
    assert f'value="Process Automation Solution"' in response_text, "Solution field should be pre-filled"
    assert 'selected' in response_text, "Problem dropdown should have selection"


def test_ai_solution_creation_error_handling(test_client):
    """Test error handling in AI solution creation"""
    client, test_user, test_dept = test_client
    
    # Login user
    jwt_token = login_user(client, test_user)
    
    # Try to create solution for non-existent problem
    solution_data = {
        'problem_id': 999,
        'title': 'Test Solution',
        'description': 'Test description'
    }
    
    response = client.post('/api/solutions', 
                          json=solution_data,
                          headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 400, "Should return error for invalid problem_id"
    data = response.get_json()
    assert 'error' in data, "Should return error message"


def test_ai_solutions_authentication_required(test_client):
    """Test that AI endpoints require authentication"""
    client, test_user, test_dept = test_client
    
    # Try to access AI endpoints without authentication
    response = client.post('/api/ai/suggest-solutions', 
                          json={'problem_id': 1},
                          headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 401, "Should require authentication"
    
    response = client.post('/api/solutions', 
                          json={'problem_id': 1, 'title': 'Test', 'description': 'Test'},
                          headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 401, "Should require authentication"


def test_business_case_form_solution_integration(test_client):
    """Test that business case form properly integrates with solution data"""
    client, test_user, test_dept = test_client
    
    # Login and create problem and solution
    jwt_token = login_user(client, test_user)
    
    with app.app_context():
        # Create problem
        problem = Problem(
            title='Test Problem',
            description='Test problem description',
            priority=PriorityEnum.Medium,
            impact=ImpactEnum.Medium,
            urgency=UrgencyEnum.Medium,
            reported_by=test_user.id,
            created_by=test_user.id,
            dept_id=test_dept.id,
            code='P0002'
        )
        db.session.add(problem)
        db.session.commit()
        
        # Create solution
        solution = Solution(
            problem_id=problem.id,
            title='Test Solution',
            description='Test solution description',
            created_by=test_user.id
        )
        db.session.add(solution)
        db.session.commit()
        solution_id = solution.id
    
    # Test business case form with solution pre-population
    response = client.get(f'/cases/new?solution_id={solution_id}')
    assert response.status_code == 200
    
    response_text = response.data.decode('utf-8')
    assert 'Test Solution' in response_text, "Solution should be pre-populated"
    assert 'Test solution description' in response_text, "Solution description should be pre-populated"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])