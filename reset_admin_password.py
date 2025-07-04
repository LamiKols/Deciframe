#!/usr/bin/env python3
"""
Reset admin password script
"""
import os
import sys
from werkzeug.security import generate_password_hash
from app import app, db
from models import User

def reset_admin_password():
    """Reset admin password to known value"""
    with app.app_context():
        # Find admin user
        admin_user = User.query.filter_by(email='admin@deciframe.com').first()
        
        if not admin_user:
            print("❌ Admin user not found!")
            return False
            
        # Generate new password hash
        new_password = 'admin123'
        password_hash = generate_password_hash(new_password)
        
        print(f"🔧 Updating password for: {admin_user.email}")
        print(f"🔧 New password hash: {password_hash}")
        
        # Update password
        admin_user.password_hash = password_hash
        db.session.commit()
        
        print("✅ Admin password reset successfully!")
        print(f"📧 Email: {admin_user.email}")
        print(f"🔑 Password: {new_password}")
        
        return True

if __name__ == '__main__':
    reset_admin_password()