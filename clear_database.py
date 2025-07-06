"""
Clear all user data from the database for testing first user admin assignment
"""
from app import app, db
from models import *

def clear_all_data():
    """Clear all data from database tables"""
    with app.app_context():
        print('🔄 Clearing all data from database...')
        
        try:
            # Clear tables in order to respect foreign key constraints
            db.session.execute(db.text("DELETE FROM epic_comments"))
            db.session.execute(db.text("DELETE FROM epic_sync_logs"))
            db.session.execute(db.text("DELETE FROM project_comments"))
            db.session.execute(db.text("DELETE FROM project_milestones"))
            db.session.execute(db.text("DELETE FROM business_case_comments"))
            db.session.execute(db.text("DELETE FROM notifications"))
            db.session.execute(db.text("DELETE FROM audit_logs"))
            db.session.execute(db.text("DELETE FROM stories"))
            
            # Update foreign keys to NULL first
            db.session.execute(db.text("UPDATE epics SET case_id = NULL WHERE case_id IS NOT NULL"))
            db.session.execute(db.text("UPDATE business_cases SET project_id = NULL WHERE project_id IS NOT NULL"))
            
            # Now delete main data
            db.session.execute(db.text("DELETE FROM epics"))
            db.session.execute(db.text("DELETE FROM projects"))
            db.session.execute(db.text("DELETE FROM business_cases"))
            db.session.execute(db.text("DELETE FROM problems"))
            db.session.execute(db.text("DELETE FROM users"))
            db.session.execute(db.text("DELETE FROM departments"))
            
            db.session.commit()
            
            print('✅ Database cleared successfully!')
            
            # Verify empty database
            user_count = db.session.execute(db.text("SELECT count(*) FROM users")).scalar()
            dept_count = db.session.execute(db.text("SELECT count(*) FROM departments")).scalar()
            project_count = db.session.execute(db.text("SELECT count(*) FROM projects")).scalar()
            problem_count = db.session.execute(db.text("SELECT count(*) FROM problems")).scalar()
            
            print('📊 Verifying empty database:')
            print(f'   Users: {user_count}')
            print(f'   Departments: {dept_count}')
            print(f'   Projects: {project_count}')
            print(f'   Problems: {problem_count}')
            print('🎯 Ready for first user registration with automatic admin assignment!')
            
        except Exception as e:
            print(f'❌ Error clearing database: {e}')
            db.session.rollback()
            raise

if __name__ == "__main__":
    clear_all_data()