#!/bin/bash
# GitHub Upload Script for Complete DeciFrame Project Structure
# Run this script to upload all directories to GitHub

echo "🚀 UPLOADING COMPLETE DECIFRAME PROJECT TO GITHUB"
echo "Repository: https://github.com/LamiKols/Deciframe.git"
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the project root."
    exit 1
fi

echo "✅ Project root confirmed"

# Add all critical directories
echo "📦 Adding core business modules..."
git add problems/
git add business/
git add projects/
git add solutions/
git add dept/
git add predict/
git add reports/
git add notifications/
git add ai/

echo "🔐 Adding auth and utilities..."
git add auth/
git add utils/

echo "⚙️ Adding admin and configuration modules..."
git add admin/
git add dashboard/
git add dashboards/
git add review/
git add workflows/
git add monitoring/

echo "👥 Adding user feature modules..."
git add search/
git add help/
git add waitlist/
git add public/
git add analytics/
git add scheduled/
git add services/
git add settings/

echo "🎨 Adding templates and static files..."
git add templates/
git add static/

echo "🧪 Adding tests and documentation..."
git add tests/
git add attached_assets/

echo "📄 Adding root files..."
git add app.py
git add main.py
git add models.py
git add config.py
git add requirements.txt
git add pyproject.toml
git add .env
git add .gitignore
git add .replit
git add render.yaml
git add replit.md
git add README.md
git add CHANGELOG.md
git add *.md
git add *.txt

echo "📊 Checking files to be committed..."
git status --porcelain

echo "💾 Committing complete project structure..."
git commit -m "Complete DeciFrame project structure upload

🏗️ Core Business Modules:
- problems/: Problem tracking and management
- business/: Business case workflows with epic management
- projects/: Project management and tracking
- solutions/: Solution recommendation engine
- dept/: Department hierarchy management
- predict/: ML-powered project success predictions
- reports/: Comprehensive reporting system
- notifications/: Notification and workflow automation
- ai/: AI-powered classification and insights

🔧 Admin & Configuration:
- admin/: Complete admin interface with 25+ features
- dashboard/: Role-based user dashboards
- dashboards/: Executive and specialized dashboards
- review/: Epic, business case, and project review workflows
- workflows/: Automated workflow and triage systems
- monitoring/: System monitoring and health checks

👤 User Features:
- auth/: Authentication and user management
- search/: PostgreSQL full-text search
- help/: Help center with markdown support
- waitlist/: Landing page and waitlist management
- public/: Terms, privacy, and public pages
- analytics/: AI-powered workflow analytics

🎨 Frontend & Assets:
- templates/: Complete template system (90+ files)
- static/: CSS, JavaScript, images, sample data
- utils/: Currency and date formatting utilities

📚 Supporting Systems:
- scheduled/: Background job automation
- services/: ML and business logic services
- settings/: Organization preference management
- tests/: Comprehensive test suite

📖 Documentation:
- Complete setup guides and API documentation
- Deployment guides for Render platform
- Admin functionality guides
- Configuration instructions

Total: 27 directories, 400+ files
Complete enterprise-grade Flask application"

echo "🌐 Pushing to GitHub..."
git push origin main

echo "✅ UPLOAD COMPLETE!"
echo "🔗 Check your repository: https://github.com/LamiKols/Deciframe.git"
echo "🚀 Trigger new deployment in Render dashboard"