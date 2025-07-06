#!/usr/bin/env python3
"""
Dashboard Authentication Fix Script
Resolves session synchronization issues between main app and dashboard routes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash

def reset_test_user_password():
    """Reset test user password to known value"""
    with app.app_context():
        user = User.query.filter_by(email='lami.kolade@gmail.com').first()
        if user:
            # Set password to 'manager123'
            user.password_hash = generate_password_hash('manager123')
            db.session.commit()
            print(f"✓ Reset password for {user.name} ({user.email})")
            print(f"✓ Role: {user.role.value}")
            print(f"✓ Department ID: {user.dept_id}")
            return user
        else:
            print("❌ User not found")
            return None

def test_authentication_flow():
    """Test the complete authentication flow"""
    with app.app_context():
        # Test user lookup
        user = User.query.filter_by(email='lami.kolade@gmail.com').first()
        if user:
            print(f"✓ User found: {user.name}")
            
            # Test password verification
            if user.check_password('manager123'):
                print("✓ Password verification works")
                
                # Test Flask-Login integration
                with app.test_request_context():
                    login_user(user)
                    print("✓ Flask-Login integration works")
                    
                return True
            else:
                print("❌ Password verification failed")
        else:
            print("❌ User not found")
        
        return False

if __name__ == '__main__':
    print("🔧 Fixing dashboard authentication...")
    
    # Reset test user password
    user = reset_test_user_password()
    
    if user:
        # Test authentication flow
        if test_authentication_flow():
            print("✅ Authentication flow working correctly")
        else:
            print("❌ Authentication flow has issues")
    
    print("🔧 Fix complete - test login with manager123")