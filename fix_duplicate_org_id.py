#!/usr/bin/env python3
"""
Fix duplicate organization_id parameters created by automatic security fixes
"""

import os
import re

def fix_duplicate_org_id():
    """Fix duplicate organization_id parameters in route files"""
    
    route_files = [
        'business/routes.py',
        'projects/routes.py', 
        'solutions/routes.py',
        'dept/routes.py'
    ]
    
    fixes_applied = {}
    
    for route_file in route_files:
        if not os.path.exists(route_file):
            continue
            
        print(f"🔧 Fixing {route_file}...")
        
        try:
            with open(route_file, 'r') as f:
                content = f.read()
                
            original_content = content
            
            # Fix the duplicate organization_id pattern
            pattern = r'organization_id=current_user\.organization_id, organization_id=current_user\.organization_id'
            replacement = r'organization_id=current_user.organization_id'
            
            content = re.sub(pattern, replacement, content)
            
            # Count fixes
            fixes_count = len(re.findall(pattern, original_content))
            
            if content != original_content:
                fixes_applied[route_file] = fixes_count
                print(f"✅ {route_file}: {fixes_count} duplicate parameters fixed")
                
                # Write back the fixed content
                with open(route_file, 'w') as f:
                    f.write(content)
            else:
                print(f"ℹ️ {route_file}: No duplicates found")
                
        except Exception as e:
            print(f"❌ Error processing {route_file}: {e}")
            
    return fixes_applied

def main():
    """Run duplicate organization_id fixes"""
    print("🛠️ Fixing Duplicate organization_id Parameters")
    print("="*60)
    
    fixes = fix_duplicate_org_id()
    
    print("\n" + "="*60)
    print("📊 DUPLICATE FIX SUMMARY")
    print("="*60)
    
    total_fixes = sum(fixes.values())
    print(f"Total files processed: {len(fixes)}")
    print(f"Total duplicate parameters fixed: {total_fixes}")
    
    for file, count in fixes.items():
        print(f"  - {file}: {count} fixes")
        
    if total_fixes > 0:
        print(f"\n✅ {total_fixes} duplicate parameters fixed!")
        print("🔄 Application ready to restart")
    else:
        print("\n✅ No duplicate parameters found")

if __name__ == "__main__":
    main()