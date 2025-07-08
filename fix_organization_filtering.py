"""
Fix organization-based data filtering in all business routes
"""

import re

def fix_business_routes():
    """Add organization filtering to all BusinessCase.query calls in business/routes.py"""
    
    # Read the file
    with open('business/routes.py', 'r') as f:
        content = f.read()
    
    # Replace all BusinessCase.query.get_or_404(id) with organization filtering
    content = re.sub(
        r'BusinessCase\.query\.get_or_404\(id\)',
        'BusinessCase.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()',
        content
    )
    
    # Replace all Problem.query.get_or_404(id) with organization filtering  
    content = re.sub(
        r'Problem\.query\.get_or_404\((\w+)\)',
        r'Problem.query.filter_by(id=\1, organization_id=current_user.organization_id).first_or_404()',
        content
    )
    
    # Add organization filtering to listings
    content = re.sub(
        r'query = BusinessCase\.query',
        'query = BusinessCase.query.filter_by(organization_id=current_user.organization_id)',
        content
    )
    
    # Add organization filtering to Epic queries
    content = re.sub(
        r'Epic\.query\.filter_by\(case_id=id\)',
        'Epic.query.filter_by(case_id=id)',  # Epic inherits org from case
        content
    )
    
    # Write back the fixed content
    with open('business/routes.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed organization filtering in business/routes.py")

def fix_problems_routes():
    """Add organization filtering to problems routes"""
    try:
        with open('problems/routes.py', 'r') as f:
            content = f.read()
        
        # Replace Problem.query.get_or_404 patterns
        content = re.sub(
            r'Problem\.query\.get_or_404\((\w+)\)',
            r'Problem.query.filter_by(id=\1, organization_id=current_user.organization_id).first_or_404()',
            content
        )
        
        # Add organization filtering to listings
        content = re.sub(
            r'query = Problem\.query',
            'query = Problem.query.filter_by(organization_id=current_user.organization_id)',
            content
        )
        
        with open('problems/routes.py', 'w') as f:
            f.write(content)
        
        print("✅ Fixed organization filtering in problems/routes.py")
    except FileNotFoundError:
        print("⚠️ problems/routes.py not found")

def fix_projects_routes():
    """Add organization filtering to projects routes"""
    try:
        with open('projects/routes.py', 'r') as f:
            content = f.read()
        
        # Replace Project.query.get_or_404 patterns
        content = re.sub(
            r'Project\.query\.get_or_404\((\w+)\)',
            r'Project.query.filter_by(id=\1, organization_id=current_user.organization_id).first_or_404()',
            content
        )
        
        # Add organization filtering to listings
        content = re.sub(
            r'query = Project\.query',
            'query = Project.query.filter_by(organization_id=current_user.organization_id)',
            content
        )
        
        with open('projects/routes.py', 'w') as f:
            f.write(content)
        
        print("✅ Fixed organization filtering in projects/routes.py")
    except FileNotFoundError:
        print("⚠️ projects/routes.py not found")

def add_organization_id_to_creation():
    """Add organization_id to Problem and Project creation routes"""
    
    # Fix Problems creation
    try:
        with open('problems/routes.py', 'r') as f:
            content = f.read()
        
        # Add organization_id to Problem creation
        if 'organization_id=current_user.organization_id' not in content:
            content = re.sub(
                r'(Problem\([^)]*created_by=current_user\.id)',
                r'\1, organization_id=current_user.organization_id',
                content
            )
        
        with open('problems/routes.py', 'w') as f:
            f.write(content)
        
        print("✅ Added organization_id to Problem creation")
    except FileNotFoundError:
        print("⚠️ problems/routes.py not found")
    
    # Fix Projects creation
    try:
        with open('projects/routes.py', 'r') as f:
            content = f.read()
        
        # Add organization_id to Project creation
        if 'organization_id=current_user.organization_id' not in content:
            content = re.sub(
                r'(Project\([^)]*created_by=current_user\.id)',
                r'\1, organization_id=current_user.organization_id',
                content
            )
        
        with open('projects/routes.py', 'w') as f:
            f.write(content)
        
        print("✅ Added organization_id to Project creation")
    except FileNotFoundError:
        print("⚠️ projects/routes.py not found")

if __name__ == "__main__":
    print("🔒 Fixing organization-based data filtering...")
    fix_business_routes()
    fix_problems_routes()
    fix_projects_routes()
    add_organization_id_to_creation()
    print("🔒 CRITICAL SECURITY FIX COMPLETE: Organization data isolation implemented")