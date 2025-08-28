#!/usr/bin/env python3
"""
Comprehensive Button Visibility Audit & Fix Script
Identifies and reports button visibility issues across the application
"""

import re
from pathlib import Path

class ButtonVisibilityAuditor:
    def __init__(self):
        self.templates_dir = Path("templates")
        self.issues_found = []
        self.critical_templates = []
        self.fixed_templates = []
        
    def audit_template(self, template_path):
        """Audit a single template for button visibility issues"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            issues = []
            
            # Check for Font Awesome + outline button combinations (high risk)
            fa_outline_pattern = r'btn-outline-[a-z]+.*?fas?\s+fa-[a-z-]+'
            fa_outline_matches = re.findall(fa_outline_pattern, content, re.DOTALL | re.IGNORECASE)
            if fa_outline_matches:
                issues.append(f"Font Awesome + outline button combination found: {len(fa_outline_matches)} instances")
                
            # Check for outline buttons without explicit text styling
            outline_pattern = r'<button[^>]*btn-outline-[^>]*>.*?</button>'
            outline_matches = re.findall(outline_pattern, content, re.DOTALL | re.IGNORECASE)
            unstyled_outline = [m for m in outline_matches if 'color:' not in m and 'style=' not in m]
            if unstyled_outline:
                issues.append(f"Unstyled outline buttons found: {len(unstyled_outline)} instances")
                
            # Check for Font Awesome icons without Bootstrap Icons alternative
            fa_icons = re.findall(r'fas?\s+fa-([a-z-]+)', content, re.IGNORECASE)
            if fa_icons:
                common_fa_icons = ['edit', 'trash', 'plus', 'download', 'upload', 'eye', 'cog', 'user']
                problematic_icons = [icon for icon in fa_icons if icon in common_fa_icons]
                if problematic_icons:
                    issues.append(f"Font Awesome icons that should be Bootstrap Icons: {set(problematic_icons)}")
                    
            if issues:
                priority = self.calculate_priority(template_path, issues)
                self.issues_found.append({
                    'template': template_path,
                    'priority': priority,
                    'issues': issues
                })
                
                if priority == 'critical':
                    self.critical_templates.append(template_path)
                    
        except Exception as e:
            print(f"Error auditing {template_path}: {e}")
            
    def calculate_priority(self, template_path, issues):
        """Calculate priority level based on template location and issue types"""
        path_str = str(template_path)
        
        # Critical: Admin interfaces with button visibility issues
        if '/admin/' in path_str and any('Font Awesome + outline' in issue for issue in issues):
            return 'critical'
            
        # High: Any admin interface with styling issues
        if '/admin/' in path_str:
            return 'high'
            
        # Medium: Non-admin interfaces with Font Awesome + outline issues
        if any('Font Awesome + outline' in issue for issue in issues):
            return 'medium'
            
        return 'low'
    
    def run_audit(self):
        """Run comprehensive audit across all templates"""
        print("🔍 Starting Comprehensive Button Visibility Audit...")
        
        for template_file in self.templates_dir.rglob("*.html"):
            self.audit_template(template_file)
            
        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        self.issues_found.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        self.generate_report()
        
    def generate_report(self):
        """Generate comprehensive audit report"""
        print("\n" + "="*80)
        print("BUTTON VISIBILITY AUDIT REPORT")
        print("="*80)
        
        if not self.issues_found:
            print("✅ No button visibility issues found!")
            return
            
        print(f"📊 Total templates with issues: {len(self.issues_found)}")
        print(f"🚨 Critical templates: {len([i for i in self.issues_found if i['priority'] == 'critical'])}")
        print(f"⚠️  High priority templates: {len([i for i in self.issues_found if i['priority'] == 'high'])}")
        
        print("\n🚨 CRITICAL ISSUES (Immediate Fix Required):")
        for issue in [i for i in self.issues_found if i['priority'] == 'critical']:
            print(f"  📁 {issue['template']}")
            for problem in issue['issues']:
                print(f"    - {problem}")
                
        print("\n⚠️  HIGH PRIORITY ISSUES:")
        for issue in [i for i in self.issues_found if i['priority'] == 'high']:
            print(f"  📁 {issue['template']}")
            for problem in issue['issues']:
                print(f"    - {problem}")
                
        print("\n💡 RECOMMENDED FIXES:")
        print("1. Replace Font Awesome icons with Bootstrap Icons:")
        print("   fa-edit → bi-pencil")
        print("   fa-trash → bi-trash") 
        print("   fa-plus → bi-plus-lg")
        print("   fa-eye → bi-eye")
        print("   fa-download → bi-download")
        
        print("\n2. Convert outline buttons to solid buttons with inline styling:")
        print("   btn-outline-secondary → btn-primary with style='color: #ffffff !important;'")
        print("   btn-outline-danger → btn-danger with style='color: #ffffff !important;'")
        
        print("\n3. Apply proven styling pattern:")
        print("   style='color: #ffffff !important; font-weight: 600 !important; text-transform: uppercase;'")
        
        return self.critical_templates

def main():
    """Execute button visibility audit"""
    auditor = ButtonVisibilityAuditor()
    critical_templates = auditor.run_audit()
    
    if critical_templates:
        print(f"\n🎯 RECOMMENDED ACTION: Fix {len(critical_templates)} critical templates first")
        return critical_templates
    else:
        print("\n✅ No critical issues found. Application button visibility is healthy!")
        return []

if __name__ == "__main__":
    main()