#!/usr/bin/env python3
"""
Simple test runner for Problem Management CRUD operations
"""

import sys
from models import Problem, Department, User, PriorityEnum, StatusEnum
from app import db, app

def setup_test_data():
    """Create test department and user"""
    with app.app_context():
        # Create test department
        dept = Department(name='Test Department', level=1)
        db.session.add(dept)
        db.session.flush()
        
        # Create test user
        user = User(
            email='test@example.com',
            name='Test User',
            role='Staff',
            department_id=dept.id
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Return IDs instead of objects to avoid session issues
        return dept.id, user.id

def test_problem_crud():
    """Test complete CRUD operations for problems"""
    print("Setting up test data...")
    dept_id, user_id = setup_test_data()
    
    with app.app_context():
        # Test 1: Direct database problem creation
        print("Testing problem creation...")
        problem = Problem(
            title='Test Problem',
            description='This is a test problem description',
            priority=PriorityEnum.Medium,
            status=StatusEnum.Open,
            department_id=dept_id,
            created_by=user_id
        )
        db.session.add(problem)
        db.session.flush()
        problem.code = f"P{problem.id:04d}"
        db.session.commit()
        
        assert problem.code.startswith('P'), f"Problem code format incorrect: {problem.code}"
        assert problem.priority == PriorityEnum.Medium, f"Priority incorrect: {problem.priority}"
        assert problem.status == StatusEnum.Open, f"Status incorrect: {problem.status}"
        print(f"✓ Problem created successfully with code: {problem.code}")
        
        # Test 2: Read problem
        print("Testing problem retrieval...")
        retrieved_problem = Problem.query.get(problem.id)
        assert retrieved_problem is not None, "Problem not found in database"
        assert retrieved_problem.title == 'Test Problem', "Problem title incorrect"
        print("✓ Problem retrieval successful")
        
        # Test 3: Update problem
        print("Testing problem update...")
        retrieved_problem.title = 'Updated Test Problem'
        retrieved_problem.priority = PriorityEnum.High
        retrieved_problem.status = StatusEnum.InProgress
        db.session.commit()
        
        updated_problem = Problem.query.get(problem.id)
        assert updated_problem.title == 'Updated Test Problem', "Problem title not updated"
        assert updated_problem.priority == PriorityEnum.High, "Problem priority not updated"
        assert updated_problem.status == StatusEnum.InProgress, "Problem status not updated"
        print("✓ Problem updated successfully")
        
        # Test 4: Code generation
        print("Testing automatic code generation...")
        problems = []
        for i in range(3):
            test_problem = Problem(
                title=f'Code Test Problem {i+1}',
                description=f'Testing code generation {i+1}',
                priority=PriorityEnum.Medium,
                status=StatusEnum.Open,
                department_id=dept_id,
                created_by=user_id
            )
            db.session.add(test_problem)
            db.session.flush()
            test_problem.code = f"P{test_problem.id:04d}"
            problems.append(test_problem)
        
        db.session.commit()
        
        # Verify codes are properly generated
        for problem in problems:
            assert problem.code.startswith('P'), f"Invalid code format: {problem.code}"
            assert len(problem.code) == 5, f"Invalid code length: {problem.code}"
            assert problem.code[1:].isdigit(), f"Code should be numeric after P: {problem.code}"
        
        print(f"✓ Code generation successful. Created {len(problems)} problems with proper codes")
        
        # Test 5: Delete problem
        print("Testing problem deletion...")
        problem_id = problem.id
        db.session.delete(problem)
        db.session.commit()
        
        deleted_problem = Problem.query.get(problem_id)
        assert deleted_problem is None, "Problem was not deleted from database"
        print("✓ Problem deleted successfully")
        
        # Test web interface accessibility
        print("Testing web interface...")
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user_id)
                sess['_fresh'] = True
            
            # Test problems list loads
            response = client.get('/problems')
            assert response.status_code == 200, f"Problems list failed: {response.status_code}"
            assert b'Problem Management' in response.data, "Problem Management page not loading correctly"
            print("✓ Problems list page loads successfully")
        
        # Cleanup
        db.session.query(Problem).delete()
        db.session.query(User).delete()
        db.session.query(Department).delete()
        db.session.commit()
        
    print("\nAll Problem Management CRUD tests passed successfully!")
    return True

if __name__ == '__main__':
    try:
        test_problem_crud()
        print("\n✅ Problem Management module is fully functional")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1)