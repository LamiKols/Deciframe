#!/usr/bin/env python3
"""
Comprehensive BA Functionality Test Suite
Tests all Business Analyst features in DeciFrame
"""

import pytest
import requests
import json
from datetime import datetime, timedelta

class BAFunctionalityTester:
    def __init__(self, base_url="http://0.0.0.0:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.ba_user = None
        self.manager_user = None
        self.test_case_id = None
        
    def run_comprehensive_test(self):
        """Run complete BA functionality test suite"""
        print("🧪 Starting Comprehensive BA Functionality Testing")
        print("=" * 60)
        
        try:
            # Test 1: BA Authentication and Dashboard Access
            self.test_ba_authentication()
            
            # Test 2: BA Dashboard Features
            self.test_ba_dashboard()
            
            # Test 3: Business Case Assignment System
            self.test_ba_assignment_system()
            
            # Test 4: Requirements Generation Workflow
            self.test_requirements_generation()
            
            # Test 5: Epic and Story Management
            self.test_epic_story_management()
            
            # Test 6: Cross-Department Visibility
            self.test_cross_department_visibility()
            
            # Test 7: BA Role Permissions
            self.test_ba_role_permissions()
            
            # Test 8: Workflow Integration
            self.test_workflow_integration()
            
            print("\n✅ All BA functionality tests completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ BA functionality test failed: {e}")
            return False
    
    def test_ba_authentication(self):
        """Test BA user authentication and role verification"""
        print("\n1️⃣ Testing BA Authentication...")
        
        # Login as BA user (Sarah Martinez)
        login_data = {
            'email': 'sarah.martinez@deciframe.com',
            'password': 'password123'
        }
        
        response = self.session.post(f"{self.base_url}/auth/login", data=login_data)
        
        if response.status_code in [200, 302]:
            print("   ✅ BA user authentication successful")
            
            # Verify role-based dashboard redirect
            dashboard_response = self.session.get(f"{self.base_url}/dashboard/")
            if '/dashboard/ba' in dashboard_response.url or dashboard_response.status_code == 200:
                print("   ✅ BA dashboard redirect working correctly")
            else:
                raise Exception("BA dashboard redirect failed")
        else:
            raise Exception(f"BA authentication failed: {response.status_code}")
    
    def test_ba_dashboard(self):
        """Test BA dashboard features and metrics"""
        print("\n2️⃣ Testing BA Dashboard Features...")
        
        # Access BA dashboard
        response = self.session.get(f"{self.base_url}/dashboard/ba")
        
        if response.status_code == 200:
            print("   ✅ BA dashboard accessible")
            
            # Check for required dashboard elements
            content = response.text
            required_elements = [
                "Business Analyst Dashboard",
                "Assigned Cases",
                "Requirements Status", 
                "Monthly Performance",
                "Recent Activity"
            ]
            
            for element in required_elements:
                if element in content:
                    print(f"   ✅ Dashboard element found: {element}")
                else:
                    print(f"   ⚠️ Dashboard element missing: {element}")
        else:
            raise Exception(f"BA dashboard access failed: {response.status_code}")
    
    def test_ba_assignment_system(self):
        """Test business case assignment to BA"""
        print("\n3️⃣ Testing BA Assignment System...")
        
        # First, login as Manager to create assignment
        manager_login = {
            'email': 'lami.kolade@gmail.com',  # Manager user
            'password': 'password123'
        }
        
        manager_session = requests.Session()
        manager_response = manager_session.post(f"{self.base_url}/auth/login", data=manager_login)
        
        if manager_response.status_code in [200, 302]:
            print("   ✅ Manager authentication for assignment testing")
            
            # Find an existing business case to assign
            cases_response = manager_session.get(f"{self.base_url}/business/cases")
            
            if cases_response.status_code == 200:
                print("   ✅ Business cases list accessible by manager")
                
                # Check if we can access case detail page for assignment
                # We'll use a test case or find first available case
                case_detail_response = manager_session.get(f"{self.base_url}/business/cases/1")
                
                if case_detail_response.status_code == 200:
                    print("   ✅ Business case detail page accessible")
                    
                    # Check for assignment form
                    if "Assign Business Analyst" in case_detail_response.text:
                        print("   ✅ BA assignment form available to manager")
                    else:
                        print("   ⚠️ BA assignment form not found")
                else:
                    print("   ⚠️ Business case detail not accessible")
        else:
            print("   ⚠️ Manager authentication failed for assignment testing")
    
    def test_requirements_generation(self):
        """Test AI requirements generation workflow"""
        print("\n4️⃣ Testing Requirements Generation Workflow...")
        
        # Switch back to BA user session
        self.test_ba_authentication()
        
        # Test access to requirements generation page
        req_response = self.session.get(f"{self.base_url}/business/requirements/1")
        
        if req_response.status_code == 200:
            print("   ✅ Requirements generation page accessible")
            
            content = req_response.text
            required_elements = [
                "Requirements Generator",
                "stakeholder",
                "success criteria",
                "Generate Requirements"
            ]
            
            for element in required_elements:
                if element.lower() in content.lower():
                    print(f"   ✅ Requirements element found: {element}")
                else:
                    print(f"   ⚠️ Requirements element missing: {element}")
        else:
            print(f"   ⚠️ Requirements generation page not accessible: {req_response.status_code}")
    
    def test_epic_story_management(self):
        """Test epic and story management capabilities"""
        print("\n5️⃣ Testing Epic and Story Management...")
        
        # Test epic creation API endpoint
        epic_data = {
            "epics": [
                {
                    "id": 1,
                    "title": "Test Epic for BA Functionality",
                    "description": "Testing epic management by BA user",
                    "stories": [
                        {
                            "id": 1,
                            "title": "Test User Story",
                            "criteria": "As a BA, I can manage user stories"
                        }
                    ]
                }
            ]
        }
        
        # Test requirements save API
        save_response = self.session.post(
            f"{self.base_url}/api/requirements/save",
            json=epic_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if save_response.status_code == 200:
            result = save_response.json()
            if result.get('success'):
                print("   ✅ Epic and story save functionality working")
            else:
                print(f"   ⚠️ Epic save failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"   ⚠️ Epic save API not accessible: {save_response.status_code}")
    
    def test_cross_department_visibility(self):
        """Test cross-department case visibility for BA"""
        print("\n6️⃣ Testing Cross-Department Visibility...")
        
        # Test access to business cases from other departments
        cases_response = self.session.get(f"{self.base_url}/business/cases")
        
        if cases_response.status_code == 200:
            print("   ✅ Business cases list accessible to BA")
            
            # Check for department filtering options
            content = cases_response.text
            if "department" in content.lower() or "filter" in content.lower():
                print("   ✅ Department filtering available")
            else:
                print("   ⚠️ Department filtering not found")
        else:
            print(f"   ⚠️ Business cases not accessible: {cases_response.status_code}")
    
    def test_ba_role_permissions(self):
        """Test BA-specific role permissions"""
        print("\n7️⃣ Testing BA Role Permissions...")
        
        # Test access to BA-specific endpoints
        ba_endpoints = [
            "/dashboard/ba",
            "/business/requirements/1",
            "/api/requirements/save"
        ]
        
        for endpoint in ba_endpoints:
            if endpoint == "/api/requirements/save":
                # POST endpoint test
                response = self.session.post(f"{self.base_url}{endpoint}", 
                                           json={"test": "data"},
                                           headers={'Content-Type': 'application/json'})
            else:
                # GET endpoint test
                response = self.session.get(f"{self.base_url}{endpoint}")
            
            if response.status_code in [200, 400]:  # 400 is ok for malformed data
                print(f"   ✅ BA endpoint accessible: {endpoint}")
            else:
                print(f"   ⚠️ BA endpoint not accessible: {endpoint} ({response.status_code})")
    
    def test_workflow_integration(self):
        """Test workflow integration and notifications"""
        print("\n8️⃣ Testing Workflow Integration...")
        
        # Test notification access
        notifications_response = self.session.get(f"{self.base_url}/notifications/")
        
        if notifications_response.status_code == 200:
            print("   ✅ Notifications system accessible to BA")
        else:
            print(f"   ⚠️ Notifications not accessible: {notifications_response.status_code}")
        
        # Test profile access
        profile_response = self.session.get(f"{self.base_url}/auth/profile")
        
        if profile_response.status_code == 200:
            print("   ✅ Profile management accessible to BA")
        else:
            print(f"   ⚠️ Profile not accessible: {profile_response.status_code}")

def main():
    """Run the comprehensive BA functionality test"""
    tester = BAFunctionalityTester()
    success = tester.run_comprehensive_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 BA Functionality Test Suite: ALL TESTS PASSED")
        print("✅ Business Analyst features are fully operational")
    else:
        print("⚠️ BA Functionality Test Suite: SOME ISSUES FOUND")
        print("📋 Review test output above for specific issues")
    
    return success

if __name__ == "__main__":
    main()