"""
Test Solution API endpoint
Tests the JSON API for solution creation with authentication and database persistence
"""

import pytest
import json
from app import app
from models import User, Problem, Solution, StatusEnum, PriorityEnum
from extensions import db
from stateless_auth import create_auth_token


class TestSolutionAPI:
    """Test the Solution API endpoint"""

    def setup_method(self):
        """Set up test data"""
        self.app = app
        self.client = app.test_client()
        
        with app.app_context():
            # Create test user with Manager role
            user = User(
                email='manager@deciframe.com',
                name='Test Manager',
                role='Manager'
            )
            user.set_password('testpassword')
            db.session.add(user)
            
            # Create test problem
            problem = Problem(
                code='P0001',
                title='Test Problem for API',
                description='Test problem description for API testing',
                priority=PriorityEnum.High,
                status=StatusEnum.Open,
                created_by=1
            )
            db.session.add(problem)
            
            db.session.commit()
            
            self.user_id = user.id
            self.problem_id = problem.id

    def test_create_solution_api_success(self):
        """Test successful solution creation via API"""
        with app.app_context():
            # Create auth token
            token = create_auth_token(self.user_id)
            
            # Prepare solution data
            solution_data = {
                'problem_id': self.problem_id,
                'name': 'AI Generated Test Solution',
                'description': 'This is a test solution created via the API endpoint for automated testing purposes.'
            }
            
            # Make POST request to API endpoint
            response = self.client.post(
                '/solutions/api/solutions',
                data=json.dumps(solution_data),
                content_type='application/json',
                cookies={'auth_token': token}
            )
            
            # Assert response status and content
            assert response.status_code == 201
            
            response_data = json.loads(response.data)
            assert response_data['success'] is True
            assert 'id' in response_data
            assert 'message' in response_data
            assert response_data['message'] == 'Solution created successfully'
            
            solution_id = response_data['id']
            
            # Verify solution was created in database
            solution = Solution.query.get(solution_id)
            assert solution is not None
            assert solution.name == 'AI Generated Test Solution'
            assert solution.description == 'This is a test solution created via the API endpoint for automated testing purposes.'
            assert solution.problem_id == self.problem_id
            assert solution.created_by == self.user_id
            assert solution.status == StatusEnum.Open

    def test_create_solution_api_unauthorized(self):
        """Test solution creation fails without authentication"""
        solution_data = {
            'problem_id': self.problem_id,
            'name': 'Unauthorized Solution',
            'description': 'This should fail without auth'
        }
        
        response = self.client.post(
            '/solutions/api/solutions',
            data=json.dumps(solution_data),
            content_type='application/json'
        )
        
        # Should return 401 for unauthenticated request
        assert response.status_code == 401

    def test_create_solution_api_insufficient_permissions(self):
        """Test solution creation fails with insufficient permissions"""
        with app.app_context():
            # Create user with Staff role (insufficient permissions)
            staff_user = User(
                email='staff@deciframe.com',
                name='Test Staff',
                role='Staff'
            )
            staff_user.set_password('testpassword')
            db.session.add(staff_user)
            db.session.commit()
            
            token = create_auth_token(staff_user.id)
            
            solution_data = {
                'problem_id': self.problem_id,
                'name': 'Staff Solution',
                'description': 'This should fail with insufficient permissions'
            }
            
            response = self.client.post(
                '/solutions/api/solutions',
                data=json.dumps(solution_data),
                content_type='application/json',
                cookies={'auth_token': token}
            )
            
            # Should return 403 for insufficient permissions
            assert response.status_code == 403
            
            response_data = json.loads(response.data)
            assert 'error' in response_data
            assert response_data['error'] == 'Insufficient permissions'

    def test_create_solution_api_invalid_data(self):
        """Test solution creation fails with invalid data"""
        with app.app_context():
            token = create_auth_token(self.user_id)
            
            # Missing required fields
            invalid_data = {
                'name': 'Incomplete Solution'
                # Missing problem_id and description
            }
            
            response = self.client.post(
                '/solutions/api/solutions',
                data=json.dumps(invalid_data),
                content_type='application/json',
                cookies={'auth_token': token}
            )
            
            # Should return 500 for invalid data
            assert response.status_code == 500
            
            response_data = json.loads(response.data)
            assert 'error' in response_data

    def test_create_solution_api_nonexistent_problem(self):
        """Test solution creation fails with nonexistent problem"""
        with app.app_context():
            token = create_auth_token(self.user_id)
            
            solution_data = {
                'problem_id': 99999,  # Nonexistent problem ID
                'name': 'Solution for Nonexistent Problem',
                'description': 'This should fail with invalid problem ID'
            }
            
            response = self.client.post(
                '/solutions/api/solutions',
                data=json.dumps(solution_data),
                content_type='application/json',
                cookies={'auth_token': token}
            )
            
            # Should return 500 for foreign key constraint violation
            assert response.status_code == 500
            
            response_data = json.loads(response.data)
            assert 'error' in response_data

    def test_solution_count_increase(self):
        """Test that solution count increases after API creation"""
        with app.app_context():
            # Count solutions before
            initial_count = Solution.query.count()
            
            token = create_auth_token(self.user_id)
            
            solution_data = {
                'problem_id': self.problem_id,
                'name': 'Count Test Solution',
                'description': 'Solution to test count increase'
            }
            
            response = self.client.post(
                '/solutions/api/solutions',
                data=json.dumps(solution_data),
                content_type='application/json',
                cookies={'auth_token': token}
            )
            
            assert response.status_code == 201
            
            # Count solutions after
            final_count = Solution.query.count()
            
            # Verify count increased by exactly 1
            assert final_count == initial_count + 1

    def teardown_method(self):
        """Clean up test data"""
        with app.app_context():
            # Clean up in reverse order of dependencies
            Solution.query.delete()
            Problem.query.delete()
            User.query.delete()
            db.session.commit()


if __name__ == "__main__":
    pytest.main([__file__, '-v'])