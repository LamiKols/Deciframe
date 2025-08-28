#!/usr/bin/env python3
"""
Migration script to add project_type field to business_cases table
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_migration():
    """Add project_type column to business_cases table"""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🔧 Adding project_type column to business_cases table...")
        
        # Add project_type column with default value of TECHNOLOGY
        session.execute(text("""
            ALTER TABLE business_cases 
            ADD COLUMN IF NOT EXISTS project_type VARCHAR(50) DEFAULT 'TECHNOLOGY'
        """))
        
        # Update existing records to have TECHNOLOGY as default project type
        session.execute(text("""
            UPDATE business_cases 
            SET project_type = 'TECHNOLOGY' 
            WHERE project_type IS NULL
        """))
        
        # Make the column NOT NULL after setting default values
        session.execute(text("""
            ALTER TABLE business_cases 
            ALTER COLUMN project_type SET NOT NULL
        """))
        
        session.commit()
        print("✅ Successfully added project_type column to business_cases table")
        
        # Verify the migration
        result = session.execute(text("""
            SELECT COUNT(*) as count, project_type 
            FROM business_cases 
            GROUP BY project_type
        """))
        
        print("📊 Current project_type distribution:")
        for row in result:
            print(f"  - {row.project_type}: {row.count} cases")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("✅ Migration completed successfully")
    else:
        print("❌ Migration failed")
        sys.exit(1)