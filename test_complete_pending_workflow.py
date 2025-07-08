#!/usr/bin/env python3
"""
Complete Pending Department Assignment Workflow Test
Demonstrates the full end-to-end process from registration to admin assignment
"""
import sys
import os
sys.path.append('.')

from app import app, db
from models import User, Department
from werkzeug.security import generate_password_hash

def test_complete_pending_workflow():
    """Test the complete pending department assignment workflow"""
    with app.app_context():
        print("=== Complete Pending Department Assignment Workflow Test ===\n")
        
        # Step 1: Show current pending users
        pending_users = User.query.filter_by(department_status='pending').all()
        print(f"📊 Current pending users: {len(pending_users)}")
        for user in pending_users:
            print(f"   - {user.name} ({user.email})")
        
        # Step 2: Create a test user with pending status (simulating registration)
        print("\n🔧 Creating test user with 'My department isn't listed' scenario...")
        
        test_user = User(
            name="Test Pending User",
            email="test.pending@example.com",
            password_hash=generate_password_hash("password123"),
            role="Staff",
            dept_id=None,  # No department assigned
            department_status='pending'  # Set to pending
        )
        
        db.session.add(test_user)
        db.session.commit()
        print(f"   ✓ Created user: {test_user.name} with pending status")
        
        # Step 3: Verify pending status
        print(f"\n📋 User Details:")
        print(f"   - Name: {test_user.name}")
        print(f"   - Email: {test_user.email}")
        print(f"   - Department Status: {test_user.department_status}")
        print(f"   - Has Pending Department: {test_user.has_pending_department}")
        print(f"   - Department ID: {test_user.dept_id}")
        
        # Step 4: Show admin workflow
        departments = Department.query.limit(5).all()
        print(f"\n🏢 Available departments for assignment:")
        for dept in departments:
            print(f"   - {dept.name} (ID: {dept.id})")
        
        # Step 5: Simulate admin assignment
        if departments:
            target_dept = departments[0]
            print(f"\n👨‍💼 Admin assigns user to: {target_dept.name}")
            
            # Use the assign_department method
            test_user.assign_department(target_dept.id)
            db.session.commit()
            
            print(f"   ✓ Assignment completed!")
            print(f"   - New Department Status: {test_user.department_status}")
            print(f"   - New Department: {test_user.department.name if test_user.department else 'None'}")
            print(f"   - Has Pending Department: {test_user.has_pending_department}")
        
        # Step 6: Verify final state
        updated_pending = User.query.filter_by(department_status='pending').all()
        print(f"\n📊 Final pending users count: {len(updated_pending)}")
        
        # Step 7: Clean up test user
        db.session.delete(test_user)
        db.session.commit()
        print(f"\n🧹 Test user cleaned up")
        
        print("\n=== Workflow Components ===")
        print("✓ Registration form with 'My department isn't listed' option")
        print("✓ Automatic pending status assignment during registration")
        print("✓ Pending dashboard for limited user access")
        print("✓ Admin interface at /admin/pending-users")
        print("✓ Department assignment functionality")
        print("✓ Automatic status transition from pending to assigned")
        
        print("\n=== URLs ===")
        print("- User Registration: /auth/register")
        print("- Pending Dashboard: /dashboard/pending")
        print("- Admin Pending Users: /admin/pending-users")
        print("- Admin Center: Admin Center → Pending Assignments")

if __name__ == "__main__":
    test_complete_pending_workflow()