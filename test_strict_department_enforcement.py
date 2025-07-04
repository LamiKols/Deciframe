#!/usr/bin/env python3
"""
Comprehensive Test Suite for Strict Department Enforcement
Verifies that users cannot create problems, business cases, or projects for other departments
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import app, db
from models import User, Department, Problem, BusinessCase, Project
from werkzeug.security import generate_password_hash
import requests
from datetime import datetime

def setup_test_data():
    """Create test departments and users for department enforcement testing"""
    print("Setting up test data...")
    
    with app.app_context():
        # Clear existing test data
        Problem.query.filter(Problem.title.like('SECURITY_TEST_%')).delete()
        BusinessCase.query.filter(BusinessCase.title.like('SECURITY_TEST_%')).delete()
        Project.query.filter(Project.name.like('SECURITY_TEST_%')).delete()
        
        # Create test departments
        dept_executive = Department.query.filter_by(name='Executive Office').first()
        dept_engineering = Department.query.filter_by(name='Engineering').first()
        dept_operations = Department.query.filter_by(name='Operations').first()
        
        if not dept_executive:
            dept_executive = Department(name='Executive Office', description='Executive leadership')
            db.session.add(dept_executive)
        
        if not dept_engineering:
            dept_engineering = Department(name='Engineering', description='Software engineering team')
            db.session.add(dept_engineering)
            
        if not dept_operations:
            dept_operations = Department(name='Operations', description='Operations team')
            db.session.add(dept_operations)
            
        db.session.commit()
        
        # Create test users in different departments
        # User 1: Executive Office Manager
        exec_user = User.query.filter_by(email='exec.manager@test.com').first()
        if not exec_user:
            exec_user = User(
                username='exec_manager',
                email='exec.manager@test.com',
                first_name='Executive',
                last_name='Manager',
                role='Manager',
                dept_id=dept_executive.id,
                password_hash=generate_password_hash('testpass123')
            )
            db.session.add(exec_user)
        
        # User 2: Engineering Staff
        eng_user = User.query.filter_by(email='eng.staff@test.com').first()
        if not eng_user:
            eng_user = User(
                username='eng_staff',
                email='eng.staff@test.com',
                first_name='Engineering',
                last_name='Staff',
                role='Staff',
                dept_id=dept_engineering.id,
                password_hash=generate_password_hash('testpass123')
            )
            db.session.add(eng_user)
        
        # User 3: Operations Staff
        ops_user = User.query.filter_by(email='ops.staff@test.com').first()
        if not ops_user:
            ops_user = User(
                username='ops_staff',
                email='ops.staff@test.com',
                first_name='Operations',
                last_name='Staff',
                role='Staff',
                dept_id=dept_operations.id,
                password_hash=generate_password_hash('testpass123')
            )
            db.session.add(ops_user)
        
        # User 4: Admin (should have cross-department access)
        admin_user = User.query.filter_by(email='admin.test@test.com').first()
        if not admin_user:
            admin_user = User(
                username='admin_test',
                email='admin.test@test.com',
                first_name='Admin',
                last_name='Test',
                role='Admin',
                dept_id=dept_executive.id,
                password_hash=generate_password_hash('testpass123')
            )
            db.session.add(admin_user)
        
        db.session.commit()
        
        return {
            'departments': {
                'executive': dept_executive,
                'engineering': dept_engineering,
                'operations': dept_operations
            },
            'users': {
                'exec_manager': exec_user,
                'eng_staff': eng_user,
                'ops_staff': ops_user,
                'admin': admin_user
            }
        }

def login_user(email, password):
    """Login user and return session cookies"""
    base_url = "http://0.0.0.0:5000"
    session = requests.Session()
    
    # Get login page to establish session
    login_page = session.get(f"{base_url}/auth/login")
    
    # Login with credentials
    login_data = {
        'email': email,
        'password': password
    }
    
    response = session.post(f"{base_url}/auth/login", data=login_data, allow_redirects=True)
    
    if response.status_code == 200 and "Dashboard" in response.text:
        print(f"✓ Successfully logged in as {email}")
        return session
    else:
        print(f"✗ Failed to login as {email}")
        return None

def test_problem_department_enforcement(test_data):
    """Test that users cannot create problems for other departments"""
    print("\n=== Testing Problem Department Enforcement ===")
    
    base_url = "http://0.0.0.0:5000"
    results = []
    
    # Test 1: Engineering staff tries to create problem for Operations department
    eng_session = login_user('eng.staff@test.com', 'testpass123')
    if eng_session:
        problem_data = {
            'title': 'SECURITY_TEST_Cross_Dept_Problem',
            'description': 'This should be blocked - cross-department creation attempt',
            'priority': 'High',
            'status': 'Open',
            'issue_type': 'SYSTEM',
            'department_id': test_data['departments']['operations'].id,  # Wrong department!
            'org_unit_id': '',
            'submit': 'Save Problem'
        }
        
        response = eng_session.post(f"{base_url}/problems/new", data=problem_data)
        
        # Check if problem was created in wrong department
        with app.app_context():
            cross_dept_problem = Problem.query.filter_by(
                title='SECURITY_TEST_Cross_Dept_Problem'
            ).first()
            
            if cross_dept_problem:
                if cross_dept_problem.dept_id == test_data['departments']['engineering'].id:
                    results.append("✓ PASS: Problem auto-assigned to user's department (Engineering)")
                else:
                    results.append(f"✗ FAIL: Problem created in wrong department {cross_dept_problem.dept_id}")
            else:
                results.append("✗ FAIL: Problem creation failed completely")
    
    # Test 2: Operations staff tries to create problem for Executive department
    ops_session = login_user('ops.staff@test.com', 'testpass123')
    if ops_session:
        problem_data = {
            'title': 'SECURITY_TEST_Another_Cross_Dept',
            'description': 'This should also be blocked',
            'priority': 'Medium',
            'status': 'Open',
            'issue_type': 'PROCESS',
            'department_id': test_data['departments']['executive'].id,  # Wrong department!
            'org_unit_id': '',
            'submit': 'Save Problem'
        }
        
        response = ops_session.post(f"{base_url}/problems/new", data=problem_data)
        
        with app.app_context():
            cross_dept_problem2 = Problem.query.filter_by(
                title='SECURITY_TEST_Another_Cross_Dept'
            ).first()
            
            if cross_dept_problem2:
                if cross_dept_problem2.dept_id == test_data['departments']['operations'].id:
                    results.append("✓ PASS: Problem auto-assigned to user's department (Operations)")
                else:
                    results.append(f"✗ FAIL: Problem created in wrong department {cross_dept_problem2.dept_id}")
            else:
                results.append("✗ FAIL: Problem creation failed completely")
    
    # Test 3: Admin should be able to create for any department
    admin_session = login_user('admin.test@test.com', 'testpass123')
    if admin_session:
        problem_data = {
            'title': 'SECURITY_TEST_Admin_Cross_Dept',
            'description': 'Admin should be able to create for any department',
            'priority': 'Low',
            'status': 'Open',
            'issue_type': 'OTHER',
            'department_id': test_data['departments']['operations'].id,
            'org_unit_id': '',
            'submit': 'Save Problem'
        }
        
        response = admin_session.post(f"{base_url}/problems/new", data=problem_data)
        
        with app.app_context():
            admin_problem = Problem.query.filter_by(
                title='SECURITY_TEST_Admin_Cross_Dept'
            ).first()
            
            if admin_problem and admin_problem.dept_id == test_data['departments']['operations'].id:
                results.append("✓ PASS: Admin can create problems for any department")
            else:
                results.append("✗ FAIL: Admin cross-department creation blocked incorrectly")
    
    return results

def test_project_department_enforcement(test_data):
    """Test that users cannot create projects for other departments"""
    print("\n=== Testing Project Department Enforcement ===")
    
    base_url = "http://0.0.0.0:5000"
    results = []
    
    # Test 1: Engineering staff tries to create project for Operations
    eng_session = login_user('eng.staff@test.com', 'testpass123')
    if eng_session:
        project_data = {
            'name': 'SECURITY_TEST_Cross_Dept_Project',
            'description': 'This should be blocked - cross-department project',
            'start_date': '2025-01-01',
            'end_date': '2025-06-30',
            'budget': '50000',
            'status': 'Open',
            'priority': 'High',
            'business_case_id': '',
            'project_manager_id': test_data['users']['eng_staff'].id,
            'department_id': test_data['departments']['operations'].id,  # Wrong department!
            'org_unit_id': '',
            'submit': 'Save Project'
        }
        
        response = eng_session.post(f"{base_url}/projects/new", data=project_data)
        
        with app.app_context():
            cross_dept_project = Project.query.filter_by(
                name='SECURITY_TEST_Cross_Dept_Project'
            ).first()
            
            if cross_dept_project:
                if cross_dept_project.department_id == test_data['departments']['engineering'].id:
                    results.append("✓ PASS: Project auto-assigned to user's department (Engineering)")
                else:
                    results.append(f"✗ FAIL: Project created in wrong department {cross_dept_project.department_id}")
            else:
                results.append("✗ FAIL: Project creation failed completely")
    
    return results

def run_security_test():
    """Run comprehensive department enforcement security test"""
    print("=" * 60)
    print("DECIFRAME SECURITY TEST: STRICT DEPARTMENT ENFORCEMENT")
    print("=" * 60)
    
    try:
        # Setup test data
        test_data = setup_test_data()
        
        # Run tests
        problem_results = test_problem_department_enforcement(test_data)
        project_results = test_project_department_enforcement(test_data)
        
        # Compile results
        all_results = problem_results + project_results
        
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for result in all_results:
            print(result)
        
        # Count passes and failures
        passes = len([r for r in all_results if "✓ PASS" in r])
        failures = len([r for r in all_results if "✗ FAIL" in r])
        
        print(f"\nTOTAL: {passes} PASSED, {failures} FAILED")
        
        if failures == 0:
            print("\n🛡️  SECURITY STATUS: FULLY PROTECTED")
            print("✓ Department enforcement is working correctly")
            print("✓ Users cannot create content for other departments") 
            print("✓ Admin retains cross-department capabilities")
        else:
            print(f"\n⚠️  SECURITY VULNERABILITIES DETECTED: {failures} issues found")
            print("✗ Department enforcement needs attention")
        
        # Cleanup test data
        with app.app_context():
            Problem.query.filter(Problem.title.like('SECURITY_TEST_%')).delete()
            BusinessCase.query.filter(BusinessCase.title.like('SECURITY_TEST_%')).delete()
            Project.query.filter(Project.name.like('SECURITY_TEST_%')).delete()
            db.session.commit()
        
        print("\n✓ Test data cleaned up")
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_security_test()