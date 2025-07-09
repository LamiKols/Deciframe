#!/usr/bin/env python3
"""
Quick demo password reset
"""
import os
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, text

def reset_demo_passwords():
    """Reset demo passwords quickly"""
    # Get database URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return
    
    # Create engine
    engine = create_engine(database_url)
    
    # Demo password
    demo_password = 'demo123'
    password_hash = generate_password_hash(demo_password)
    
    print(f"🔧 Setting demo password: {demo_password}")
    print(f"🔧 Password hash: {password_hash}")
    
    # Update passwords for demo accounts
    demo_accounts = [
        'info@sonartealchemy.com',
        'lami.kolade@gmail.com', 
        'Jay@mynewcompany.com'
    ]
    
    with engine.connect() as conn:
        for email in demo_accounts:
            try:
                result = conn.execute(
                    text("UPDATE users SET password_hash = :hash WHERE email = :email"),
                    {"hash": password_hash, "email": email}
                )
                conn.commit()
                print(f"✅ Updated password for: {email}")
            except Exception as e:
                print(f"❌ Failed to update {email}: {e}")
    
    print(f"\n🎯 Demo Credentials:")
    print(f"📧 Emails: {', '.join(demo_accounts)}")
    print(f"🔑 Password: {demo_password}")

if __name__ == '__main__':
    reset_demo_passwords()