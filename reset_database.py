"""
Complete database reset script - clears all data and users
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def reset_database():
    """Drop and recreate the entire database to clear all data"""
    
    # Get database connection info from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found")
        return False
    
    try:
        # Parse database URL to get connection details
        import urllib.parse as urlparse
        parsed = urlparse.urlparse(database_url)
        
        # Connect to postgres (not the specific database)
        postgres_conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            database='postgres'  # Connect to postgres database
        )
        postgres_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = postgres_conn.cursor()
        
        db_name = parsed.path[1:]  # Remove leading slash
        
        print(f"🔄 Resetting database: {db_name}")
        
        # Terminate existing connections to the database
        cursor.execute(f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
        """)
        
        # Drop and recreate the database
        cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
        cursor.execute(f'CREATE DATABASE "{db_name}"')
        
        cursor.close()
        postgres_conn.close()
        
        print(f"✅ Database {db_name} reset successfully")
        print("🎯 Database is now completely empty - ready for first user admin assignment!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False

def recreate_tables():
    """Recreate all tables using Flask-SQLAlchemy"""
    try:
        from app import app, db
        
        with app.app_context():
            print("🔄 Recreating database tables...")
            db.create_all()
            print("✅ All tables recreated successfully")
            
            # Verify empty state
            from models import User, Department, Project, Problem
            print("📊 Verifying empty database:")
            print(f"   Users: {User.query.count()}")
            print(f"   Departments: {Department.query.count()}")
            print(f"   Projects: {Project.query.count()}")
            print(f"   Problems: {Problem.query.count()}")
            
    except Exception as e:
        print(f"❌ Error recreating tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if reset_database():
        recreate_tables()
        print("\n🎉 Database reset complete!")
        print("Next user registration will trigger automatic admin assignment.")
    else:
        print("\n❌ Database reset failed.")