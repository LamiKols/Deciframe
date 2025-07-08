#!/usr/bin/env python3
"""
Database migration script to restore multi-tenant architecture
Adds Organization model and organization_id fields
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
        result = urlparse(database_url)
        conn = psycopg2.connect(
            database=result.path[1:],
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
    """Run the multi-tenant architecture migration"""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        print("🔧 Starting multi-tenant architecture restoration...")
        
        # 1. Create organizations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                domain VARCHAR(100) UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                subscription_plan VARCHAR(50) DEFAULT 'basic',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created organizations table")
        
        # 2. Create default organization for existing data
        cursor.execute("""
            INSERT INTO organizations (name, domain, is_active, subscription_plan)
            VALUES ('Default Organization', 'default.local', TRUE, 'enterprise')
            ON CONFLICT (domain) DO NOTHING
        """)
        print("✅ Created default organization")
        
        # 3. Add organization_id to users table (allow NULL initially)
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS organization_id INTEGER 
            REFERENCES organizations(id)
        """)
        print("✅ Added organization_id to users table")
        
        # 4. Update existing users to belong to default organization
        cursor.execute("""
            UPDATE users 
            SET organization_id = (SELECT id FROM organizations WHERE domain = 'default.local')
            WHERE organization_id IS NULL
        """)
        print("✅ Updated existing users with default organization")
        
        # 5. Make organization_id NOT NULL now that all users have it
        cursor.execute("""
            ALTER TABLE users 
            ALTER COLUMN organization_id SET NOT NULL
        """)
        print("✅ Made organization_id NOT NULL")
        
        # 6. Update organization_settings table
        cursor.execute("""
            ALTER TABLE organization_settings 
            ADD COLUMN IF NOT EXISTS organization_id INTEGER 
            REFERENCES organizations(id)
        """)
        print("✅ Added organization_id to organization_settings")
        
        # 7. Update existing organization settings
        cursor.execute("""
            UPDATE organization_settings 
            SET organization_id = (SELECT id FROM organizations WHERE domain = 'default.local')
            WHERE organization_id IS NULL
        """)
        print("✅ Updated organization settings")
        
        # 8. Remove old org_id column if it exists
        cursor.execute("""
            ALTER TABLE organization_settings 
            DROP COLUMN IF EXISTS org_id
        """)
        print("✅ Removed old org_id column")
        
        conn.commit()
        print("🎉 Multi-tenant architecture restoration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
