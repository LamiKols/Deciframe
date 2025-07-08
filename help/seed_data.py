"""
Help Center Seed Data Script
Creates initial help articles for DeciFrame system
"""

import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app import db
from models import HelpCategory, HelpArticle, HelpArticleRoleEnum, Organization, User

def seed_help_articles():
    """Seed the database with initial help articles"""
    
    print("🌱 Starting Help Center seed data creation...")
    
    # Load seed data from JSON file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    seed_file = os.path.join(os.path.dirname(script_dir), 'help_articles_seed.json')
    
    try:
        with open(seed_file, 'r') as f:
            seed_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Seed file not found: {seed_file}")
        return False
    
    # Get the first organization (for seeding purposes)
    organization = Organization.query.first()
    if not organization:
        print("❌ No organization found. Please create an organization first.")
        return False
    
    # Get the first admin user (for author assignment)
    admin_user = User.query.filter_by(organization_id=organization.id).filter(
        User.role.in_(['Admin', 'CEO', 'Director'])
    ).first()
    
    if not admin_user:
        print("❌ No admin user found. Please create an admin user first.")
        return False
    
    print(f"📝 Seeding data for organization: {organization.name}")
    print(f"👤 Using admin user: {admin_user.email}")
    
    # Create help categories based on modules in seed data
    modules = set()
    for article_data in seed_data['help_articles']:
        if article_data.get('module_name'):
            modules.add(article_data['module_name'])
    
    # Create categories for each module
    categories = {}
    for module in modules:
        existing_category = HelpCategory.query.filter_by(
            name=module,
            organization_id=organization.id
        ).first()
        
        if not existing_category:
            category = HelpCategory(
                name=module,
                organization_id=organization.id,
                sort_order=len(categories)
            )
            db.session.add(category)
            db.session.flush()  # Get the ID
            categories[module] = category
            print(f"✅ Created category: {module}")
        else:
            categories[module] = existing_category
            print(f"📂 Using existing category: {module}")
    
    # Create a general category for articles without modules
    general_category = HelpCategory.query.filter_by(
        name="General",
        organization_id=organization.id
    ).first()
    
    if not general_category:
        general_category = HelpCategory(
            name="General",
            organization_id=organization.id,
            sort_order=99
        )
        db.session.add(general_category)
        db.session.flush()
        print("✅ Created category: General")
    
    # Create help articles
    articles_created = 0
    articles_updated = 0
    
    for article_data in seed_data['help_articles']:
        # Determine category
        module_name = article_data.get('module_name')
        category = categories.get(module_name, general_category)
        
        # Check if article already exists
        existing_article = HelpArticle.query.filter_by(
            title=article_data['title'],
            organization_id=organization.id
        ).first()
        
        if existing_article:
            # Update existing article
            existing_article.module_name = article_data.get('module_name')
            existing_article.content = article_data['content']
            existing_article.role = getattr(HelpArticleRoleEnum, article_data['role'])
            existing_article.tags = ','.join(article_data.get('tags', []))
            existing_article.faq = article_data.get('faq', [])
            existing_article.updated_at = datetime.utcnow()
            
            articles_updated += 1
            print(f"🔄 Updated article: {article_data['title']}")
        else:
            # Create new article
            article = HelpArticle(
                organization_id=organization.id,
                category_id=category.id,
                module_name=article_data.get('module_name'),
                title=article_data['title'],
                content=article_data['content'],
                role=getattr(HelpArticleRoleEnum, article_data['role']),
                tags=','.join(article_data.get('tags', [])),
                faq=article_data.get('faq', []),
                created_by=admin_user.id,
                sort_order=articles_created
            )
            
            # Generate slug
            article.slug = article.generate_slug()
            
            db.session.add(article)
            articles_created += 1
            print(f"✅ Created article: {article_data['title']}")
    
    # Commit all changes
    try:
        db.session.commit()
        print(f"\n🎉 Help Center seeding completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Categories: {len(categories) + 1}")  # +1 for General
        print(f"   - Articles created: {articles_created}")
        print(f"   - Articles updated: {articles_updated}")
        print(f"   - Total articles: {articles_created + articles_updated}")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error during seeding: {str(e)}")
        return False

def main():
    """Main function to run seeding"""
    from app import create_app
    
    app = create_app()
    with app.app_context():
        success = seed_help_articles()
        if success:
            print("\n✨ You can now access the Help Center at /help")
            print("🔗 Admin can manage articles at /admin/help-center")
        else:
            print("\n❌ Seeding failed. Please check the errors above.")

if __name__ == '__main__':
    main()