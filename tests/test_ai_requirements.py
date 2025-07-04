"""
Test suite for AI Requirements Generation functionality
Tests API endpoints, OpenAI integration, and fallback systems
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import url_for
from models import User, BusinessCase, Problem, Solution, Department
from app import app, db
from stateless_auth import generate_jwt_token

class TestAIRequirementsAPI:
    """Test the AI requirements generation API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client with database setup"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    @pytest.fixture
    def test_data(self, client):
        """Create test data for requirements generation"""
        with app.app_context():
            # Create department
            dept = Department(name='Engineering', level=1)
            db.session.add(dept)
            db.session.flush()
            
            # Create user
            user = User(
                name='Test User',
                email='test@example.com',
                password_hash='hashed_password',
                role='Manager',
                department_id=dept.id
            )
            db.session.add(user)
            db.session.flush()
            
            # Create problem
            problem = Problem(
                title='System Performance Issues',
                description='Application is running slowly and affecting user productivity',
                department_id=dept.id,
                created_by=user.id
            )
            db.session.add(problem)
            db.session.flush()
            
            # Create solution
            solution = Solution(
                problem_id=problem.id,
                name='Performance Optimization',
                description='Implement caching and database optimization',
                created_by=user.id
            )
            db.session.add(solution)
            db.session.flush()
            
            # Create business case
            business_case = BusinessCase(
                title='Performance Enhancement Initiative',
                description='Improve system performance to enhance user experience',
                cost_estimate=50000.0,
                benefit_estimate=150000.0,
                problem_id=problem.id,
                solution_id=solution.id,
                created_by=user.id
            )
            db.session.add(business_case)
            db.session.commit()
            
            return {
                'user': user,
                'business_case': business_case,
                'problem': problem,
                'solution': solution,
                'department': dept
            }
    
    def test_draft_requirements_missing_case_id(self, client, test_data):
        """Test API returns error when case_id is missing"""
        user = test_data['user']
        token = generate_jwt_token(user.id)
        
        response = client.post('/api/ai/draft-requirements',
                             json={'answers': ['Test answer']},
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Business case ID is required' in data['error']
    
    def test_draft_requirements_invalid_case_id(self, client, test_data):
        """Test API returns 404 for non-existent case"""
        user = test_data['user']
        token = generate_jwt_token(user.id)
        
        response = client.post('/api/ai/draft-requirements',
                             json={'case_id': 99999, 'answers': ['Test answer']},
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 404
    
    @patch('ai.routes.os.environ.get')
    def test_draft_requirements_no_openai_key_fallback(self, mock_env, client, test_data):
        """Test fallback system when OpenAI API key is not available"""
        # Mock no OpenAI key
        mock_env.return_value = None
        
        user = test_data['user']
        business_case = test_data['business_case']
        token = generate_jwt_token(user.id)
        
        answers = [
            'Primary users are sales managers and representatives',
            'Need reporting dashboard and CRM integration',
            'Must integrate with Salesforce and email systems',
            'Handle 100 concurrent users with 2-second response time'
        ]
        
        response = client.post('/api/ai/draft-requirements',
                             json={'case_id': business_case.id, 'answers': answers},
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['fallback'] is True
        assert 'epics' in data
        assert len(data['epics']) > 0
        
        # Validate epic structure
        epic = data['epics'][0]
        assert 'title' in epic
        assert 'description' in epic
        assert 'user_stories' in epic
        assert len(epic['user_stories']) > 0
        
        # Validate user story structure
        story = epic['user_stories'][0]
        assert 'title' in story
        assert 'description' in story
        assert 'acceptance_criteria' in story
        assert 'priority' in story
        assert 'effort_estimate' in story
    
    @patch('ai.routes.openai.ChatCompletion.create')
    @patch('ai.routes.os.environ.get')
    def test_draft_requirements_openai_success(self, mock_env, mock_openai, client, test_data):
        """Test successful OpenAI API integration"""
        # Mock OpenAI key exists
        mock_env.return_value = 'test-api-key'
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "epics": [
                {
                    "title": "User Management System",
                    "description": "Comprehensive user management with role-based access",
                    "user_stories": [
                        {
                            "title": "User Registration",
                            "description": "As a new user, I want to register an account so that I can access the system",
                            "acceptance_criteria": [
                                "Given I'm on the registration page, when I submit valid details, then my account is created",
                                "Given I submit invalid email, when I try to register, then I see appropriate error message"
                            ],
                            "priority": "High",
                            "effort_estimate": "3-5 story points"
                        }
                    ]
                },
                {
                    "title": "Reporting Dashboard",
                    "description": "Real-time reporting and analytics dashboard",
                    "user_stories": [
                        {
                            "title": "Dashboard View",
                            "description": "As a manager, I want to view key metrics so that I can track performance",
                            "acceptance_criteria": [
                                "Given I'm logged in as manager, when I access dashboard, then I see current metrics",
                                "Given metrics are updated, when I refresh dashboard, then I see latest data"
                            ],
                            "priority": "Medium",
                            "effort_estimate": "5-8 story points"
                        }
                    ]
                }
            ]
        })
        mock_openai.return_value = mock_response
        
        user = test_data['user']
        business_case = test_data['business_case']
        token = generate_jwt_token(user.id)
        
        answers = [
            'Primary users are sales managers',
            'Need reporting dashboard',
            'Integration with CRM systems',
            'High performance requirements'
        ]
        
        response = client.post('/api/ai/draft-requirements',
                             json={'case_id': business_case.id, 'answers': answers},
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['fallback'] is False
        assert len(data['epics']) == 2
        
        # Validate first epic
        epic1 = data['epics'][0]
        assert epic1['title'] == 'User Management System'
        assert epic1['description'] == 'Comprehensive user management with role-based access'
        assert len(epic1['user_stories']) == 1
        
        # Validate user story
        story = epic1['user_stories'][0]
        assert story['title'] == 'User Registration'
        assert story['priority'] == 'High'
        assert len(story['acceptance_criteria']) == 2
        
        # Verify OpenAI was called with correct parameters
        mock_openai.assert_called_once()
        call_args = mock_openai.call_args
        assert call_args[1]['model'] == 'gpt-4'
        assert call_args[1]['temperature'] == 0.2
        assert len(call_args[1]['messages']) == 2
        assert 'system' in call_args[1]['messages'][0]['role']
        assert 'user' in call_args[1]['messages'][1]['role']
    
    @patch('ai.routes.openai.ChatCompletion.create')
    @patch('ai.routes.os.environ.get')
    def test_draft_requirements_openai_failure_fallback(self, mock_env, mock_openai, client, test_data):
        """Test fallback when OpenAI API fails"""
        # Mock OpenAI key exists
        mock_env.return_value = 'test-api-key'
        
        # Mock OpenAI failure
        mock_openai.side_effect = Exception("API rate limit exceeded")
        
        user = test_data['user']
        business_case = test_data['business_case']
        token = generate_jwt_token(user.id)
        
        response = client.post('/api/ai/draft-requirements',
                             json={'case_id': business_case.id, 'answers': ['Test answer']},
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['fallback'] is True
        assert 'note' in data
        assert 'API rate limit exceeded' in data['note']
    
    def test_draft_requirements_unauthorized(self, client, test_data):
        """Test API requires authentication"""
        business_case = test_data['business_case']
        
        response = client.post('/api/ai/draft-requirements',
                             json={'case_id': business_case.id, 'answers': ['Test']})
        
        assert response.status_code == 401

class TestRequirementsParser:
    """Test the requirements parsing utilities"""
    
    def test_parse_requirements_json_epics(self):
        """Test parsing valid JSON epics format"""
        from ai.routes import parse_requirements
        
        json_text = json.dumps({
            "epics": [
                {
                    "title": "Test Epic",
                    "description": "Test description",
                    "user_stories": [
                        {
                            "title": "Test Story",
                            "description": "As a user, I want to test",
                            "acceptance_criteria": ["Given test, when test, then test"],
                            "priority": "High"
                        }
                    ]
                }
            ]
        })
        
        result = parse_requirements(json_text)
        assert len(result) == 1
        assert result[0]['title'] == 'Test Epic'
        assert len(result[0]['stories']) == 1
        assert result[0]['stories'][0]['title'] == 'Test Story'
    
    def test_parse_requirements_invalid_json_fallback(self):
        """Test fallback parsing for invalid JSON"""
        from ai.routes import parse_requirements
        
        invalid_text = "This is not valid JSON but contains requirements"
        
        result = parse_requirements(invalid_text)
        assert len(result) >= 1
        assert 'title' in result[0]
        assert 'description' in result[0]
        assert 'stories' in result[0]
    
    def test_format_criteria_list(self):
        """Test formatting acceptance criteria from list"""
        from ai.routes import format_criteria
        
        criteria_list = ["Criterion 1", "Criterion 2", "Criterion 3"]
        formatted = format_criteria(criteria_list)
        
        assert "• Criterion 1" in formatted
        assert "• Criterion 2" in formatted
        assert "• Criterion 3" in formatted
    
    def test_format_criteria_string(self):
        """Test formatting acceptance criteria from string"""
        from ai.routes import format_criteria
        
        criteria_string = "Single acceptance criterion"
        formatted = format_criteria(criteria_string)
        
        assert formatted == criteria_string

class TestJavaScriptIntegration:
    """Test JavaScript integration aspects (structure validation)"""
    
    def test_case_requirements_ai_js_structure(self):
        """Verify the JavaScript file exists and has expected structure"""
        import os
        js_file_path = 'static/js/case_requirements_ai.js'
        
        assert os.path.exists(js_file_path), "JavaScript file should exist"
        
        with open(js_file_path, 'r') as f:
            content = f.read()
        
        # Check for essential components
        assert 'questions' in content, "Should contain questions array"
        assert 'showStep' in content, "Should contain showStep function"
        assert 'nextStep' in content, "Should contain nextStep handling"
        assert '/api/ai/draft-requirements' in content, "Should call correct API endpoint"
        assert 'bootstrap.Modal' in content, "Should use Bootstrap modal"
    
    def test_requirements_template_structure(self):
        """Verify the requirements template has expected elements"""
        template_path = 'business/templates/requirements.html'
        
        assert os.path.exists(template_path), "Requirements template should exist"
        
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Check for essential elements
        assert 'aiDraftReqBtn' in content, "Should have AI draft button"
        assert 'aiReqModal' in content, "Should have AI modal"
        assert 'wizard-question' in content, "Should have wizard question element"
        assert 'wizard-answer' in content, "Should have wizard answer element"
        assert 'case_requirements_ai.js' in content, "Should include JavaScript file"

def test_theme_extraction():
    """Test theme extraction from user answers"""
    from ai.routes import extract_themes_from_answers
    
    answers = [
        "We need reporting capabilities for managers",
        "System should integrate with existing CRM",
        "Performance must be fast for 100 users",
        "Security is important for user data"
    ]
    
    themes = extract_themes_from_answers(answers)
    
    # Should detect multiple themes
    assert 'Reporting' in themes
    assert 'Integration' in themes  
    assert 'Performance' in themes
    assert 'Security' in themes

def test_fallback_requirements_generation():
    """Test fallback requirements generation"""
    from ai.routes import generate_fallback_requirements
    from models import BusinessCase
    
    # Create mock business case
    mock_case = BusinessCase()
    mock_case.title = "Test Business Case"
    mock_case.cost_estimate = 10000
    mock_case.benefit_estimate = 30000
    
    answers = ["Need user management", "Reporting required", "Mobile support"]
    
    epics = generate_fallback_requirements(mock_case, answers)
    
    assert len(epics) >= 2, "Should generate multiple epics"
    
    # Check structure
    for epic in epics:
        assert 'title' in epic
        assert 'description' in epic
        assert 'user_stories' in epic
        assert len(epic['user_stories']) > 0
        
        for story in epic['user_stories']:
            assert 'title' in story
            assert 'description' in story
            assert 'acceptance_criteria' in story
            assert 'priority' in story
            assert 'effort_estimate' in story

if __name__ == '__main__':
    pytest.main([__file__, '-v'])