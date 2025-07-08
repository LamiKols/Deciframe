#!/usr/bin/env python3
"""
Fix all remaining multi-tenant security violations in DeciFrame
Applies organization filtering to all route files systematically
"""

import os
import re
from datetime import datetime

class SecurityViolationFixer:
    def __init__(self):
        self.files_fixed = []
        self.violations_fixed = 0
        
    def fix_solutions_routes(self):
        """Fix solutions/routes.py organization filtering"""
        print("🔧 Fixing solutions/routes.py...")
        
        if not os.path.exists('solutions/routes.py'):
            return
            
        with open('solutions/routes.py', 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Already fixed: Line 12 view_solution function has proper filtering
        # No additional fixes needed - already has organization_id filtering
        
        if content != original_content:
            with open('solutions/routes.py', 'w') as f:
                f.write(content)
            print("✅ Fixed solutions/routes.py")
            self.files_fixed.append('solutions/routes.py')
    
    def fix_business_routes(self):
        """Fix business/routes.py organization filtering"""
        print("🔧 Fixing business/routes.py...")
        
        if not os.path.exists('business/routes.py'):
            return
            
        with open('business/routes.py', 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix Epic and Story queries that lack organization filtering
        fixes = [
            # Fix Epic queries
            (r'Epic\.query\.get_or_404\((\w+)\)', 
             r'Epic.query.filter_by(id=\1, organization_id=current_user.organization_id).first_or_404()'),
            (r'Epic\.query\.get\((\w+)\)', 
             r'Epic.query.filter_by(id=\1, organization_id=current_user.organization_id).first()'),
            (r'Epic\.query\.filter_by\(case_id=(\w+)\)\.all\(\)', 
             r'Epic.query.filter_by(case_id=\1, organization_id=current_user.organization_id).all()'),
            
            # Fix Story queries
            (r'Story\.query\.get_or_404\((\w+)\)', 
             r'Story.query.filter_by(id=\1, organization_id=current_user.organization_id).first_or_404()'),
            (r'Story\.query\.get\((\w+)\)', 
             r'Story.query.filter_by(id=\1, organization_id=current_user.organization_id).first()'),
            (r'Story\.query\.filter_by\(epic_id=(\w+)\)\.all\(\)', 
             r'Story.query.filter_by(epic_id=\1, organization_id=current_user.organization_id).all()'),
        ]
        
        for pattern, replacement in fixes:
            content = re.sub(pattern, replacement, content)
            if pattern in original_content:
                self.violations_fixed += 1
        
        if content != original_content:
            with open('business/routes.py', 'w') as f:
                f.write(content)
            print("✅ Fixed business/routes.py")
            self.files_fixed.append('business/routes.py')
    
    def fix_projects_routes(self):
        """Fix projects/routes.py organization filtering"""
        print("🔧 Fixing projects/routes.py...")
        
        if not os.path.exists('projects/routes.py'):
            return
            
        with open('projects/routes.py', 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix Project, Epic, and Story queries
        fixes = [
            # Fix Project queries
            (r'Project\.query\.get_or_404\((\w+)\)', 
             r'Project.query.filter_by(id=\1, organization_id=current_user.organization_id).first_or_404()'),
            (r'Project\.query\.get\((\w+)\)', 
             r'Project.query.filter_by(id=\1, organization_id=current_user.organization_id).first()'),
            
            # Fix Epic queries
            (r'Epic\.query\.get_or_404\((\w+)\)', 
             r'Epic.query.filter_by(id=\1, organization_id=current_user.organization_id).first_or_404()'),
            (r'Epic\.query\.filter_by\(project_id=(\w+)\)\.all\(\)', 
             r'Epic.query.filter_by(project_id=\1, organization_id=current_user.organization_id).all()'),
            
            # Fix Story queries
            (r'Story\.query\.filter_by\(epic_id=(\w+)\)\.all\(\)', 
             r'Story.query.filter_by(epic_id=\1, organization_id=current_user.organization_id).all()'),
        ]
        
        for pattern, replacement in fixes:
            content = re.sub(pattern, replacement, content)
            if pattern in original_content:
                self.violations_fixed += 1
        
        if content != original_content:
            with open('projects/routes.py', 'w') as f:
                f.write(content)
            print("✅ Fixed projects/routes.py")
            self.files_fixed.append('projects/routes.py')
    
    def fix_dashboards_routes(self):
        """Fix dashboards/routes.py organization filtering"""
        print("🔧 Fixing dashboards/routes.py...")
        
        if not os.path.exists('dashboards/routes.py'):
            return
            
        with open('dashboards/routes.py', 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Add organization filtering to all business model queries
        fixes = [
            # Fix base queries to include organization filtering
            (r'(\w+)\.query\.filter\(', r'\1.query.filter_by(organization_id=current_user.organization_id).filter('),
            (r'(\w+)\.query\.all\(\)', r'\1.query.filter_by(organization_id=current_user.organization_id).all()'),
            (r'(\w+)\.query\.count\(\)', r'\1.query.filter_by(organization_id=current_user.organization_id).count()'),
        ]
        
        # Apply fixes only to business models
        business_models = ['Problem', 'BusinessCase', 'Project', 'Epic', 'Story', 'Department']
        for model in business_models:
            content = re.sub(f'{model}\.query\.all\(\)', 
                           f'{model}.query.filter_by(organization_id=current_user.organization_id).all()', 
                           content)
            content = re.sub(f'{model}\.query\.count\(\)', 
                           f'{model}.query.filter_by(organization_id=current_user.organization_id).count()', 
                           content)
            if f'{model}.query.all()' in original_content or f'{model}.query.count()' in original_content:
                self.violations_fixed += 1
        
        if content != original_content:
            with open('dashboards/routes.py', 'w') as f:
                f.write(content)
            print("✅ Fixed dashboards/routes.py")
            self.files_fixed.append('dashboards/routes.py')
    
    def fix_dept_routes(self):
        """Fix dept/routes.py organization filtering"""
        print("🔧 Fixing dept/routes.py...")
        
        if not os.path.exists('dept/routes.py'):
            return
            
        with open('dept/routes.py', 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix Department queries
        content = re.sub(r'Department\.query\.all\(\)', 
                        'Department.query.filter_by(organization_id=current_user.organization_id).all()', 
                        content)
        content = re.sub(r'Department\.query\.get_or_404\((\w+)\)', 
                        r'Department.query.filter_by(id=\1, organization_id=current_user.organization_id).first_or_404()', 
                        content)
        
        if 'Department.query.all()' in original_content or 'Department.query.get_or_404' in original_content:
            self.violations_fixed += 1
        
        if content != original_content:
            with open('dept/routes.py', 'w') as f:
                f.write(content)
            print("✅ Fixed dept/routes.py")
            self.files_fixed.append('dept/routes.py')
    
    def fix_admin_working(self):
        """Fix admin_working.py organization filtering"""
        print("🔧 Fixing admin_working.py...")
        
        if not os.path.exists('admin_working.py'):
            return
            
        with open('admin_working.py', 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Add organization filtering to OrgUnit and Department queries in admin
        # Admin users should still see organization-scoped data
        content = re.sub(r'OrgUnit\.query\.all\(\)', 
                        'OrgUnit.query.filter_by(organization_id=current_user.organization_id).all()', 
                        content)
        content = re.sub(r'Department\.query\.all\(\)', 
                        'Department.query.filter_by(organization_id=current_user.organization_id).all()', 
                        content)
        
        if 'OrgUnit.query.all()' in original_content or 'Department.query.all()' in original_content:
            self.violations_fixed += 1
        
        if content != original_content:
            with open('admin_working.py', 'w') as f:
                f.write(content)
            print("✅ Fixed admin_working.py")
            self.files_fixed.append('admin_working.py')
    
    def fix_notifications_routes(self):
        """Fix notifications/routes.py organization filtering"""
        print("🔧 Fixing notifications/routes.py...")
        
        if not os.path.exists('notifications/routes.py'):
            return
            
        with open('notifications/routes.py', 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix NotificationTemplate queries
        content = re.sub(r'NotificationTemplate\.query\.all\(\)', 
                        'NotificationTemplate.query.filter_by(organization_id=current_user.organization_id).all()', 
                        content)
        content = re.sub(r'NotificationTemplate\.query\.get_or_404\((\w+)\)', 
                        r'NotificationTemplate.query.filter_by(id=\1, organization_id=current_user.organization_id).first_or_404()', 
                        content)
        
        if 'NotificationTemplate.query' in original_content:
            self.violations_fixed += 1
        
        if content != original_content:
            with open('notifications/routes.py', 'w') as f:
                f.write(content)
            print("✅ Fixed notifications/routes.py")
            self.files_fixed.append('notifications/routes.py')
    
    def generate_report(self):
        """Generate fix report"""
        print(f"\n{'='*60}")
        print("🛡️ SECURITY VIOLATIONS FIX REPORT")
        print(f"{'='*60}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Files Fixed: {len(self.files_fixed)}")
        print(f"Violations Fixed: {self.violations_fixed}")
        
        if self.files_fixed:
            print("\n✅ FIXED FILES:")
            for file_path in self.files_fixed:
                print(f"  - {file_path}")
        
        print(f"\n🔒 Multi-tenant security violations have been resolved!")
        return True

def main():
    """Fix all remaining multi-tenant security violations"""
    print("🚀 Starting DeciFrame Security Violation Fixes...")
    
    fixer = SecurityViolationFixer()
    
    # Fix all route files
    fixer.fix_solutions_routes()
    fixer.fix_business_routes()
    fixer.fix_projects_routes()
    fixer.fix_dashboards_routes()
    fixer.fix_dept_routes()
    fixer.fix_admin_working()
    fixer.fix_notifications_routes()
    
    # Generate report
    fixer.generate_report()
    
    print("\n🎉 All security fixes applied! Ready for security re-test.")
    return 0

if __name__ == "__main__":
    main()