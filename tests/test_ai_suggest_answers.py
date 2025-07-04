"""
Test suite for AI requirements suggestion endpoint
Verifies OpenAI integration, error handling, and User model compatibility
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app import app, db
from models import User, BusinessCase, Department, RoleEnum, CaseTypeEnum, CaseDepthEnum, PriorityEnum, StatusEnum
from stateless_auth import generate_jwt_token


@pytest.fixture
def client():
    """Create test client with in-memory database"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def test_user(client):
    """Create test user with proper attributes"""
    with app.app_context():
        # Create department
        dept = Department(name='Test Department', level=1)
        db.session.add(dept)
        db.session.flush()
        
        # Create user with correct model fields
        user = User(
            email='test@example.com',
            name='Test User',  # Using 'name' field, not first_name/last_name
            role=RoleEnum.BA,
            department_id=dept.id
        )
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        
        return user


@pytest.fixture
def test_business_case(client, test_user):
    """Create test business case with realistic data"""
    with app.app_context():
        bc = BusinessCase(
            title='Digital Tender Management System',
            description='Comprehensive tender management platform to automate document processing and approval workflows',
            case_type=CaseTypeEnum.Reactive,
            case_depth=CaseDepthEnum.Full,
            priority=PriorityEnum.High,
            status=StatusEnum.Open,
            cost_estimate=125000.00,
            benefit_estimate=450000.00,
            roi=260.0,
            created_by=test_user.id,
            department_id=test_user.department_id
        )
        db.session.add(bc)
        db.session.commit()
        
        return bc


class TestAISuggestAnswers:
    """Test suite for AI requirements suggestion functionality"""
    
    def test_successful_openai_response(self, client, test_user, test_business_case):
        """Test successful OpenAI API response with proper JSON format"""
        
        # Mock OpenAI response
        mock_openai_response = {
            "answers": [
                "Core tender management functionality with document automation and workflow processing",
                "Multi-role access including Procurement Officers, Managers, and Administrators",
                "ERP integration for budget validation and automated data synchronization",
                "Support 200+ concurrent users with sub-2-second response times",
                "Executive dashboards with performance metrics and compliance reporting",
                "Real-time validation with contextual errors and data integrity checks",
                "Mobile-responsive design with WCAG 2.1 AA compliance",
                "Multi-factor authentication with AES-256 encryption and audit logging"
            ]
        }
        
        with patch('ai.routes.openai.OpenAI') as mock_openai_class:
            # Setup mock OpenAI client
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            
            # Mock the chat completion response
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps(mock_openai_response)
            mock_client.chat.completions.create.return_value = mock_response
            
            # Generate JWT token for authentication
            token = generate_jwt_token(test_user.id)
            
            # Make API request
            response = client.post(
                '/api/ai/suggest-requirements-answers',
                json={'case_id': test_business_case.id},
                headers={'Authorization': f'Bearer {token}'},
                content_type='application/json'
            )
            
            # Verify response
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'answers' in data
            assert len(data['answers']) == 8
            assert 'message' in data
            
            # Verify no User model attribute errors in response
            response_text = response.data.decode()
            assert 'first_name' not in response_text
            assert 'username' not in response_text
            assert 'AttributeError' not in response_text
            
            # Verify OpenAI was called with correct parameters
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]['model'] == 'gpt-4o'
            assert call_args[1]['response_format'] == {"type": "json_object"}
    
    def test_openai_api_failure_fallback(self, client, test_user, test_business_case):
        """Test fallback behavior when OpenAI API fails"""
        
        with patch('ai.routes.openai.OpenAI') as mock_openai_class:
            # Setup mock to raise exception
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("API rate limit exceeded")
            
            # Generate JWT token
            token = generate_jwt_token(test_user.id)
            
            # Make API request
            response = client.post(
                '/api/ai/suggest-requirements-answers',
                json={'case_id': test_business_case.id},
                headers={'Authorization': f'Bearer {token}'},
                content_type='application/json'
            )
            
            # Verify error response format
            assert response.status_code == 500
            
            data = json.loads(response.data)
            assert 'error' in data
            assert 'AI service error' in data['error']
            
            # Verify no User model errors
            response_text = response.data.decode()
            assert 'first_name' not in response_text
            assert 'username' not in response_text
    
    def test_missing_openai_key_fallback(self, client, test_user, test_business_case):
        """Test fallback answers when OpenAI API key is not available"""
        
        with patch.dict('os.environ', {}, clear=True):
            # Remove OPENAI_API_KEY from environment
            
            # Generate JWT token
            token = generate_jwt_token(test_user.id)
            
            # Make API request
            response = client.post(
                '/api/ai/suggest-requirements-answers',
                json={'case_id': test_business_case.id},
                headers={'Authorization': f'Bearer {token}'},
                content_type='application/json'
            )
            
            # Verify fallback response
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'answers' in data
            assert len(data['answers']) == 8
            assert 'fallback' in data['message'].lower()
            
            # Verify answers are contextual to business case
            answers_text = ' '.join(data['answers'])
            assert str(test_business_case.cost_estimate) in answers_text.replace(',', '')
    
    def test_invalid_case_id(self, client, test_user):
        """Test error handling for invalid business case ID"""
        
        # Generate JWT token
        token = generate_jwt_token(test_user.id)
        
        # Make API request with non-existent case ID
        response = client.post(
            '/api/ai/suggest-requirements-answers',
            json={'case_id': 99999},
            headers={'Authorization': f'Bearer {token}'},
            content_type='application/json'
        )
        
        # Verify 404 response
        assert response.status_code == 404
    
    def test_missing_case_id(self, client, test_user):
        """Test error handling for missing case_id parameter"""
        
        # Generate JWT token
        token = generate_jwt_token(test_user.id)
        
        # Make API request without case_id
        response = client.post(
            '/api/ai/suggest-requirements-answers',
            json={},
            headers={'Authorization': f'Bearer {token}'},
            content_type='application/json'
        )
        
        # Verify error response
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'case_id is required' in data['error']
    
    def test_authentication_required(self, client, test_business_case):
        """Test that authentication is required for the endpoint"""
        
        # Make API request without authentication
        response = client.post(
            '/api/ai/suggest-requirements-answers',
            json={'case_id': test_business_case.id},
            content_type='application/json'
        )
        
        # Verify authentication error
        assert response.status_code == 401
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Authentication required' in data['error']
    
    def test_malformed_openai_response(self, client, test_user, test_business_case):
        """Test handling of malformed OpenAI JSON response"""
        
        with patch('ai.routes.openai.OpenAI') as mock_openai_class:
            # Setup mock with invalid JSON
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Invalid JSON response"
            mock_client.chat.completions.create.return_value = mock_response
            
            # Generate JWT token
            token = generate_jwt_token(test_user.id)
            
            # Make API request
            response = client.post(
                '/api/ai/suggest-requirements-answers',
                json={'case_id': test_business_case.id},
                headers={'Authorization': f'Bearer {token}'},
                content_type='application/json'
            )
            
            # Verify JSON parsing error response
            assert response.status_code == 500
            
            data = json.loads(response.data)
            assert 'error' in data
            assert 'parsing failed' in data['error']


if __name__ == '__main__':
    pytest.main([__file__])