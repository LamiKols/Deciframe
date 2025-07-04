#!/usr/bin/env python3
"""
Direct test of Role-Scoped Dashboards functionality
Tests using actual system users and direct HTTP requests
"""
import requests
import time

def test_dashboard_functionality():
    """Test dashboard routing and content with actual system users"""
    
    base_url = "http://0.0.0.0:5000"
    
    print("Testing Role-Scoped Dashboards System")
    print("=" * 50)
    
    # Test 1: Verify unauthenticated access redirects to login
    print("\n1. Testing unauthenticated access...")
    
    dashboard_urls = ['/dashboard/', '/dashboard/staff', '/dashboard/admin']
    
    for url in dashboard_urls:
        response = requests.get(f"{base_url}{url}", allow_redirects=False)
        if response.status_code == 302 and '/auth/login' in response.headers.get('Location', ''):
            print(f"✓ {url} correctly redirects to login")
        else:
            print(f"✗ {url} unexpected response: {response.status_code}")
    
    # Test 2: Try to login with common test credentials and test dashboard routing
    print("\n2. Testing dashboard routing with test user...")
    
    session = requests.Session()
    
    # Get login page first to establish session
    login_page = session.get(f"{base_url}/auth/login")
    
    # Try login with admin credentials commonly used in demo systems
    test_credentials = [
        ('admin@example.com', 'admin123'),
        ('admin@company.com', 'password123'),
        ('test@example.com', 'test123'),
        ('user@example.com', 'password'),
    ]
    
    login_successful = False
    
    for email, password in test_credentials:
        login_data = {
            'email': email,
            'password': password,
            'csrf_token': 'test'
        }
        
        login_response = session.post(f"{base_url}/auth/login", data=login_data, allow_redirects=False)
        
        if login_response.status_code == 302 and '/dashboard/' in login_response.headers.get('Location', ''):
            print(f"✓ Login successful with {email}")
            login_successful = True
            break
        else:
            print(f"- Login attempt with {email} failed")
    
    if login_successful:
        # Test dashboard home redirect
        dashboard_response = session.get(f"{base_url}/dashboard/", allow_redirects=False)
        
        if dashboard_response.status_code == 302:
            redirect_location = dashboard_response.headers.get('Location', '')
            print(f"✓ Dashboard home redirects to: {redirect_location}")
            
            # Test specific dashboard page
            if '/dashboard/' in redirect_location:
                final_dashboard = session.get(f"{base_url}{redirect_location}")
                
                if final_dashboard.status_code == 200:
                    print("✓ Role-specific dashboard loads successfully")
                    
                    # Check for dashboard-specific content
                    content = final_dashboard.text
                    dashboard_indicators = [
                        'Dashboard',
                        'KPI',
                        'Projects',
                        'Problems',
                        'Cases'
                    ]
                    
                    found_indicators = [ind for ind in dashboard_indicators if ind in content]
                    print(f"✓ Dashboard content includes: {', '.join(found_indicators)}")
                    
                    # Test navigation integration
                    if 'href="/dashboard/"' in content or 'dashboards.dashboard_home' in content:
                        print("✓ Dashboard navigation properly integrated")
                    else:
                        print("- Dashboard navigation not found in content")
                        
                else:
                    print(f"✗ Dashboard page failed to load: {final_dashboard.status_code}")
        else:
            print(f"✗ Dashboard home should redirect but returned: {dashboard_response.status_code}")
    else:
        print("! No successful login - testing with registration...")
        
        # Test 3: Create a test user and verify dashboard functionality
        print("\n3. Testing with user registration...")
        
        # Register a new test user
        register_data = {
            'name': 'Test Dashboard User',
            'email': 'testdash@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'role': 'Staff',
            'department_id': '1',
            'csrf_token': 'test'
        }
        
        register_response = session.post(f"{base_url}/auth/register", data=register_data, allow_redirects=False)
        
        if register_response.status_code == 302:
            redirect_location = register_response.headers.get('Location', '')
            
            if '/dashboard/' in redirect_location:
                print("✓ Registration redirects to dashboard")
                
                # Follow redirect to dashboard
                dashboard_page = session.get(f"{base_url}/dashboard/", allow_redirects=True)
                
                if dashboard_page.status_code == 200:
                    print("✓ Dashboard accessible after registration")
                    
                    content = dashboard_page.text
                    if 'Staff Dashboard' in content:
                        print("✓ Correct role-specific dashboard displayed")
                    else:
                        print("- Role-specific content not clearly identified")
                        
                else:
                    print(f"✗ Dashboard not accessible: {dashboard_page.status_code}")
            else:
                print(f"- Registration redirects to: {redirect_location}")
        else:
            print(f"- Registration response: {register_response.status_code}")
    
    # Test 4: Test different dashboard URLs directly if we have a session
    print("\n4. Testing individual dashboard routes...")
    
    dashboard_routes = [
        '/dashboard/staff',
        '/dashboard/manager', 
        '/dashboard/admin'
    ]
    
    for route in dashboard_routes:
        response = session.get(f"{base_url}{route}")
        
        if response.status_code == 200:
            print(f"✓ {route} accessible")
        elif response.status_code == 302:
            print(f"- {route} redirects (possibly auth required)")
        else:
            print(f"✗ {route} error: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("Dashboard testing completed")


if __name__ == '__main__':
    test_dashboard_functionality()