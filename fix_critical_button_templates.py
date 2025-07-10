#!/usr/bin/env python3
"""
Critical Button Template Fix Script
Applies proven Bootstrap Icons + solid button styling to critical admin templates
"""

import os
import re
from pathlib import Path

class CriticalButtonFixer:
    def __init__(self):
        self.fixed_count = 0
        self.templates_fixed = []
        
        # Icon mapping: Font Awesome -> Bootstrap Icons
        self.icon_mapping = {
            'fas fa-edit': 'bi bi-pencil',
            'fa-edit': 'bi-pencil',
            'fas fa-trash': 'bi bi-trash',
            'fa-trash': 'bi-trash',
            'fas fa-plus': 'bi bi-plus-lg',
            'fa-plus': 'bi-plus-lg',
            'fas fa-download': 'bi bi-download',
            'fa-download': 'bi-download',
            'fas fa-upload': 'bi bi-upload',
            'fa-upload': 'bi-upload',
            'fas fa-eye': 'bi bi-eye',
            'fa-eye': 'bi-eye',
            'fas fa-user': 'bi bi-person',
            'fa-user': 'bi-person',
            'fas fa-cog': 'bi bi-gear',
            'fa-cog': 'bi-gear',
            'fas fa-save': 'bi bi-check-lg',
            'fa-save': 'bi-check-lg',
            'fas fa-search': 'bi bi-search',
            'fa-search': 'bi-search',
            'fas fa-times': 'bi bi-x-lg',
            'fa-times': 'bi-x-lg',
            'fas fa-arrow-left': 'bi bi-arrow-left',
            'fa-arrow-left': 'bi-arrow-left'
        }
        
        # Proven styling pattern
        self.button_style = 'style="color: #ffffff !important; font-weight: 600 !important; text-transform: uppercase;"'
        
    def fix_font_awesome_icons(self, content):
        """Replace Font Awesome icons with Bootstrap Icons"""
        for fa_icon, bi_icon in self.icon_mapping.items():
            content = content.replace(f'<i class="{fa_icon}', f'<i class="{bi_icon}')
            content = content.replace(f'"fas {fa_icon.split()[-1]}', f'"bi {bi_icon.split()[-1]}')
            
        return content
        
    def fix_outline_buttons(self, content):
        """Convert problematic outline buttons to solid buttons with proper styling"""
        
        # Pattern 1: btn-outline-secondary -> btn-secondary with styling
        pattern1 = r'(<(?:a|button)[^>]*class="[^"]*btn-outline-secondary[^"]*"[^>]*>)'
        matches1 = re.findall(pattern1, content)
        for match in matches1:
            if 'style=' not in match:
                new_match = match.replace('btn-outline-secondary', 'btn-secondary')
                new_match = new_match.replace('>', f' {self.button_style}>')
                content = content.replace(match, new_match)
                
        # Pattern 2: btn-outline-danger -> btn-danger with styling  
        pattern2 = r'(<(?:a|button)[^>]*class="[^"]*btn-outline-danger[^"]*"[^>]*>)'
        matches2 = re.findall(pattern2, content)
        for match in matches2:
            if 'style=' not in match:
                new_match = match.replace('btn-outline-danger', 'btn-danger')
                new_match = new_match.replace('>', f' {self.button_style}>')
                content = content.replace(match, new_match)
                
        # Pattern 3: btn-outline-primary -> btn-primary with styling
        pattern3 = r'(<(?:a|button)[^>]*class="[^"]*btn-outline-primary[^"]*"[^>]*>)'
        matches3 = re.findall(pattern3, content)
        for match in matches3:
            if 'style=' not in match:
                new_match = match.replace('btn-outline-primary', 'btn-primary')
                new_match = new_match.replace('>', f' {self.button_style}>')
                content = content.replace(match, new_match)
                
        return content
        
    def fix_template(self, template_path):
        """Apply comprehensive button fixes to a template"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
                
            # Apply fixes
            content = self.fix_font_awesome_icons(original_content)
            content = self.fix_outline_buttons(content)
            
            # Only write if changes were made
            if content != original_content:
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.fixed_count += 1
                self.templates_fixed.append(template_path)
                print(f"✅ Fixed: {template_path}")
                return True
            else:
                print(f"⏭️  Skipped: {template_path} (no changes needed)")
                return False
                
        except Exception as e:
            print(f"❌ Error fixing {template_path}: {e}")
            return False
            
    def run_critical_fixes(self):
        """Apply fixes to critical admin templates"""
        critical_templates = [
            'templates/admin/role_permissions.html',
            'templates/admin/workflows.html',
            'templates/admin/dashboard.html',
            'templates/admin/data_export.html',
            'templates/admin/org_structure.html',
            'templates/admin/ai_settings.html',
            'templates/admin/regional_settings.html',
            'templates/admin/reports.html',
            'templates/admin/audit_logs.html',
            'templates/admin/audit_trail.html',
            'templates/admin/system_health.html',
            'templates/admin/data_management/overview.html'
        ]
        
        print("🚀 Starting Critical Button Template Fixes...")
        print("=" * 60)
        
        for template_path in critical_templates:
            if os.path.exists(template_path):
                self.fix_template(template_path)
            else:
                print(f"⚠️  Template not found: {template_path}")
                
        print("=" * 60)
        print(f"✅ Fix Summary: {self.fixed_count} templates updated")
        
        if self.templates_fixed:
            print("\n📝 Templates Fixed:")
            for template in self.templates_fixed:
                print(f"   - {template}")
                
        return self.templates_fixed

def main():
    """Execute critical button template fixes"""
    fixer = CriticalButtonFixer()
    fixed_templates = fixer.run_critical_fixes()
    
    if fixed_templates:
        print(f"\n🎯 SUCCESS: Fixed button visibility in {len(fixed_templates)} critical templates")
        print("\n💡 Applied standardization:")
        print("   - Font Awesome → Bootstrap Icons")  
        print("   - Outline buttons → Solid buttons")
        print("   - Added white text styling with uppercase text")
    else:
        print("\n✅ All critical templates already have proper button styling!")

if __name__ == "__main__":
    main()