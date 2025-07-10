#!/usr/bin/env python3
"""
Button Content Optimization Script
Removes descriptions from button texts to make them smaller and more professional
Changes "TITLE & DESCRIPTION" to just "TITLE"
"""

import os
import re
from pathlib import Path

class ButtonContentOptimizer:
    def __init__(self):
        self.fixed_count = 0
        self.templates_fixed = []
        self.button_fixes = {
            # Common button content patterns to shorten
            "ORGANIZATION SETTINGS & PREFERENCES": "ORGANIZATION SETTINGS",
            "NOTIFICATIONS EVENT & CONFIGURATION": "NOTIFICATIONS",
            "PERMISSIONS ROLE & MANAGEMENT": "PERMISSIONS", 
            "WORKFLOWS TEMPLATE & MANAGEMENT": "WORKFLOWS",
            "USER MANAGEMENT & ROLES": "USER MANAGEMENT",
            "DATA EXPORT & IMPORT": "DATA EXPORT",
            "SYSTEM MONITORING & HEALTH": "SYSTEM MONITORING",
            "HELP CENTER & DOCUMENTATION": "HELP CENTER",
            "AUDIT LOGS & SECURITY": "AUDIT LOGS",
            "REPORTS & ANALYTICS": "REPORTS",
            "TRIAGE RULES & AUTOMATION": "TRIAGE RULES",
            "ROLE PERMISSIONS & ACCESS": "ROLE PERMISSIONS",
            
            # Specific patterns for different templates
            "Organization Settings & Preferences": "Organization Settings",
            "Notifications & Configuration": "Notifications",
            "Permissions & Management": "Permissions",
            "Workflows & Templates": "Workflows",
            "User Management & Roles": "User Management",
            "Data Export & Import": "Data Export",
            "System Health & Monitoring": "System Health",
            "Help & Documentation": "Help Center",
            "Audit & Security": "Audit Logs",
            "Reports & Analytics": "Reports",
            "Triage & Automation": "Triage Rules",
            
            # Button text patterns
            "Settings & Preferences": "Settings",
            "Management & Control": "Management",
            "Configuration & Setup": "Configuration",
            "Monitoring & Health": "Monitoring",
            "Security & Audit": "Security",
            "Import & Export": "Data Management",
            "Rules & Automation": "Rules",
            "Access & Permissions": "Access Control"
        }
        
    def optimize_button_content(self, content):
        """Optimize button content by removing descriptions"""
        
        # Apply all button text replacements
        for long_text, short_text in self.button_fixes.items():
            # Case insensitive replacement for button contents
            content = re.sub(
                re.escape(long_text), 
                short_text, 
                content, 
                flags=re.IGNORECASE
            )
            
        # Pattern-based replacements for common button structures
        # Remove " & Description" patterns
        content = re.sub(
            r'(\w+)\s*&\s*[\w\s]+(?=</)',
            r'\1',
            content
        )
        
        # Shorten verbose button texts in nav structures
        content = re.sub(
            r'(>[\s]*)([\w\s]+)\s*&\s*([\w\s]+)([\s]*</)',
            r'\1\2\4',
            content
        )
        
        return content
        
    def fix_template(self, template_path):
        """Apply content optimization to a template"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
                
            # Apply content optimization
            content = self.optimize_button_content(original_content)
            
            # Only write if changes were made
            if content != original_content:
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.fixed_count += 1
                self.templates_fixed.append(template_path)
                print(f"✅ Optimized content: {template_path}")
                return True
            else:
                print(f"⏭️  No content changes needed: {template_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error optimizing {template_path}: {e}")
            return False
            
    def run_content_optimization(self):
        """Apply content optimization to admin templates"""
        templates_to_optimize = [
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
            'templates/admin/audit_logs.html',
            'templates/admin/settings.html',
            'templates/admin/system_health.html',
            'templates/admin/ai_settings.html',
            'templates/admin/regional_settings.html'
        ]
        
        print("🎯 Starting Button Content Optimization...")
        print("=" * 50)
        
        for template_path in templates_to_optimize:
            if os.path.exists(template_path):
                self.fix_template(template_path)
            else:
                print(f"⚠️  Template not found: {template_path}")
                
        print("=" * 50)
        print(f"✅ Content Optimization Summary: {self.fixed_count} templates updated")
        
        if self.templates_fixed:
            print("\n📝 Templates with content optimization:")
            for template in self.templates_fixed:
                print(f"   - {template}")
                
        return self.templates_fixed

def main():
    """Execute button content optimization"""
    optimizer = ButtonContentOptimizer()
    fixed_templates = optimizer.run_content_optimization()
    
    if fixed_templates:
        print(f"\n🎯 SUCCESS: Optimized button content in {len(fixed_templates)} templates")
        print("\n💡 Changes applied:")
        print("   - Removed descriptions from button texts")
        print("   - Shortened verbose button labels")
        print("   - Made buttons more concise and professional")
        print("   - Improved button sizing and layout")
    else:
        print("\n✅ No button content optimization needed!")

if __name__ == "__main__":
    main()