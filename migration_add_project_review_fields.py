#!/usr/bin/env python3
"""
Migration script to add project review fields
- submitted_by (foreign key to users)
- submitted_at (datetime)
- approved_by (foreign key to users)  
- approved_at (datetime)
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
import psycopg2

def add_project_review_fields():
    """Add review fields to projects table and create project_comments table"""
    
    try:
        # Get database connection details from app config
        database_url = app.config['SQLALCHEMY_DATABASE_URI']
        
        # Parse the database URL to get connection parameters
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgres://', 1)
        
        # Connect to database directly
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🔧 Starting Project Review Fields Migration...")
        
        # 1. Add review fields to projects table
        print("📝 Adding review fields to projects table...")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'projects' 
            AND column_name IN ('submitted_by', 'submitted_at', 'approved_by', 'approved_at')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add submitted_by column if it doesn't exist
        if 'submitted_by' not in existing_columns:
            cursor.execute("""
                ALTER TABLE projects 
                ADD COLUMN submitted_by INTEGER REFERENCES users(id)
            """)
            print("✓ Added submitted_by column")
        else:
            print("⚠️ submitted_by column already exists")
            
        # Add submitted_at column if it doesn't exist
        if 'submitted_at' not in existing_columns:
            cursor.execute("""
                ALTER TABLE projects 
                ADD COLUMN submitted_at TIMESTAMP
            """)
            print("✓ Added submitted_at column")
        else:
            print("⚠️ submitted_at column already exists")
            
        # Add approved_by column if it doesn't exist
        if 'approved_by' not in existing_columns:
            cursor.execute("""
                ALTER TABLE projects 
                ADD COLUMN approved_by INTEGER REFERENCES users(id)
            """)
            print("✓ Added approved_by column")
        else:
            print("⚠️ approved_by column already exists")
            
        # Add approved_at column if it doesn't exist
        if 'approved_at' not in existing_columns:
            cursor.execute("""
                ALTER TABLE projects 
                ADD COLUMN approved_at TIMESTAMP
            """)
            print("✓ Added approved_at column")
        else:
            print("⚠️ approved_at column already exists")
        
        # 2. Create project_comments table
        print("💬 Creating project_comments table...")
        
        # Check if table already exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'project_comments'
        """)
        
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE project_comments (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    author_id INTEGER NOT NULL REFERENCES users(id),
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✓ Created project_comments table")
            
            # Create index for better query performance
            cursor.execute("""
                CREATE INDEX idx_project_comments_project_id ON project_comments(project_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_project_comments_created_at ON project_comments(created_at)
            """)
            print("✓ Created indexes for project_comments")
        else:
            print("⚠️ project_comments table already exists")
        
        # 3. Check if notification event types exist for projects
        print("🔔 Checking notification event types...")
        
        cursor.execute("""
            SELECT unnest(enum_range(NULL::notificationeventenum))
        """)
        event_types = [row[0] for row in cursor.fetchall()]
        
        # Add PROJECT_APPROVED if it doesn't exist
        if 'PROJECT_APPROVED' not in event_types:
            cursor.execute("""
                ALTER TYPE notificationeventenum ADD VALUE 'PROJECT_APPROVED'
            """)
            print("✓ Added PROJECT_APPROVED notification event")
        else:
            print("⚠️ PROJECT_APPROVED event already exists")
            
        # Add PROJECT_NEEDS_REVISION if it doesn't exist  
        if 'PROJECT_NEEDS_REVISION' not in event_types:
            cursor.execute("""
                ALTER TYPE notificationeventenum ADD VALUE 'PROJECT_NEEDS_REVISION'
            """)
            print("✓ Added PROJECT_NEEDS_REVISION notification event")
        else:
            print("⚠️ PROJECT_NEEDS_REVISION event already exists")
        
        # Commit all changes
        conn.commit()
        print("✅ Project review fields migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    with app.app_context():
        add_project_review_fields()