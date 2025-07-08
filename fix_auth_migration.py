#!/usr/bin/env python3
"""
Script to complete JWT to session-based authentication migration
Replaces all @require_auth, get_current_user(), and redirect_with_auth() references
"""

import os
import re

def replace_auth_patterns(file_path):
    """Replace JWT authentication patterns with session-based equivalents"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original = content
    
    # Replace @require_auth with @login_required
    content = re.sub(r'@require_auth', '@login_required', content)
    
    # Replace get_current_user() with current_user
    content = re.sub(r'get_current_user\(\)', 'current_user', content)
    
    # Replace redirect_with_auth with redirect(url_for(...))
    content = re.sub(r"redirect_with_auth\('([^']+)'\)", r"redirect(url_for('\1'))", content)
    content = re.sub(r"redirect_with_auth\('([^']+)',\s*([^)]+)\)", r"redirect(url_for('\1', \2))", content)
    
    # Update user assignments
    content = re.sub(r'user = get_current_user\(\)', 'user = current_user', content)
    
    if content != original:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Updated {file_path}")
        return True
    return False

def main():
    """Process all Python files that need authentication migration"""
    files_to_process = [
        'business/routes.py',
        'projects/routes.py', 
        'dashboard/routes.py',
        'ai/routes.py',
        'ai/summary_routes.py',
        'solutions/routes.py',
        'admin_working.py'
    ]
    
    updated_count = 0
    for file_path in files_to_process:
        if os.path.exists(file_path):
            if replace_auth_patterns(file_path):
                updated_count += 1
        else:
            print(f"File not found: {file_path}")
    
    print(f"Authentication migration completed. Updated {updated_count} files.")

if __name__ == "__main__":
    main()