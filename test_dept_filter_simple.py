#!/usr/bin/env python3
"""
Simple test script to verify department filtering functionality
"""

from app import app, db
from models import User, Department, Problem
import requests
import time

def test_department_filtering():
    """Test department filtering with actual data"""
    with app.app_context():
        print("=== Department Filtering Test ===")
        
        # Get current user
        user = User.query.filter_by(email='lami.kolade@gmail.com').first()
        if not user:
            print("❌ Test user not found")
            return
            
        print(f"✓ Testing with user: {user.name} ({user.role.value})")
        
        if user.department:
            allowed_depts = user.department.get_descendant_ids(include_self=True)
            dept_names = [d.name for d in Department.query.filter(Department.id.in_(allowed_depts)).all()]
            print(f"✓ User has access to departments: {dept_names}")
        else:
            print("✓ Admin user - access to all departments")
            
        # Test problem filtering
        total_problems = Problem.query.count()
        print(f"✓ Total problems in system: {total_problems}")
        
        if user.department:
            allowed = user.department.get_descendant_ids(include_self=True)
            filtered_problems = Problem.query.filter(Problem.department_id.in_(allowed)).count()
            print(f"✓ Problems accessible to user: {filtered_problems}")
        else:
            # Admin access
            filtered_problems = total_problems
            print(f"✓ Admin sees all problems: {filtered_problems}")
            
        print("=== Test Complete ===")

def test_web_interface():
    """Test the web interface department filtering"""
    print("\n=== Web Interface Test ===")
    
    # Test problems page
    try:
        response = requests.get('http://0.0.0.0:5000/problems/', timeout=10)
        if response.status_code == 200:
            print("✓ Problems page loads successfully")
            if b'All My Departments' in response.content:
                print("✓ Department filter dropdown present")
            else:
                print("❌ Department filter dropdown not found")
        else:
            print(f"❌ Problems page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Web test failed: {e}")

if __name__ == '__main__':
    test_department_filtering()
    test_web_interface()