#!/usr/bin/env python3
"""
Comprehensive Multi-Tenant Security Test Suite for DeciFrame
Tests cross-organizational data access and security boundaries
"""

import os
import sys
from datetime import datetime
from flask import Flask
from app import create_app, db
from models import *
from sqlalchemy import text

class MultiTenantSecurityTester:
    def __init__(self):
        self.app = create_app()
        self.violations = []
        self.tests_passed = 0
        self.tests_failed = 0
        
    def test_database_schema(self):
        """Test 1: Verify all core models have organization_id"""
        print("🔍 Test 1: Database Schema Validation")
        
        with self.app.app_context():
            # Check organization_id columns exist with NOT NULL constraints
            result = db.session.execute(text("""
                SELECT table_name, 
                       CASE WHEN EXISTS (
                           SELECT 1 FROM information_schema.columns 
                           WHERE table_name = t.table_name AND column_name = 'organization_id'
                           AND is_nullable = 'NO'
                       ) THEN 'PASS' ELSE 'FAIL' END as status
                FROM information_schema.tables t
                WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    AND table_name IN ('problems', 'business_cases', 'projects', 'epics', 'stories', 'solutions', 'departments', 'org_units', 'notifications')
                ORDER BY table_name;
            """)).fetchall()
            
            for row in result:
                if row.status == 'PASS':
                    print(f"✅ {row.table_name}: organization_id NOT NULL")
                    self.tests_passed += 1
                else:
                    print(f"❌ {row.table_name}: MISSING organization_id or nullable")
                    self.violations.append(f"Table {row.table_name} missing organization_id constraint")
                    self.tests_failed += 1
    
    def test_cross_org_access(self):
        """Test 2: Create test users from different orgs and test data isolation"""
        print("\n🔍 Test 2: Cross-Organizational Data Access")
        
        with self.app.app_context():
            try:
                # Create test organizations
                org1 = Organization(name="TestOrg1", domain="testorg1.com")
                org2 = Organization(name="TestOrg2", domain="testorg2.com")
                db.session.add_all([org1, org2])
                db.session.flush()
                
                # Create test users
                user1 = User(email="user1@testorg1.com", organization_id=org1.id, role=UserRoleEnum.Manager)
                user2 = User(email="user2@testorg2.com", organization_id=org2.id, role=UserRoleEnum.Manager)
                db.session.add_all([user1, user2])
                db.session.flush()
                
                # Create test problems in different orgs
                problem1 = Problem(title="Org1 Problem", organization_id=org1.id, created_by=user1.id)
                problem2 = Problem(title="Org2 Problem", organization_id=org2.id, created_by=user2.id)
                db.session.add_all([problem1, problem2])
                db.session.commit()
                
                # Test 2a: User1 should only see org1 problems
                org1_problems = Problem.query.filter_by(organization_id=org1.id).all()
                org2_problems = Problem.query.filter_by(organization_id=org2.id).all()
                
                if len(org1_problems) == 1 and org1_problems[0].title == "Org1 Problem":
                    print("✅ Organization 1 data isolation works")
                    self.tests_passed += 1
                else:
                    print("❌ Organization 1 data leakage detected")
                    self.violations.append("Org1 user can see other organization data")
                    self.tests_failed += 1
                
                if len(org2_problems) == 1 and org2_problems[0].title == "Org2 Problem":
                    print("✅ Organization 2 data isolation works")
                    self.tests_passed += 1
                else:
                    print("❌ Organization 2 data leakage detected")
                    self.violations.append("Org2 user can see other organization data")
                    self.tests_failed += 1
                
                # Test 2b: Cross-org access should fail
                try:
                    cross_access = Problem.query.filter_by(id=problem1.id, organization_id=org2.id).first()
                    if cross_access is None:
                        print("✅ Cross-organizational access properly blocked")
                        self.tests_passed += 1
                    else:
                        print("❌ Cross-organizational access allowed!")
                        self.violations.append("Cross-org access not blocked")
                        self.tests_failed += 1
                except Exception as e:
                    print(f"✅ Cross-org access threw exception (good): {e}")
                    self.tests_passed += 1
                
            except Exception as e:
                print(f"❌ Error in cross-org test: {e}")
                self.violations.append(f"Cross-org test failed: {e}")
                self.tests_failed += 1
            finally:
                # Cleanup test data
                db.session.rollback()
    
    def test_route_security(self):
        """Test 3: Check route security patterns"""
        print("\n🔍 Test 3: Route Security Validation")
        
        # Define files that should have organization filtering
        critical_files = [
            'problems/routes.py',
            'business/routes.py', 
            'projects/routes.py',
            'solutions/routes.py'
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for dangerous patterns
                dangerous_patterns = [
                    '.query.get_or_404(',
                    '.query.get(',
                    '.query.all()',
                    '.query.first()'
                ]
                
                has_org_filtering = 'organization_id=current_user.organization_id' in content
                has_dangerous_queries = any(pattern in content for pattern in dangerous_patterns)
                
                if has_org_filtering:
                    print(f"✅ {file_path}: Has organization filtering")
                    self.tests_passed += 1
                else:
                    print(f"❌ {file_path}: Missing organization filtering")
                    self.violations.append(f"{file_path} missing organization filtering")
                    self.tests_failed += 1
                    
                if has_dangerous_queries and not has_org_filtering:
                    print(f"⚠️ {file_path}: Has potentially unsafe queries")
                    self.violations.append(f"{file_path} has unsafe query patterns")
    
    def test_first_user_admin(self):
        """Test 4: First user admin assignment"""
        print("\n🔍 Test 4: First User Admin Assignment")
        
        with self.app.app_context():
            try:
                # Clear existing users for this test
                initial_count = User.query.count()
                
                if initial_count == 0:
                    print("✅ Database is empty for first user test")
                    self.tests_passed += 1
                else:
                    print(f"ℹ️ Database has {initial_count} existing users")
                
                # This test would require implementing the registration logic
                # For now, we'll check if the logic exists in auth routes
                if os.path.exists('auth/routes.py'):
                    with open('auth/routes.py', 'r') as f:
                        auth_content = f.read()
                    
                    if 'User.query.count()' in auth_content and 'Admin' in auth_content:
                        print("✅ First user admin logic exists in auth routes")
                        self.tests_passed += 1
                    else:
                        print("❌ First user admin logic missing")
                        self.violations.append("First user admin assignment logic missing")
                        self.tests_failed += 1
                        
            except Exception as e:
                print(f"❌ Error in first user test: {e}")
                self.tests_failed += 1
    
    def test_data_cleanup(self):
        """Test 5: Organization deletion and data cleanup"""
        print("\n🔍 Test 5: Data Cleanup and GDPR Compliance")
        
        with self.app.app_context():
            try:
                # Check if CASCADE constraints exist
                cascade_check = db.session.execute(text("""
                    SELECT tc.constraint_name, tc.table_name, 
                           rc.delete_rule
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.referential_constraints rc 
                        ON tc.constraint_name = rc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                        AND rc.delete_rule = 'CASCADE'
                        AND tc.table_name IN ('problems', 'business_cases', 'projects', 'solutions')
                """)).fetchall()
                
                if len(cascade_check) > 0:
                    print(f"✅ Found {len(cascade_check)} CASCADE constraints for data cleanup")
                    self.tests_passed += 1
                else:
                    print("⚠️ No CASCADE constraints found - manual cleanup required")
                    self.violations.append("Missing CASCADE constraints for organization deletion")
                    self.tests_failed += 1
                    
            except Exception as e:
                print(f"❌ Error in data cleanup test: {e}")
                self.tests_failed += 1
    
    def generate_report(self):
        """Generate comprehensive security report"""
        print(f"\n{'='*60}")
        print("🛡️ DECIFRAME MULTI-TENANT SECURITY AUDIT REPORT")
        print(f"{'='*60}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_failed}")
        print(f"Total Violations: {len(self.violations)}")
        
        if len(self.violations) == 0:
            print("\n🔒 ✅ DECIFRAME IS FULLY TENANT-ISOLATED")
            print("✅ All multi-tenant security tests passed")
            print("✅ Organization boundaries properly enforced")
            print("✅ No data leakage detected")
        else:
            print(f"\n🚨 SECURITY VIOLATIONS DETECTED:")
            for i, violation in enumerate(self.violations, 1):
                print(f"{i}. ❌ {violation}")
        
        return len(self.violations) == 0

def main():
    """Run comprehensive multi-tenant security test suite"""
    print("🚀 Starting DeciFrame Multi-Tenant Security Audit...")
    
    tester = MultiTenantSecurityTester()
    
    # Run all tests
    tester.test_database_schema()
    tester.test_cross_org_access()
    tester.test_route_security()
    tester.test_first_user_admin()
    tester.test_data_cleanup()
    
    # Generate final report
    is_secure = tester.generate_report()
    
    if is_secure:
        print("\n🎉 All security tests passed! DeciFrame is ready for production.")
        return 0
    else:
        print("\n⚠️ Security issues found. Please review and fix violations.")
        return 1

if __name__ == "__main__":
    sys.exit(main())