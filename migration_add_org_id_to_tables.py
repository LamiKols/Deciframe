#!/usr/bin/env python3
"""
Add organization_id to all tables that need multi-tenant isolation
This migration ensures proper data separation between organizations
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def add_organization_id_to_tables():
    """Add organization_id column to tables that need multi-tenant isolation"""
    
    # Database connection
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        conn.set_session(autocommit=False)
        
        print("🔧 Starting multi-tenant table migration...")
        
        # Tables that need organization_id for data isolation
        tables_to_update = [
            'org_units',
            'departments', 
            'problems',
            'business_cases',
            'projects',
            'project_milestones',
            'notifications',
            'notification_templates',
            'epic_sync_logs',
            'analytics_data',
            'triage_rules'
        ]
        
        # 1. Add organization_id column to tables
        for table in tables_to_update:
            try:
                # Check if table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    )
                """, (table,))
                
                if not cursor.fetchone()[0]:
                    print(f"⚠️ Table {table} does not exist, skipping...")
                    continue
                
                # Check if organization_id column already exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = 'organization_id'
                    )
                """, (table,))
                
                if cursor.fetchone()[0]:
                    print(f"✅ Table {table} already has organization_id column")
                    continue
                
                # Add organization_id column
                cursor.execute(f"""
                    ALTER TABLE {table} 
                    ADD COLUMN organization_id INTEGER 
                    REFERENCES organizations(id)
                """)
                print(f"✅ Added organization_id to {table}")
                
            except Exception as e:
                print(f"❌ Error updating table {table}: {str(e)}")
                continue
        
        # 2. Get the default organization (should exist from previous migration)
        cursor.execute("SELECT id FROM organizations WHERE domain = 'default.local' LIMIT 1")
        default_org_result = cursor.fetchone()
        
        if not default_org_result:
            print("❌ Default organization not found! Run migration_restore_multitenant.py first")
            return False
            
        default_org_id = default_org_result['id']
        print(f"🏢 Using default organization ID: {default_org_id}")
        
        # 3. Update existing records to belong to default organization
        for table in tables_to_update:
            try:
                # Check if table exists and has organization_id column
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = 'organization_id'
                    )
                """, (table,))
                
                if not cursor.fetchone()[0]:
                    continue
                
                # Update NULL organization_id values
                cursor.execute(f"""
                    UPDATE {table} 
                    SET organization_id = %s 
                    WHERE organization_id IS NULL
                """, (default_org_id,))
                
                updated_count = cursor.rowcount
                print(f"✅ Updated {updated_count} records in {table}")
                
            except Exception as e:
                print(f"❌ Error updating records in {table}: {str(e)}")
                continue
        
        # 4. Make organization_id NOT NULL for critical tables
        critical_tables = ['org_units', 'departments', 'problems', 'business_cases', 'projects']
        
        for table in critical_tables:
            try:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = 'organization_id'
                    )
                """, (table,))
                
                if not cursor.fetchone()[0]:
                    continue
                
                cursor.execute(f"""
                    ALTER TABLE {table} 
                    ALTER COLUMN organization_id SET NOT NULL
                """)
                print(f"✅ Made organization_id NOT NULL in {table}")
                
            except Exception as e:
                print(f"❌ Error making organization_id NOT NULL in {table}: {str(e)}")
                continue
        
        # 5. Create indexes for performance
        for table in tables_to_update:
            try:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = 'organization_id'
                    )
                """, (table,))
                
                if not cursor.fetchone()[0]:
                    continue
                
                index_name = f"idx_{table}_organization_id"
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS {index_name} 
                    ON {table} (organization_id)
                """)
                print(f"✅ Created index for {table}.organization_id")
                
            except Exception as e:
                print(f"❌ Error creating index for {table}: {str(e)}")
                continue
        
        # Commit all changes
        conn.commit()
        print("🎉 Multi-tenant table migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = add_organization_id_to_tables()
    sys.exit(0 if success else 1)