#!/usr/bin/env python3
"""
Fix duplicate organization_id parameters in queries
"""

import re
import os

def fix_duplicate_org_id_in_file(file_path):
    """Fix duplicate organization_id parameters in a file"""
    if not os.path.exists(file_path):
        return 0
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        fixes = 0
        
        # Pattern to find duplicate organization_id parameters
        pattern = r'(\.filter_by\([^)]*organization_id=current_user\.organization_id[^)]*), organization_id=current_user\.organization_id([^)]*\))'
        
        def fix_match(match):
            nonlocal fixes
            fixes += 1
            # Remove the duplicate organization_id parameter
            return match.group(1) + match.group(2)
        
        content = re.sub(pattern, fix_match, content)
        
        # Also fix cases where organization_id appears multiple times in the same filter_by
        pattern2 = r'(organization_id=current_user\.organization_id[^,)]*),\s*organization_id=current_user\.organization_id'
        content = re.sub(pattern2, r'\1', content)
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Fixed {fixes} duplicate organization_id issues in {file_path}")
            return fixes
        else:
            return 0
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return 0

def main():
    """Fix all files with duplicate organization_id issues"""
    files_to_fix = [
        'admin_working.py',
        'business/routes.py', 
        'problems/routes.py',
        'projects/routes.py',
        'solutions/routes.py',
        'dept/routes.py',
        'dashboards/routes.py',
        'reports/routes.py',
        'notifications/routes.py',
        'predict/routes.py'
    ]
    
    total_fixes = 0
    for file_path in files_to_fix:
        fixes = fix_duplicate_org_id_in_file(file_path)
        total_fixes += fixes
    
    print(f"\n🎉 Fixed {total_fixes} duplicate organization_id issues across all files")

if __name__ == "__main__":
    main()