#!/usr/bin/env python3
"""
User Password Reset Utility
Simple script to reset user passwords for admin purposes
"""

import os
import sys
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///deciframe.db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def reset_password(email, new_password):
    """Reset password for a user by email"""
    session = Session()
    try:
        # Hash the new password
        password_hash = generate_password_hash(new_password)
        
        # Update the user's password
        result = session.execute(
            text("UPDATE users SET password_hash = :password_hash WHERE email = :email"),
            {"password_hash": password_hash, "email": email}
        )
        
        if result.rowcount > 0:
            session.commit()
            print(f"✅ Password reset successful for {email}")
            print(f"New password: {new_password}")
            return True
        else:
            print(f"❌ User not found: {email}")
            return False
            
    except Exception as e:
        session.rollback()
        print(f"❌ Error resetting password: {e}")
        return False
    finally:
        session.close()

def list_users():
    """List all users in the system"""
    session = Session()
    try:
        result = session.execute(
            text("SELECT email, name, role FROM users ORDER BY email")
        )
        users = result.fetchall()
        
        if users:
            print("\n📋 Users in the system:")
            print("-" * 50)
            for user in users:
                print(f"Email: {user[0]}")
                print(f"Name: {user[1]}")
                print(f"Role: {user[2]}")
                print("-" * 50)
        else:
            print("No users found in the system")
            
    except Exception as e:
        print(f"❌ Error listing users: {e}")
    finally:
        session.close()

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  List users: python reset_user_password.py list")
        print("  Reset password: python reset_user_password.py <email> [password]")
        print("  Example: python reset_user_password.py lami.kolade@gmail.com password123")
        return
    
    if sys.argv[1] == "list":
        list_users()
        return
    
    email = sys.argv[1]
    
    # Use provided password or default
    if len(sys.argv) > 2:
        password = sys.argv[2]
    else:
        password = "password123"  # Default password
    
    print(f"Resetting password for: {email}")
    reset_password(email, password)

if __name__ == "__main__":
    main()