#!/usr/bin/env python3
"""
Database migration to add onboarded field to User model
"""

import psycopg2
import os
from urllib.parse import urlparse

def add_onboarded_field():
    """Add onboarded field to users table"""
    try:
        # Parse DATABASE_URL
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("DATABASE_URL environment variable not found")
            return False
            
        # Parse the URL
        parsed = urlparse(database_url)
        
        # Connect to database
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password
        )
        
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='onboarded'
        """)
        
        if cursor.fetchone():
            print("Column 'onboarded' already exists in users table")
            cursor.close()
            conn.close()
            return True
            
        # Add the onboarded column
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN onboarded BOOLEAN DEFAULT FALSE
        """)
        
        # Update existing users to have onboarded=False by default
        cursor.execute("""
            UPDATE users 
            SET onboarded = FALSE 
            WHERE onboarded IS NULL
        """)
        
        conn.commit()
        print("✓ Successfully added 'onboarded' column to users table")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error adding onboarded field: {e}")
        return False

if __name__ == "__main__":
    success = add_onboarded_field()
    if success:
        print("Migration completed successfully")
    else:
        print("Migration failed")