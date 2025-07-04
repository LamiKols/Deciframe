"""
PostgreSQL Full-Text Search Setup for DeciFrame
Adds tsvector columns, GIN indexes, and triggers for automatic search vector updates
"""

from app import app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_fulltext_search():
    """Set up PostgreSQL full-text search for Problems, BusinessCases, and Projects"""
    
    with app.app_context():
        try:
            # Drop existing search columns if they exist (for clean setup)
            logger.info("Cleaning up existing search columns...")
            cleanup_queries = [
                "ALTER TABLE problems DROP COLUMN IF EXISTS search_vector",
                "ALTER TABLE business_cases DROP COLUMN IF EXISTS search_vector", 
                "ALTER TABLE projects DROP COLUMN IF EXISTS search_vector"
            ]
            
            for query in cleanup_queries:
                try:
                    db.session.execute(text(query))
                except Exception as e:
                    logger.warning(f"Cleanup query failed (expected): {e}")
            
            db.session.commit()
            
            # 1. Add tsvector columns for Problems
            logger.info("Adding search_vector column to problems table...")
            db.session.execute(text("""
                ALTER TABLE problems ADD COLUMN search_vector tsvector
            """))
            
            # 2. Add tsvector columns for Business Cases
            logger.info("Adding search_vector column to business_cases table...")
            db.session.execute(text("""
                ALTER TABLE business_cases ADD COLUMN search_vector tsvector
            """))
            
            # 3. Add tsvector columns for Projects
            logger.info("Adding search_vector column to projects table...")
            db.session.execute(text("""
                ALTER TABLE projects ADD COLUMN search_vector tsvector
            """))
            
            # 4. Create GIN indexes for fast full-text search
            logger.info("Creating GIN indexes for search vectors...")
            
            db.session.execute(text("""
                CREATE INDEX idx_problems_search ON problems USING GIN(search_vector)
            """))
            
            db.session.execute(text("""
                CREATE INDEX idx_business_cases_search ON business_cases USING GIN(search_vector)
            """))
            
            db.session.execute(text("""
                CREATE INDEX idx_projects_search ON projects USING GIN(search_vector)
            """))
            
            # 5. Create triggers for automatic search vector updates
            logger.info("Creating triggers for automatic search vector updates...")
            
            # Problems trigger
            db.session.execute(text("""
                CREATE TRIGGER tsvectorupdate_problems 
                BEFORE INSERT OR UPDATE ON problems 
                FOR EACH ROW EXECUTE FUNCTION
                tsvector_update_trigger('search_vector', 'pg_catalog.english', 'title', 'description')
            """))
            
            # Business Cases trigger (includes more fields)
            db.session.execute(text("""
                CREATE TRIGGER tsvectorupdate_business_cases 
                BEFORE INSERT OR UPDATE ON business_cases 
                FOR EACH ROW EXECUTE FUNCTION
                tsvector_update_trigger('search_vector', 'pg_catalog.english', 'title', 'description', 'summary', 'initiative_name')
            """))
            
            # Projects trigger
            db.session.execute(text("""
                CREATE TRIGGER tsvectorupdate_projects 
                BEFORE INSERT OR UPDATE ON projects 
                FOR EACH ROW EXECUTE FUNCTION
                tsvector_update_trigger('search_vector', 'pg_catalog.english', 'name', 'description')
            """))
            
            # 6. Populate existing records with search vectors
            logger.info("Populating search vectors for existing records...")
            
            # Update existing Problems
            db.session.execute(text("""
                UPDATE problems SET search_vector = 
                to_tsvector('pg_catalog.english', COALESCE(title, '') || ' ' || COALESCE(description, ''))
                WHERE search_vector IS NULL
            """))
            
            # Update existing Business Cases
            db.session.execute(text("""
                UPDATE business_cases SET search_vector = 
                to_tsvector('pg_catalog.english', 
                    COALESCE(title, '') || ' ' || 
                    COALESCE(description, '') || ' ' || 
                    COALESCE(summary, '') || ' ' || 
                    COALESCE(initiative_name, '')
                )
                WHERE search_vector IS NULL
            """))
            
            # Update existing Projects
            db.session.execute(text("""
                UPDATE projects SET search_vector = 
                to_tsvector('pg_catalog.english', COALESCE(name, '') || ' ' || COALESCE(description, ''))
                WHERE search_vector IS NULL
            """))
            
            db.session.commit()
            logger.info("✓ Full-text search setup completed successfully!")
            
            # Test the search functionality
            logger.info("Testing search functionality...")
            test_search()
            
        except Exception as e:
            logger.error(f"Error setting up full-text search: {e}")
            db.session.rollback()
            raise

def test_search():
    """Test the full-text search functionality"""
    try:
        # Test problems search
        result = db.session.execute(text("""
            SELECT title, ts_rank(search_vector, query) as rank
            FROM problems, to_tsquery('english', 'performance | optimization') query
            WHERE search_vector @@ query
            ORDER BY rank DESC
            LIMIT 5
        """)).fetchall()
        
        logger.info(f"Found {len(result)} problems matching test search")
        
        # Test business cases search
        result = db.session.execute(text("""
            SELECT title, ts_rank(search_vector, query) as rank
            FROM business_cases, to_tsquery('english', 'cost | benefit') query
            WHERE search_vector @@ query
            ORDER BY rank DESC
            LIMIT 5
        """)).fetchall()
        
        logger.info(f"Found {len(result)} business cases matching test search")
        
        # Test projects search
        result = db.session.execute(text("""
            SELECT name, ts_rank(search_vector, query) as rank
            FROM projects, to_tsquery('english', 'infrastructure | system') query
            WHERE search_vector @@ query
            ORDER BY rank DESC
            LIMIT 5
        """)).fetchall()
        
        logger.info(f"Found {len(result)} projects matching test search")
        logger.info("✓ Search functionality tests passed!")
        
    except Exception as e:
        logger.warning(f"Search test failed (may be due to no data): {e}")

def drop_fulltext_search():
    """Remove full-text search setup (for testing/cleanup)"""
    with app.app_context():
        try:
            logger.info("Removing full-text search setup...")
            
            # Drop triggers
            drop_queries = [
                "DROP TRIGGER IF EXISTS tsvectorupdate_problems ON problems",
                "DROP TRIGGER IF EXISTS tsvectorupdate_business_cases ON business_cases", 
                "DROP TRIGGER IF EXISTS tsvectorupdate_projects ON projects",
                "DROP INDEX IF EXISTS idx_problems_search",
                "DROP INDEX IF EXISTS idx_business_cases_search",
                "DROP INDEX IF EXISTS idx_projects_search",
                "ALTER TABLE problems DROP COLUMN IF EXISTS search_vector",
                "ALTER TABLE business_cases DROP COLUMN IF EXISTS search_vector",
                "ALTER TABLE projects DROP COLUMN IF EXISTS search_vector"
            ]
            
            for query in drop_queries:
                try:
                    db.session.execute(text(query))
                except Exception as e:
                    logger.warning(f"Drop query failed: {e}")
            
            db.session.commit()
            logger.info("✓ Full-text search setup removed")
            
        except Exception as e:
            logger.error(f"Error removing full-text search: {e}")
            db.session.rollback()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        drop_fulltext_search()
    else:
        setup_fulltext_search()