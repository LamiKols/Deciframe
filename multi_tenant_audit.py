#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE MULTI-TENANT SECURITY AUDIT & ENFORCEMENT
Verify and enforce proper organization-level data isolation across all models and routes
"""

import os
import re
from typing import List, Dict

class MultiTenantAuditor:
    """
    Comprehensive multi-tenant security auditor for DeciFrame
    Scans models and routes to ensure proper organization-level isolation
    """
    
    def __init__(self):
        self.models_with_org_id = set()
        self.models_missing_org_id = set()
        self.routes_with_org_filtering = set()
        self.routes_missing_org_filtering = set()
        self.security_violations = []
        
        # Models that should NOT have organization_id (system-level models)
        self.system_models = {
            'Organization', 'User', 'Setting', 'RolePermission', 
            'AuditLog', 'ImportJob', 'ExportJob', 'RetentionLog',
            'DataRetentionPolicy', 'Waitlist'
        }
        
        # Core business models that MUST have organization_id
        self.business_models = {
            'Problem', 'BusinessCase', 'Project', 'Epic', 'Story',
            'ProjectMilestone', 'Solution', 'NotificationTemplate',
            'Notification', 'BusinessCaseComment', 'ProjectComment',
            'EpicComment', 'ReportTemplate', 'ReportRun',
            'RequirementsBackup', 'PredictionFeedback', 'OrgUnit',
            'Department', 'WorkflowTemplate', 'WorkflowLibrary',
            'Task', 'ScheduledTask', 'WorkflowExecution', 'HelpCategory',
            'HelpArticle', 'NotificationSetting', 'ArchivedProblem',
            'ArchivedBusinessCase', 'ArchivedProject', 'TriageRule',
            'OrganizationSettings', 'AIThresholdSettings', 'EpicSyncLog'
        }
    
    def scan_models(self) -> Dict[str, any]:
        """Scan models.py for organization_id fields"""
        print("🔍 Scanning models.py for organization_id fields...")
        
        try:
            with open('models.py', 'r') as f:
                content = f.read()
            
            # Find all class definitions
            class_pattern = re.compile(r'class\s+(\w+)\s*\([^)]*db\.Model[^)]*\):')
            classes = class_pattern.findall(content)
            
            # Check each class for organization_id field
            for class_name in classes:
                if class_name in self.system_models:
                    continue  # Skip system models
                
                # Check if class has organization_id field
                class_content = self._extract_class_content(content, class_name)
                has_org_id = 'organization_id' in class_content
                
                if has_org_id:
                    self.models_with_org_id.add(class_name)
                else:
                    self.models_missing_org_id.add(class_name)
                    if class_name in self.business_models:
                        self.security_violations.append(f"❌ CRITICAL: {class_name} missing organization_id field")
            
            return {
                'models_with_org_id': self.models_with_org_id,
                'models_missing_org_id': self.models_missing_org_id,
                'total_models': len(classes)
            }
            
        except Exception as e:
            print(f"❌ Error scanning models: {e}")
            return {}
    
    def scan_routes(self) -> Dict[str, any]:
        """Scan all route files for organization filtering"""
        print("🔍 Scanning route files for organization filtering...")
        
        route_files = [
            'problems/routes.py', 'business/routes.py', 'projects/routes.py',
            'solutions/routes.py', 'dept/routes.py', 'dashboards/routes.py',
            'reports/routes.py', 'notifications/routes.py', 'admin_working.py',
            'auth/routes.py', 'predict/routes.py'
        ]
        
        for file_path in route_files:
            if os.path.exists(file_path):
                self._scan_route_file(file_path)
        
        return {
            'routes_with_filtering': self.routes_with_org_filtering,
            'routes_missing_filtering': self.routes_missing_org_filtering,
            'security_violations': len(self.security_violations)
        }
    
    def _scan_route_file(self, file_path: str):
        """Scan individual route file for security issues"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Find queries that might need organization filtering
            dangerous_patterns = [
                r'\.query\.get\(',
                r'\.query\.get_or_404\(',
                r'\.query\.filter\(',
                r'\.query\.filter_by\(',
                r'\.query\.all\(\)',
                r'\.query\.first\(\)',
            ]
            
            # Find model imports
            model_imports = re.findall(r'from models import.*?(\w+)', content)
            
            violations = []
            for pattern in dangerous_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = content.split('\n')[line_num - 1].strip()
                    
                    # Check if this query has organization filtering
                    if 'organization_id' not in line_content and 'current_user.organization_id' not in line_content:
                        # Check if it's a business model query
                        for model in self.business_models:
                            if model in line_content:
                                violations.append(f"Line {line_num}: {line_content[:100]}")
                                self.security_violations.append(
                                    f"⚠️ {file_path}:{line_num} - Query without org filtering: {model}"
                                )
                                break
            
            if violations:
                self.routes_missing_org_filtering.add(file_path)
            else:
                self.routes_with_org_filtering.add(file_path)
                
        except Exception as e:
            print(f"❌ Error scanning {file_path}: {e}")
    
    def _extract_class_content(self, content: str, class_name: str) -> str:
        """Extract the content of a specific class"""
        pattern = rf'class\s+{class_name}\s*\([^)]*\):(.*?)(?=\nclass\s|\nif\s|$)'
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1) if match else ""
    
    def generate_enforcement_decorator(self) -> str:
        """Generate the organization enforcement decorator"""
        return """
# 🔒 MULTI-TENANT SECURITY DECORATOR
from functools import wraps
from flask import abort, request
from flask_login import current_user

def require_same_org(get_record_func=None):
    \"\"\"
    Decorator to enforce organization-level access control
    Usage:
        @require_same_org(lambda id: Problem.query.get_or_404(id))
        def view_problem(id):
            # This will automatically check org access
    \"\"\"
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Extract record ID from kwargs or args
            record_id = kwargs.get('id') or (args[0] if args else None)
            
            if get_record_func and record_id:
                try:
                    record = get_record_func(record_id)
                    if hasattr(record, 'organization_id'):
                        if record.organization_id != current_user.organization_id:
                            abort(403, "Access denied: Resource belongs to different organization")
                except Exception:
                    abort(404)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

def enforce_org_filter(query_class):
    \"\"\"
    Helper to automatically add organization filtering to queries
    Usage: Problem.query becomes enforce_org_filter(Problem).query
    \"\"\"
    if hasattr(current_user, 'organization_id') and current_user.is_authenticated:
        return query_class.query.filter_by(organization_id=current_user.organization_id)
    return query_class.query
"""
    
    def create_security_patches(self) -> List[str]:
        """Generate patches for security violations"""
        patches = []
        
        # Generate model patches for missing organization_id
        for model in self.models_missing_org_id:
            if model in self.business_models:
                patches.append(f"""
# Add organization_id to {model} model in models.py:
# In class {model}(db.Model):
#     organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
#     organization = db.relationship('Organization', foreign_keys=[organization_id])
""")
        
        # Generate route patches
        for violation in self.security_violations:
            if "Query without org filtering" in violation:
                patches.append(f"# Fix: {violation}")
        
        return patches
    
    def generate_audit_report(self) -> str:
        """Generate comprehensive audit report"""
        report = f"""
# 🔍 MULTI-TENANT SECURITY AUDIT REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 AUDIT SUMMARY
- Total Models Scanned: {len(self.models_with_org_id) + len(self.models_missing_org_id)}
- Models with Organization ID: {len(self.models_with_org_id)}
- Models Missing Organization ID: {len(self.models_missing_org_id)}
- Route Files Scanned: {len(self.routes_with_org_filtering) + len(self.routes_missing_org_filtering)}
- Security Violations Found: {len(self.security_violations)}

## ✅ MODELS WITH PROPER ORG ENFORCEMENT
{chr(10).join(f'- ✅ {model}' for model in sorted(self.models_with_org_id))}

## ❌ MODELS MISSING ORGANIZATION_ID
{chr(10).join(f'- ❌ {model}' for model in sorted(self.models_missing_org_id))}

## ⚠️ SECURITY VIOLATIONS
{chr(10).join(f'- {violation}' for violation in self.security_violations)}

## 🔒 ROUTES STATUS
### Properly Filtered Routes:
{chr(10).join(f'- ✅ {route}' for route in sorted(self.routes_with_org_filtering))}

### Routes Needing Review:
{chr(10).join(f'- ⚠️ {route}' for route in sorted(self.routes_missing_org_filtering))}

## 🚨 CRITICAL RECOMMENDATIONS
1. Add organization_id fields to all business models
2. Implement @require_same_org decorator on sensitive routes
3. Add organization filtering to all business model queries
4. Create 403 error page for unauthorized access attempts
5. Add automated tests for multi-tenant security

## 🔧 NEXT STEPS
1. Run database migration to add missing organization_id fields
2. Update all route queries to include organization filtering
3. Deploy organization enforcement decorator
4. Add security tests to prevent regressions
"""
        return report

# Main execution
if __name__ == "__main__":
    from datetime import datetime
    
    print("🔍 Starting Multi-Tenant Security Audit...")
    auditor = MultiTenantAuditor()
    
    # Scan models and routes
    model_results = auditor.scan_models()
    route_results = auditor.scan_routes()
    
    # Generate report
    report = auditor.generate_audit_report()
    
    # Save report
    with open('multi_tenant_security_audit.md', 'w') as f:
        f.write(report)
    
    # Generate enforcement decorator
    decorator_code = auditor.generate_enforcement_decorator()
    with open('utils/security.py', 'w') as f:
        f.write(decorator_code)
    
    print("✅ Audit complete! Check multi_tenant_security_audit.md for results")
    print("✅ Security decorator created at utils/security.py")
    
    # Print summary
    print("\n📊 QUICK SUMMARY:")
    print(f"✅ Models with org_id: {len(auditor.models_with_org_id)}")
    print(f"❌ Models missing org_id: {len(auditor.models_missing_org_id)}")
    print(f"⚠️ Security violations: {len(auditor.security_violations)}")
    
    if auditor.security_violations:
        print("\n🚨 TOP SECURITY ISSUES:")
        for violation in auditor.security_violations[:5]:
            print(f"  {violation}")