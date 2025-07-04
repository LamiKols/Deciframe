"""
Comprehensive Department Scoping Tests
Tests multi-level department hierarchy and access control across Problems, Business Cases, and Projects
"""

import pytest
from flask import url_for
from app import app, db
from models import User, Department, Problem, BusinessCase, Project, RoleEnum, StatusEnum, PriorityEnum, ImpactEnum, UrgencyEnum
from werkzeug.security import generate_password_hash
from flask_login import login_user


class TestDepartmentScoping:
    """Test suite for department-based access control and filtering"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test data with multi-level department hierarchy"""
        with app.app_context():
            # Clear existing data
            db.session.query(Problem).delete()
            db.session.query(BusinessCase).delete()
            db.session.query(Project).delete()
            db.session.query(User).delete()
            db.session.query(Department).delete()
            
            # Create multi-level department hierarchy
            # Level 1: Executive Office (Top Level)
            self.executive_dept = Department(name="Executive Office", description="Top level department")
            db.session.add(self.executive_dept)
            db.session.flush()
            
            # Level 2: Engineering and Operations under Executive
            self.engineering_dept = Department(
                name="Engineering",
                description="Engineering division",
                parent_id=self.executive_dept.id
            )
            self.operations_dept = Department(
                name="Operations",
                description="Operations division",
                parent_id=self.executive_dept.id
            )
            db.session.add_all([self.engineering_dept, self.operations_dept])
            db.session.flush()
            
            # Level 3: Frontend and Backend under Engineering
            self.frontend_dept = Department(
                name="Frontend Development",
                description="Frontend engineering team",
                parent_id=self.engineering_dept.id
            )
            self.backend_dept = Department(
                name="Backend Development", 
                description="Backend engineering team",
                parent_id=self.engineering_dept.id
            )
            
            # Level 3: QA and DevOps under Operations
            self.qa_dept = Department(
                name="Quality Assurance",
                description="QA team",
                parent_id=self.operations_dept.id
            )
            self.devops_dept = Department(
                name="DevOps",
                description="DevOps team",
                parent_id=self.operations_dept.id
            )
            
            db.session.add_all([self.frontend_dept, self.backend_dept, self.qa_dept, self.devops_dept])
            db.session.flush()
            
            # Create users with different department assignments
            self.executive_manager = User(
                name="Executive Manager",
                email="exec@company.com",
                password_hash=generate_password_hash("password"),
                role=RoleEnum.Manager,
                dept_id=self.executive_dept.id
            )
            
            self.engineering_manager = User(
                name="Engineering Manager",
                email="eng@company.com",
                password_hash=generate_password_hash("password"),
                role=RoleEnum.Manager,
                dept_id=self.engineering_dept.id
            )
            
            self.frontend_dev = User(
                name="Frontend Developer",
                email="frontend@company.com",
                password_hash=generate_password_hash("password"),
                role=RoleEnum.Staff,
                dept_id=self.frontend_dept.id
            )
            
            self.backend_dev = User(
                name="Backend Developer",
                email="backend@company.com", 
                password_hash=generate_password_hash("password"),
                role=RoleEnum.Staff,
                dept_id=self.backend_dept.id
            )
            
            self.qa_lead = User(
                name="QA Lead",
                email="qa@company.com",
                password_hash=generate_password_hash("password"),
                role=RoleEnum.Staff,
                dept_id=self.qa_dept.id
            )
            
            self.admin_user = User(
                name="Admin User",
                email="admin@company.com",
                password_hash=generate_password_hash("password"),
                role=RoleEnum.Admin,
                dept_id=None  # Admin without department assignment
            )
            
            db.session.add_all([
                self.executive_manager, self.engineering_manager, 
                self.frontend_dev, self.backend_dev, self.qa_lead, self.admin_user
            ])
            db.session.flush()
            
            # Create problems across different departments
            self.exec_problem = Problem(
                title="Executive Strategic Issue",
                description="High-level strategic problem",
                department_id=self.executive_dept.id,
                reported_by=self.executive_manager.id,
                created_by=self.executive_manager.id,
                priority=PriorityEnum.High,
                impact=ImpactEnum.High,
                urgency=UrgencyEnum.High,
                status=StatusEnum.Open
            )
            
            self.eng_problem = Problem(
                title="Engineering Architecture Issue",
                description="Engineering-specific problem",
                department_id=self.engineering_dept.id,
                reported_by=self.engineering_manager.id,
                created_by=self.engineering_manager.id,
                priority=PriorityEnum.Medium,
                impact=ImpactEnum.Medium,
                urgency=UrgencyEnum.Medium,
                status=StatusEnum.Open
            )
            
            self.frontend_problem = Problem(
                title="Frontend UI Bug",
                description="Frontend-specific issue",
                department_id=self.frontend_dept.id,
                reported_by=self.frontend_dev.id,
                created_by=self.frontend_dev.id,
                priority=PriorityEnum.Low,
                impact=ImpactEnum.Low,
                urgency=UrgencyEnum.Low,
                status=StatusEnum.Open
            )
            
            self.qa_problem = Problem(
                title="Testing Framework Issue",
                description="QA-specific problem",
                department_id=self.qa_dept.id,
                reported_by=self.qa_lead.id,
                created_by=self.qa_lead.id,
                priority=PriorityEnum.Medium,
                impact=ImpactEnum.Medium,
                urgency=UrgencyEnum.Medium,
                status=StatusEnum.Open
            )
            
            db.session.add_all([self.exec_problem, self.eng_problem, self.frontend_problem, self.qa_problem])
            db.session.flush()
            
            # Create business cases across departments
            self.exec_case = BusinessCase(
                title="Strategic Initiative",
                description="Executive business case",
                dept_id=self.executive_dept.id,
                created_by=self.executive_manager.id,
                status=StatusEnum.Open,
                case_type="Proactive"
            )
            
            self.eng_case = BusinessCase(
                title="Engineering Process Improvement",
                description="Engineering business case",
                dept_id=self.engineering_dept.id,
                created_by=self.engineering_manager.id,
                status=StatusEnum.Open,
                case_type="Reactive",
                problem_id=self.eng_problem.id
            )
            
            self.frontend_case = BusinessCase(
                title="Frontend Modernization",
                description="Frontend business case",
                dept_id=self.frontend_dept.id,
                created_by=self.frontend_dev.id,
                status=StatusEnum.Open,
                case_type="Reactive",
                problem_id=self.frontend_problem.id
            )
            
            db.session.add_all([self.exec_case, self.eng_case, self.frontend_case])
            db.session.flush()
            
            # Create projects across departments
            self.exec_project = Project(
                name="Executive Strategic Project",
                description="Executive project",
                department_id=self.executive_dept.id,
                project_manager_id=self.executive_manager.id,
                status=StatusEnum.Open,
                priority=PriorityEnum.High,
                case_id=self.exec_case.id
            )
            
            self.eng_project = Project(
                name="Engineering Infrastructure Project",
                description="Engineering project", 
                department_id=self.engineering_dept.id,
                project_manager_id=self.engineering_manager.id,
                status=StatusEnum.InProgress,
                priority=PriorityEnum.Medium,
                case_id=self.eng_case.id
            )
            
            self.frontend_project = Project(
                name="Frontend Redesign Project",
                description="Frontend project",
                department_id=self.frontend_dept.id,
                project_manager_id=self.frontend_dev.id,
                status=StatusEnum.Open,
                priority=PriorityEnum.Low,
                case_id=self.frontend_case.id
            )
            
            db.session.add_all([self.exec_project, self.eng_project, self.frontend_project])
            db.session.commit()

    def test_executive_manager_sees_all_descendant_problems(self):
        """Executive manager should see problems from all child departments"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = str(self.executive_manager.id)
            
            with app.test_request_context():
                login_user(self.executive_manager)
                response = client.get('/problems/')
                
                assert response.status_code == 200
                # Executive manager should see all 4 problems (exec, eng, frontend, qa)
                assert b"Executive Strategic Issue" in response.data
                assert b"Engineering Architecture Issue" in response.data
                assert b"Frontend UI Bug" in response.data
                assert b"Testing Framework Issue" in response.data

    def test_engineering_manager_sees_engineering_tree_problems(self):
        """Engineering manager should see problems from engineering and child departments only"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = str(self.engineering_manager.id)
            
            with app.test_request_context():
                login_user(self.engineering_manager)
                response = client.get('/problems/')
                
                assert response.status_code == 200
                # Engineering manager should see engineering and frontend problems
                assert b"Engineering Architecture Issue" in response.data
                assert b"Frontend UI Bug" in response.data
                # Should NOT see executive or QA problems
                assert b"Executive Strategic Issue" not in response.data
                assert b"Testing Framework Issue" not in response.data

    def test_frontend_dev_sees_only_frontend_problems(self):
        """Frontend developer should only see problems from their department"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = str(self.frontend_dev.id)
            
            with app.test_request_context():
                login_user(self.frontend_dev)
                response = client.get('/problems/')
                
                assert response.status_code == 200
                # Frontend dev should only see frontend problems
                assert b"Frontend UI Bug" in response.data
                # Should NOT see other department problems
                assert b"Executive Strategic Issue" not in response.data
                assert b"Engineering Architecture Issue" not in response.data
                assert b"Testing Framework Issue" not in response.data

    def test_admin_sees_all_problems(self):
        """Admin without department assignment should see all problems"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = str(self.admin_user.id)
            
            with app.test_request_context():
                login_user(self.admin_user)
                response = client.get('/problems/')
                
                assert response.status_code == 200
                # Admin should see all problems
                assert b"Executive Strategic Issue" in response.data
                assert b"Engineering Architecture Issue" in response.data
                assert b"Frontend UI Bug" in response.data
                assert b"Testing Framework Issue" in response.data

    def test_dept_parameter_override_problems(self):
        """Test ?dept= parameter narrows results to single department"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = str(self.executive_manager.id)
            
            with app.test_request_context():
                login_user(self.executive_manager)
                # Test filtering to specific frontend department
                response = client.get(f'/problems/?dept={self.frontend_dept.id}')
                
                assert response.status_code == 200
                # Should only see frontend problems when filtered
                assert b"Frontend UI Bug" in response.data
                # Should NOT see other departments even though user has access
                assert b"Executive Strategic Issue" not in response.data
                assert b"Engineering Architecture Issue" not in response.data
                assert b"Testing Framework Issue" not in response.data

    def test_engineering_manager_business_cases_scope(self):
        """Engineering manager should see business cases from engineering hierarchy"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = str(self.engineering_manager.id)
            
            with app.test_request_context():
                login_user(self.engineering_manager)
                response = client.get('/business/')
                
                assert response.status_code == 200
                # Should see engineering and frontend cases
                assert b"Engineering Process Improvement" in response.data
                assert b"Frontend Modernization" in response.data
                # Should NOT see executive cases
                assert b"Strategic Initiative" not in response.data

    def test_dept_parameter_override_business_cases(self):
        """Test ?dept= parameter filtering for business cases"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = str(self.executive_manager.id)
            
            with app.test_request_context():
                login_user(self.executive_manager)
                # Filter to specific engineering department
                response = client.get(f'/business/?dept={self.engineering_dept.id}')
                
                assert response.status_code == 200
                # Should only see engineering cases when filtered
                assert b"Engineering Process Improvement" in response.data
                # Should NOT see other departments
                assert b"Strategic Initiative" not in response.data
                assert b"Frontend Modernization" not in response.data

    def test_engineering_manager_projects_scope(self):
        """Engineering manager should see projects from engineering hierarchy"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = str(self.engineering_manager.id)
            
            with app.test_request_context():
                login_user(self.engineering_manager)
                response = client.get('/projects/')
                
                assert response.status_code == 200
                # Should see engineering and frontend projects
                assert b"Engineering Infrastructure Project" in response.data
                assert b"Frontend Redesign Project" in response.data
                # Should NOT see executive projects
                assert b"Executive Strategic Project" not in response.data

    def test_dept_parameter_override_projects(self):
        """Test ?dept= parameter filtering for projects"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = str(self.executive_manager.id)
            
            with app.test_request_context():
                login_user(self.executive_manager)
                # Filter to specific frontend department
                response = client.get(f'/projects/?dept={self.frontend_dept.id}')
                
                assert response.status_code == 200
                # Should only see frontend projects when filtered
                assert b"Frontend Redesign Project" in response.data
                # Should NOT see other departments
                assert b"Executive Strategic Project" not in response.data
                assert b"Engineering Infrastructure Project" not in response.data

    def test_unauthorized_dept_parameter_ignored(self):
        """Test that unauthorized dept parameter values are ignored"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = str(self.frontend_dev.id)
            
            with app.test_request_context():
                login_user(self.frontend_dev)
                # Try to access executive department (unauthorized)
                response = client.get(f'/problems/?dept={self.executive_dept.id}')
                
                assert response.status_code == 200
                # Should fall back to user's normal scope (frontend only)
                assert b"Frontend UI Bug" in response.data
                # Should NOT see executive problems even with dept parameter
                assert b"Executive Strategic Issue" not in response.data

    def test_department_dropdown_shows_authorized_departments(self):
        """Test that department dropdown only shows authorized departments"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = str(self.engineering_manager.id)
            
            with app.test_request_context():
                login_user(self.engineering_manager)
                response = client.get('/problems/')
                
                assert response.status_code == 200
                # Should see engineering department options
                assert b"Engineering" in response.data
                assert b"Frontend Development" in response.data
                assert b"Backend Development" in response.data
                # Should NOT see unauthorized departments
                assert b"Executive Office" not in response.data
                assert b"Quality Assurance" not in response.data

    def test_parameter_preservation_with_dept_filter(self):
        """Test that existing parameters are preserved when dept filter is applied"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = str(self.executive_manager.id)
            
            with app.test_request_context():
                login_user(self.executive_manager)
                # Test with search and status parameters plus dept filter
                response = client.get(f'/problems/?q=Strategic&status=Open&dept={self.executive_dept.id}')
                
                assert response.status_code == 200
                # Should maintain search and status filters with dept filter
                assert b"Executive Strategic Issue" in response.data
                # Should not show non-matching items
                assert b"Engineering Architecture Issue" not in response.data

    def test_get_descendant_ids_method(self):
        """Test the get_descendant_ids method works correctly"""
        with app.app_context():
            # Test executive department gets all descendants
            exec_descendants = self.executive_dept.get_descendant_ids(include_self=True)
            expected_ids = {
                self.executive_dept.id,
                self.engineering_dept.id,
                self.operations_dept.id, 
                self.frontend_dept.id,
                self.backend_dept.id,
                self.qa_dept.id,
                self.devops_dept.id
            }
            assert set(exec_descendants) == expected_ids
            
            # Test engineering department gets engineering descendants only
            eng_descendants = self.engineering_dept.get_descendant_ids(include_self=True)
            expected_eng_ids = {
                self.engineering_dept.id,
                self.frontend_dept.id,
                self.backend_dept.id
            }
            assert set(eng_descendants) == expected_eng_ids
            
            # Test leaf department only gets itself
            frontend_descendants = self.frontend_dept.get_descendant_ids(include_self=True)
            assert set(frontend_descendants) == {self.frontend_dept.id}


if __name__ == '__main__':
    pytest.main([__file__])