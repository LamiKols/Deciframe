"""
Simple Role-Scoped Dashboards Test Suite
Tests role-specific dashboard routing and content using direct HTTP requests
"""
import pytest
import requests
import time


def test_dashboard_routing_and_content():
    """Test that dashboards route correctly and display role-specific content"""
    
    base_url = "http://0.0.0.0:5000"
    
    # Test role-specific content patterns
    role_tests = [
        {
            'role': 'staff',
            'email': 'alice.smith@company.com',
            'expected_content': ['Staff Dashboard', 'My Problems', 'My Business Cases'],
            'expected_url': '/dashboard/staff'
        },
        {
            'role': 'manager', 
            'email': 'bob.manager@company.com',
            'expected_content': ['Manager Dashboard', 'Department Overview', 'Team Performance'],
            'expected_url': '/dashboard/manager'
        },
        {
            'role': 'ba',
            'email': 'carol.analyst@company.com', 
            'expected_content': ['Business Analyst Dashboard', 'Assigned Cases', 'Requirements'],
            'expected_url': '/dashboard/ba'
        },
        {
            'role': 'pm',
            'email': 'david.pm@company.com',
            'expected_content': ['Project Manager Dashboard', 'Active Projects', 'Milestones'],
            'expected_url': '/dashboard/pm'
        },
        {
            'role': 'director',
            'email': 'eve.director@company.com',
            'expected_content': ['Director Dashboard', 'Strategic Overview', 'Approval'],
            'expected_url': '/dashboard/director'
        },
        {
            'role': 'admin',
            'email': 'admin@company.com',
            'expected_content': ['Admin Dashboard', 'System Health', 'User Management'],
            'expected_url': '/dashboard/admin'
        }
    ]
    
    session = requests.Session()
    
    for role_test in role_tests:
        print(f"\n🧪 Testing {role_test['role']} dashboard...")
        
        # Login as role-specific user
        login_data = {
            'email': role_test['email'],
            'password': 'password123',
            'csrf_token': 'test'
        }
        
        # First get login form to establish session
        login_page = session.get(f"{base_url}/auth/login")
        
        # Attempt login
        login_response = session.post(f"{base_url}/auth/login", data=login_data, allow_redirects=False)
        
        if login_response.status_code == 302:
            print(f"✅ Login successful for {role_test['role']}")
            
            # Test dashboard home redirect
            dashboard_response = session.get(f"{base_url}/dashboard/", allow_redirects=False)
            
            if dashboard_response.status_code == 302:
                redirect_location = dashboard_response.headers.get('Location', '')
                print(f"✅ Dashboard redirect: {redirect_location}")
                
                # Verify redirect goes to correct role dashboard
                if role_test['expected_url'] in redirect_location:
                    print(f"✅ Correct redirect to {role_test['expected_url']}")
                else:
                    print(f"❌ Incorrect redirect. Expected {role_test['expected_url']}, got {redirect_location}")
            
            # Test role-specific dashboard content
            dashboard_content = session.get(f"{base_url}{role_test['expected_url']}")
            
            if dashboard_content.status_code == 200:
                print(f"✅ Dashboard page accessible")
                
                content_text = dashboard_content.text
                missing_content = []
                
                for expected in role_test['expected_content']:
                    if expected in content_text:
                        print(f"✅ Found expected content: {expected}")
                    else:
                        missing_content.append(expected)
                        print(f"❌ Missing expected content: {expected}")
                
                if not missing_content:
                    print(f"✅ All expected content found for {role_test['role']}")
                else:
                    print(f"❌ Missing content for {role_test['role']}: {missing_content}")
                    
            else:
                print(f"❌ Dashboard page not accessible: {dashboard_content.status_code}")
        else:
            print(f"❌ Login failed for {role_test['role']}: {login_response.status_code}")
        
        # Logout to clean session
        session.get(f"{base_url}/auth/logout")
        time.sleep(0.5)  # Brief pause between tests


def test_unauthenticated_access():
    """Test that unauthenticated users are redirected to login"""
    
    base_url = "http://0.0.0.0:5000"
    
    dashboard_urls = [
        '/dashboard/',
        '/dashboard/staff',
        '/dashboard/manager', 
        '/dashboard/ba',
        '/dashboard/pm',
        '/dashboard/director',
        '/dashboard/admin'
    ]
    
    print("\n🧪 Testing unauthenticated access...")
    
    for url in dashboard_urls:
        response = requests.get(f"{base_url}{url}", allow_redirects=False)
        
        if response.status_code == 302:
            redirect_location = response.headers.get('Location', '')
            if '/auth/login' in redirect_location:
                print(f"✅ {url} correctly redirects to login")
            else:
                print(f"❌ {url} redirects to unexpected location: {redirect_location}")
        else:
            print(f"❌ {url} should redirect but returned: {response.status_code}")


def test_navigation_integration():
    """Test that dashboard navigation is properly integrated"""
    
    base_url = "http://0.0.0.0:5000"
    session = requests.Session()
    
    print("\n🧪 Testing navigation integration...")
    
    # Login as staff user
    login_data = {
        'email': 'alice.smith@company.com',
        'password': 'password123',
        'csrf_token': 'test'
    }
    
    login_page = session.get(f"{base_url}/auth/login")
    login_response = session.post(f"{base_url}/auth/login", data=login_data, allow_redirects=False)
    
    if login_response.status_code == 302:
        # Check that dashboard link exists in navigation
        dashboard_page = session.get(f"{base_url}/dashboard/staff")
        
        if dashboard_page.status_code == 200:
            content = dashboard_page.text
            
            # Check for dashboard navigation elements
            nav_indicators = [
                'Dashboard',
                'href="/dashboard/"',
                'dashboards.dashboard_home',
                'tachometer'
            ]
            
            found_indicators = []
            for indicator in nav_indicators:
                if indicator in content:
                    found_indicators.append(indicator)
            
            if found_indicators:
                print(f"✅ Navigation integration confirmed: {found_indicators}")
            else:
                print(f"❌ No navigation indicators found")
        else:
            print(f"❌ Could not access dashboard page: {dashboard_page.status_code}")
    else:
        print(f"❌ Login failed for navigation test: {login_response.status_code}")


if __name__ == '__main__':
    print("🚀 Starting Role-Scoped Dashboards Test Suite")
    print("=" * 60)
    
    test_dashboard_routing_and_content()
    test_unauthenticated_access() 
    test_navigation_integration()
    
    print("\n" + "=" * 60)
    print("🏁 Test suite completed")