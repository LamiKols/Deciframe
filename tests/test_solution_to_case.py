"""
Test Solution to Business Case workflow
Tests the end-to-end flow from AI solution generation to business case creation
"""

import pytest
from app import app
from models import User, Problem, Solution, BusinessCase, StatusEnum, PriorityEnum, CaseTypeEnum, CaseDepthEnum
from extensions import db


class TestSolutionToBusinessCase:
    """Test the complete Solution → Business Case workflow"""

    def setup_method(self):
        """Set up test data"""
        self.app = app
        self.client = app.test_client()
        
        with app.app_context():
            # Create test user
            user = User(
                email='test@deciframe.com',
                name='Test User',
                role='Manager'
            )
            user.set_password('testpassword')
            db.session.add(user)
            
            # Create test problem
            problem = Problem(
                code='P0001',
                title='Test Problem',
                description='Test problem description',
                priority=PriorityEnum.High,
                status=StatusEnum.Open,
                created_by=1
            )
            db.session.add(problem)
            
            # Create test solution
            solution = Solution(
                problem_id=1,
                name='AI Generated Solution',
                description='Implement automated workflow tools to streamline manual processes',
                status=StatusEnum.Open,
                priority=PriorityEnum.Medium,
                created_by=1
            )
            db.session.add(solution)
            
            db.session.commit()
            
            self.user_id = user.id
            self.problem_id = problem.id
            self.solution_id = solution.id

    def test_business_case_form_prepopulation(self):
        """Test that business case form is pre-populated from solution"""
        with app.app_context():
            # Simulate authenticated request
            from stateless_auth import create_auth_token
            token = create_auth_token(self.user_id)
            
            # GET request with solution_id parameter
            response = self.client.get(
                f'/business/cases/new?problem_id={self.problem_id}&solution_id={self.solution_id}',
                cookies={'auth_token': token}
            )
            
            assert response.status_code == 200
            # Check that solution description is in the form
            assert b'AI Generated Solution' in response.data
            assert b'automated workflow tools' in response.data
            assert b'Creating Business Case from AI Solution' in response.data

    def test_solution_to_business_case_creation(self):
        """Test creating business case from solution"""
        with app.app_context():
            from stateless_auth import create_auth_token
            token = create_auth_token(self.user_id)
            
            # POST data for business case creation
            form_data = {
                'csrf_token': 'test_token',  # Would need proper CSRF token in real test
                'solution_id': str(self.solution_id),
                'case_type': 'Reactive',
                'case_depth': 'Light',
                'problem': str(self.problem_id),
                'title': 'Business Case for: AI Generated Solution',
                'description': 'Business case from AI solution',
                'cost_estimate': '50000',
                'benefit_estimate': '100000',
                'summary': 'Test summary',
                'submit': 'Create Business Case'
            }
            
            # Mock CSRF validation for testing
            with app.test_request_context():
                app.config['WTF_CSRF_ENABLED'] = False
                
                response = self.client.post(
                    '/business/cases/new',
                    data=form_data,
                    cookies={'auth_token': token},
                    follow_redirects=True
                )
                
                # Verify business case was created
                business_case = BusinessCase.query.filter_by(solution_id=self.solution_id).first()
                assert business_case is not None
                assert business_case.solution_id == self.solution_id
                assert business_case.problem_id == self.problem_id
                assert business_case.cost_estimate == 50000
                assert business_case.benefit_estimate == 100000
                assert business_case.case_type == CaseTypeEnum.Reactive

    def test_solution_business_case_traceability(self):
        """Test that solution-business case relationship is maintained"""
        with app.app_context():
            # Create business case linked to solution
            business_case = BusinessCase(
                problem_id=self.problem_id,
                solution_id=self.solution_id,
                title='Test Business Case',
                description='Test description',
                cost_estimate=75000,
                benefit_estimate=150000,
                case_type=CaseTypeEnum.Reactive,
                case_depth=CaseDepthEnum.Light,
                created_by=self.user_id
            )
            db.session.add(business_case)
            db.session.commit()
            
            # Verify relationships work
            solution = Solution.query.get(self.solution_id)
            business_case = BusinessCase.query.filter_by(solution_id=self.solution_id).first()
            
            assert business_case.solution == solution
            assert business_case.solution.name == 'AI Generated Solution'
            assert business_case.problem_id == solution.problem_id

    def teardown_method(self):
        """Clean up test data"""
        with app.app_context():
            # Clean up in reverse order of dependencies
            BusinessCase.query.delete()
            Solution.query.delete()
            Problem.query.delete()
            User.query.delete()
            db.session.commit()


if __name__ == "__main__":
    pytest.main([__file__])