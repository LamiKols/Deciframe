#!/usr/bin/env python3
"""
Fix Remaining Security Violations in Route Files
Target the insecure patterns identified in the security audit
"""

import os
import re

def fix_insecure_patterns():
    """Fix insecure query patterns across route files"""
    
    route_files = [
        'problems/routes.py',
        'business/routes.py', 
        'projects/routes.py',
        'solutions/routes.py',
        'dept/routes.py',
        'notifications/routes.py'
    ]
    
    fixes_applied = {}
    
    for route_file in route_files:
        if not os.path.exists(route_file):
            continue
            
        print(f"\n🔧 Analyzing {route_file}...")
        
        try:
            with open(route_file, 'r') as f:
                content = f.read()
                
            original_content = content
            
            # Fix Pattern 1: Direct .get_or_404() without organization filtering
            # Replace Model.query.get_or_404(id) with organization filtering
            models = ['Problem', 'BusinessCase', 'Project', 'Epic', 'Story', 'Solution', 'Department', 'OrgUnit']
            
            for model in models:
                # Pattern: Model.query.get_or_404(id)
                pattern = rf'{model}\.query\.get_or_404\(([^)]+)\)'
                replacement = rf'{model}.query.filter_by(id=\1, organization_id=current_user.organization_id).first_or_404()'
                content = re.sub(pattern, replacement, content)
                
                # Pattern: Model.query.filter_by(id=id).first_or_404()
                pattern = rf'{model}\.query\.filter_by\(id=([^)]+)\)\.first_or_404\(\)'
                replacement = rf'{model}.query.filter_by(id=\1, organization_id=current_user.organization_id).first_or_404()'
                content = re.sub(pattern, replacement, content)
                
            # Fix Pattern 2: Generic query.get() patterns
            pattern = r'\.query\.get\(([^)]+)\)'
            # This is more complex - would need manual review for each case
            
            # Check if changes were made
            if content != original_content:
                changes = len(re.findall(r'organization_id=current_user\.organization_id', content)) - len(re.findall(r'organization_id=current_user\.organization_id', original_content))
                fixes_applied[route_file] = changes
                print(f"✅ {route_file}: {changes} security fixes applied")
                
                # Write back the fixed content
                with open(route_file, 'w') as f:
                    f.write(content)
            else:
                print(f"ℹ️ {route_file}: No automatic fixes needed")
                
        except Exception as e:
            print(f"❌ Error processing {route_file}: {e}")
            
    return fixes_applied

def verify_user_model_filtering():
    """Verify User model queries are properly filtered by organization_id"""
    print("\n🔍 Verifying User model organization filtering...")
    
    route_files = [
        'admin_working.py',
        'auth/routes.py',
        'dept/routes.py'
    ]
    
    for route_file in route_files:
        if not os.path.exists(route_file):
            continue
            
        try:
            with open(route_file, 'r') as f:
                content = f.read()
                
            # Look for User queries that should be organization-filtered
            user_queries = re.findall(r'User\.query[^.]*(?:\.filter[^(]*\([^)]*\))*', content)
            
            secure_user_queries = len(re.findall(r'User\.query[^.]*filter[^(]*\([^)]*organization_id', content))
            total_user_queries = len(re.findall(r'User\.query', content))
            
            if total_user_queries > 0:
                print(f"📊 {route_file}: {secure_user_queries}/{total_user_queries} User queries have organization filtering")
                
        except Exception as e:
            print(f"❌ Error checking {route_file}: {e}")

def main():
    """Run security fixes"""
    print("🛠️ Starting Security Violation Fixes")
    print("="*60)
    
    fixes = fix_insecure_patterns()
    verify_user_model_filtering()
    
    print("\n" + "="*60)
    print("📊 SECURITY FIX SUMMARY")
    print("="*60)
    
    total_fixes = sum(fixes.values())
    print(f"Total files processed: {len(fixes)}")
    print(f"Total security fixes applied: {total_fixes}")
    
    for file, count in fixes.items():
        print(f"  - {file}: {count} fixes")
        
    if total_fixes > 0:
        print(f"\n✅ {total_fixes} security improvements applied!")
        print("🔄 Restart application to apply changes")
    else:
        print("\n✅ No automatic fixes needed - manual review may be required")
        
    print("\n🎯 NEXT STEPS:")
    print("1. Review any remaining insecure patterns manually")
    print("2. Test application functionality after fixes")
    print("3. Re-run security audit to verify improvements")

if __name__ == "__main__":
    main()