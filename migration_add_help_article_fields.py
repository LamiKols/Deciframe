"""
Database Migration: Add Enhanced Help Article Fields
Adds module_name, role, tags, faq, and analytics fields to help_articles table
"""

from app import db
from sqlalchemy import text

def migrate_help_articles():
    """Add new fields to help_articles table"""
    
    print("🔧 Starting Help Articles database migration...")
    
    try:
        # Check if columns already exist
        inspector = db.inspect(db.engine)
        columns = inspector.get_columns('help_articles')
        existing_columns = [col['name'] for col in columns]
        
        # Add missing columns
        migrations = []
        
        if 'module_name' not in existing_columns:
            migrations.append("ALTER TABLE help_articles ADD COLUMN module_name VARCHAR(100)")
            
        if 'role' not in existing_columns:
            migrations.append("ALTER TABLE help_articles ADD COLUMN role VARCHAR(10) DEFAULT 'both'")
            
        if 'tags' not in existing_columns:
            migrations.append("ALTER TABLE help_articles ADD COLUMN tags VARCHAR(500)")
            
        if 'faq' not in existing_columns:
            migrations.append("ALTER TABLE help_articles ADD COLUMN faq JSON")
            
        if 'view_count' not in existing_columns:
            migrations.append("ALTER TABLE help_articles ADD COLUMN view_count INTEGER DEFAULT 0")
            
        if 'helpful_count' not in existing_columns:
            migrations.append("ALTER TABLE help_articles ADD COLUMN helpful_count INTEGER DEFAULT 0")
            
        if 'not_helpful_count' not in existing_columns:
            migrations.append("ALTER TABLE help_articles ADD COLUMN not_helpful_count INTEGER DEFAULT 0")
        
        # Execute migrations
        if migrations:
            for migration in migrations:
                print(f"✅ Executing: {migration}")
                db.session.execute(text(migration))
            
            db.session.commit()
            print(f"🎉 Successfully added {len(migrations)} new columns to help_articles table")
        else:
            print("✅ All columns already exist, no migration needed")
            
        # Update existing records to have default values
        print("🔄 Updating existing records with default values...")
        
        # Set default role for existing articles
        db.session.execute(text(
            "UPDATE help_articles SET role = 'both' WHERE role IS NULL"
        ))
        
        # Set default analytics values
        db.session.execute(text(
            "UPDATE help_articles SET view_count = 0 WHERE view_count IS NULL"
        ))
        db.session.execute(text(
            "UPDATE help_articles SET helpful_count = 0 WHERE helpful_count IS NULL"
        ))
        db.session.execute(text(
            "UPDATE help_articles SET not_helpful_count = 0 WHERE not_helpful_count IS NULL"
        ))
        
        db.session.commit()
        print("✅ Updated existing records with default values")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == '__main__':
    from app import create_app
    
    app = create_app()
    with app.app_context():
        success = migrate_help_articles()
        if success:
            print("\n🎉 Help Articles migration completed successfully!")
            print("🔗 You can now access the enhanced Help Center")
        else:
            print("\n❌ Migration failed. Please check the errors above.")