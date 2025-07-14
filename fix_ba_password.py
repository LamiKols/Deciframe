#!/usr/bin/env python3
"""
Fix BA User Password
Sets a proper password hash for Sarah Martinez (BA user)
"""

from werkzeug.security import generate_password_hash
from app import create_app, db
from models import User

def fix_ba_password():
    """Set password hash for BA user"""
    app = create_app()
    
    with app.app_context():
        # Find the BA user
        ba_user = User.query.filter_by(email='sarah.martinez@deciframe.com').first()
        
        if ba_user:
            # Set password hash for 'password123'
            ba_user.password_hash = generate_password_hash('password123')
            db.session.commit()
            print(f"✅ Password hash set for BA user: {ba_user.email}")
            print(f"   Password: password123")
            print(f"   Role: {ba_user.role}")
        else:
            print("❌ BA user not found")

if __name__ == "__main__":
    fix_ba_password()