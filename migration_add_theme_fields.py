#!/usr/bin/env python3
"""
Database migration script to add theme fields to User and OrganizationSettings models
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def get_database_connection():
    """Get database connection from environment variable"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return None
    
    try:
        # Parse the database URL
        result = urlparse(database_url)
        conn = psycopg2.connect(
            database=result.path[1:],  # Remove leading slash
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def run_migration():
    """Run the theme fields migration"""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if theme column already exists in users table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='theme'
        """)
        user_theme_exists = cursor.fetchone() is not None
        
        # Check if default_theme column already exists in organization_settings table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='organization_settings' AND column_name='default_theme'
        """)
        org_theme_exists = cursor.fetchone() is not None
        
        # Add theme column to users table if it doesn't exist
        if not user_theme_exists:
            print("🔧 Adding theme column to users table...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN theme VARCHAR(10) DEFAULT 'light'
            """)
            print("✅ Added theme column to users table")
        else:
            print("ℹ️ Theme column already exists in users table")
        
        # Add default_theme column to organization_settings table if it doesn't exist
        if not org_theme_exists:
            print("🔧 Adding default_theme column to organization_settings table...")
            cursor.execute("""
                ALTER TABLE organization_settings 
                ADD COLUMN default_theme VARCHAR(10) DEFAULT 'light'
            """)
            print("✅ Added default_theme column to organization_settings table")
        else:
            print("ℹ️ Default_theme column already exists in organization_settings table")
        
        # Commit the changes
        conn.commit()
        
        # Update any existing organization settings to have default_theme
        if not org_theme_exists:
            print("🔧 Updating existing organization settings with default theme...")
            cursor.execute("""
                UPDATE organization_settings 
                SET default_theme = 'light' 
                WHERE default_theme IS NULL
            """)
            conn.commit()
            print("✅ Updated existing organization settings")
        
        print("🎉 Theme fields migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🚀 Starting theme fields migration...")
    success = run_migration()
    if success:
        print("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)