"""
CRITICAL SECURITY FIX: Multi-Tenant Data Isolation
Fixes organization_id missing from Problems, BusinessCases, and Projects
"""

from app import create_app, db
from models import Problem, BusinessCase, Project, User
from sqlalchemy import text

def fix_organization_data_isolation():
    """Add organization_id to core models and populate from user data"""
    from app import app
    
    with app.app_context():
        print("🚨 CRITICAL SECURITY FIX: Adding organization_id fields to core models")
        
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            
            # Add organization_id to problems table
            problems_columns = [col['name'] for col in inspector.get_columns('problems')]
            if 'organization_id' not in problems_columns:
                print("📝 Adding organization_id to problems table...")
                db.session.execute(text("""
                    ALTER TABLE problems 
                    ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
                """))
                
                # Populate organization_id from creator's organization
                db.session.execute(text("""
                    UPDATE problems 
                    SET organization_id = (
                        SELECT u.organization_id 
                        FROM users u 
                        WHERE u.id = problems.created_by
                    );
                """))
                
                # Make the column NOT NULL after population
                db.session.execute(text("""
                    ALTER TABLE problems 
                    ALTER COLUMN organization_id SET NOT NULL;
                """))
                print("✅ Problems table organization_id field added and populated")
            
            # Add organization_id to business_cases table
            bc_columns = [col['name'] for col in inspector.get_columns('business_cases')]
            if 'organization_id' not in bc_columns:
                print("📝 Adding organization_id to business_cases table...")
                db.session.execute(text("""
                    ALTER TABLE business_cases 
                    ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
                """))
                
                # Populate organization_id from creator's organization
                db.session.execute(text("""
                    UPDATE business_cases 
                    SET organization_id = (
                        SELECT u.organization_id 
                        FROM users u 
                        WHERE u.id = business_cases.created_by
                    );
                """))
                
                # Make the column NOT NULL after population
                db.session.execute(text("""
                    ALTER TABLE business_cases 
                    ALTER COLUMN organization_id SET NOT NULL;
                """))
                print("✅ Business cases table organization_id field added and populated")
            
            # Add organization_id to projects table
            projects_columns = [col['name'] for col in inspector.get_columns('projects')]
            if 'organization_id' not in projects_columns:
                print("📝 Adding organization_id to projects table...")
                db.session.execute(text("""
                    ALTER TABLE projects 
                    ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
                """))
                
                # Populate organization_id from creator's organization
                db.session.execute(text("""
                    UPDATE projects 
                    SET organization_id = (
                        SELECT u.organization_id 
                        FROM users u 
                        WHERE u.id = projects.created_by
                    );
                """))
                
                # Make the column NOT NULL after population
                db.session.execute(text("""
                    ALTER TABLE projects 
                    ALTER COLUMN organization_id SET NOT NULL;
                """))
                print("✅ Projects table organization_id field added and populated")
            
            db.session.commit()
            print("🔒 CRITICAL SECURITY FIX COMPLETE: Multi-tenant data isolation restored")
            
            # Verify data isolation
            print("\n📊 Data isolation verification:")
            orgs_with_data = db.session.execute(text("""
                SELECT 
                    o.name as org_name,
                    COUNT(DISTINCT p.id) as problems,
                    COUNT(DISTINCT bc.id) as business_cases,
                    COUNT(DISTINCT pr.id) as projects
                FROM organizations o
                LEFT JOIN problems p ON p.organization_id = o.id
                LEFT JOIN business_cases bc ON bc.organization_id = o.id  
                LEFT JOIN projects pr ON pr.organization_id = o.id
                GROUP BY o.id, o.name
                ORDER BY o.name;
            """)).fetchall()
            
            for row in orgs_with_data:
                print(f"  {row.org_name}: {row.problems} problems, {row.business_cases} cases, {row.projects} projects")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing data isolation: {e}")
            raise

if __name__ == "__main__":
    fix_organization_data_isolation()