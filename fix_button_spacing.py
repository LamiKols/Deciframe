#!/usr/bin/env python3
"""
Button Spacing Fix Script
Fixes button spacing issues in navigation areas where buttons are touching each other
"""

import os
import re

class ButtonSpacingFixer:
    def __init__(self):
        self.fixed_count = 0
        self.templates_fixed = []
        
    def fix_button_spacing(self, content):
        """Fix button spacing issues by adding proper margin/gap classes"""
        
        # Pattern 1: Fix button groups without spacing
        # Look for consecutive buttons in horizontal layouts
        pattern1 = r'(<(?:a|button)[^>]*class="[^"]*btn[^"]*"[^>]*>.*?</(?:a|button)>)\s*(<(?:a|button)[^>]*class="[^"]*btn[^"]*"[^>]*>)'
        
        def add_spacing_class(match):
            first_button = match.group(1)
            second_button = match.group(2)
            
            # Add margin-end to first button if not already present
            if 'me-' not in first_button and 'margin-end' not in first_button:
                # Find the class attribute and add me-2
                class_pattern = r'(class="[^"]*btn[^"]*)"'
                first_button = re.sub(class_pattern, r'\1 me-2"', first_button)
            
            return first_button + ' ' + second_button
        
        content = re.sub(pattern1, add_spacing_class, content, flags=re.DOTALL)
        
        # Pattern 2: Fix div containers with multiple buttons
        # Look for div containers with multiple buttons and ensure they have gap classes
        pattern2 = r'(<div[^>]*class="[^"]*d-flex[^"]*"[^>]*>)'
        
        def add_gap_class(match):
            div_tag = match.group(1)
            if 'gap-' not in div_tag and 'column-gap' not in div_tag:
                # Add gap-2 class for flex containers
                class_pattern = r'(class="[^"]*d-flex[^"]*)"'
                div_tag = re.sub(class_pattern, r'\1 gap-2"', div_tag)
            return div_tag
        
        content = re.sub(pattern2, add_gap_class, content)
        
        # Pattern 3: Fix button groups specifically
        pattern3 = r'(<div[^>]*class="[^"]*btn-group[^"]*"[^>]*>)'
        
        def add_btn_group_spacing(match):
            div_tag = match.group(1)
            if 'gap-' not in div_tag:
                class_pattern = r'(class="[^"]*btn-group[^"]*)"'
                div_tag = re.sub(class_pattern, r'\1 gap-1"', div_tag)
            return div_tag
        
        content = re.sub(pattern3, add_btn_group_spacing, content)
        
        # Pattern 4: Fix nav-tabs or similar navigation with buttons
        pattern4 = r'(<nav[^>]*>.*?</nav>)'
        
        def fix_nav_spacing(match):
            nav_content = match.group(1)
            # Add spacing between nav items
            nav_content = re.sub(
                r'(<(?:a|button)[^>]*class="[^"]*nav-link[^"]*"[^>]*>.*?</(?:a|button)>)\s*(<(?:a|button)[^>]*class="[^"]*nav-link[^"]*")',
                r'\1 \2',
                nav_content,
                flags=re.DOTALL
            )
            return nav_content
        
        content = re.sub(pattern4, fix_nav_spacing, content, flags=re.DOTALL)
        
        return content
        
    def fix_template(self, template_path):
        """Apply spacing fixes to a template"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
                
            # Apply spacing fixes
            content = self.fix_button_spacing(original_content)
            
            # Only write if changes were made
            if content != original_content:
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.fixed_count += 1
                self.templates_fixed.append(template_path)
                print(f"✅ Fixed spacing: {template_path}")
                return True
            else:
                print(f"⏭️  No spacing issues: {template_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error fixing {template_path}: {e}")
            return False
            
    def run_spacing_fixes(self):
        """Apply spacing fixes to admin templates with navigation"""
        templates_to_fix = [
            'templates/admin/dashboard.html',
            'templates/admin/workflows.html',
            'templates/admin/organization_settings.html',
            'templates/admin/data_export.html',
            'templates/admin/users.html',
            'templates/admin/triage_rules.html',
            'templates/admin/help_center.html',
            'templates/admin/role_permissions.html',
            'templates/admin/workflow_configuration.html',
            'templates/notifications/config/settings.html',
            'templates/admin/reports.html',
            'templates/admin/audit_logs.html'
        ]
        
        print("🎯 Starting Button Spacing Fixes...")
        print("=" * 50)
        
        for template_path in templates_to_fix:
            if os.path.exists(template_path):
                self.fix_template(template_path)
            else:
                print(f"⚠️  Template not found: {template_path}")
                
        print("=" * 50)
        print(f"✅ Spacing Fix Summary: {self.fixed_count} templates updated")
        
        if self.templates_fixed:
            print("\n📝 Templates with spacing fixes:")
            for template in self.templates_fixed:
                print(f"   - {template}")
                
        return self.templates_fixed

# Also create a manual fix for the specific navigation structure seen in the image
def create_navigation_spacing_fix():
    """Create a specific fix for the navigation spacing issue"""
    fix_content = """
/* Button Navigation Spacing Fix */
.btn-group .btn {
    margin-right: 8px !important;
}

.btn-group .btn:last-child {
    margin-right: 0 !important;
}

/* Horizontal button navigation spacing */
.d-flex .btn + .btn,
.nav .btn + .btn {
    margin-left: 8px !important;
}

/* Configuration navigation specific fix */
nav .btn {
    margin-right: 8px !important;
}

nav .btn:last-child {
    margin-right: 0 !important;
}

/* Tab-like navigation buttons */
.nav-tabs .nav-link {
    margin-right: 4px !important;
}

/* Admin navigation buttons */
.admin-nav .btn {
    margin-right: 12px !important;
}
"""
    
    with open('static/css/button-spacing-fix.css', 'w') as f:
        f.write(fix_content)
    
    print("📝 Created button spacing CSS fix: static/css/button-spacing-fix.css")

def main():
    """Execute button spacing fixes"""
    fixer = ButtonSpacingFixer()
    fixed_templates = fixer.run_spacing_fixes()
    
    # Also create the CSS fix
    create_navigation_spacing_fix()
    
    if fixed_templates:
        print(f"\n🎯 SUCCESS: Fixed button spacing in {len(fixed_templates)} templates")
        print("\n💡 Applied fixes:")
        print("   - Added me-2 class to consecutive buttons")
        print("   - Added gap-2 class to flex containers")
        print("   - Enhanced btn-group spacing")
        print("   - Created CSS override file")
    else:
        print("\n✅ No spacing issues found in checked templates!")

if __name__ == "__main__":
    main()