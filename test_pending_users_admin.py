#!/usr/bin/env python3
"""
Test script to demonstrate pending users admin interface
"""
import sys
import os
sys.path.append('.')

from app import app, db
from models import User, Department

def test_admin_pending_interface():
    """Test the admin pending users interface"""
    with app.app_context():
        print("=== Pending Users Admin Interface Test ===\n")
        
        # Check pending users
        pending_users = User.query.filter_by(department_status='pending').all()
        print(f"Found {len(pending_users)} pending users:")
        
        for user in pending_users:
            print(f"- {user.name} ({user.email}) - Role: {user.role.value}")
            print(f"  Status: {user.department_status}")
            print(f"  Department: {'None assigned' if not user.dept_id else user.department.name}")
            print()
        
        # Show available departments for assignment
        departments = Department.query.all()
        print(f"\nAvailable departments for assignment ({len(departments)} total):")
        
        for dept in departments[:10]:  # Show first 10
            print(f"- {dept.name} (ID: {dept.id})")
        
        print(f"\n... and {len(departments)-10} more departments")
        
        print("\n=== Admin Interface URLs ===")
        print("Admin Pending Users: /admin/pending-users")
        print("Admin Dashboard: /admin/")
        
        print("\n=== Workflow Test ===")
        if pending_users:
            test_user = pending_users[0]
            print(f"Test assignment for {test_user.name}:")
            print(f"- Current status: {test_user.department_status}")
            print(f"- Has pending department: {test_user.has_pending_department}")
            
            # Test assignment to first department
            if departments:
                test_dept = departments[0]
                print(f"- Would assign to: {test_dept.name}")
                print(f"- Assignment method: user.assign_department({test_dept.id})")

if __name__ == "__main__":
    test_admin_pending_interface()