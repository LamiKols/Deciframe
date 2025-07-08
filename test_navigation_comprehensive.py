#!/usr/bin/env python3
"""
Comprehensive Navigation and Dashboard Test
Tests department navigation and dashboard chart functionality
"""
import requests
import json

def test_navigation_and_dashboard():
    """Test navigation and dashboard with session authentication"""
    base_url = "http://0.0.0.0:5000"
    
    print("Testing navigation and dashboard functionality...")
    
    # Test 1: Department navigation redirect behavior
    print("\n1. Testing department navigation...")
    dept_response = requests.get(f"{base_url}/dept/", allow_redirects=False)
    if dept_response.status_code == 302:
        print("✓ Department page correctly redirects unauthenticated users")
        redirect_url = dept_response.headers.get('Location', '')
        print(f"  Redirect: {redirect_url}")
    else:
        print(f"? Department page status: {dept_response.status_code}")
    
    # Test 2: Dashboard chart endpoints
    print("\n2. Testing dashboard chart endpoints...")
    chart_endpoints = [
        "/admin/api/dashboard/problems-trend",
        "/admin/api/dashboard/status-breakdown", 
        "/admin/api/dashboard/case-conversion",
        "/admin/api/dashboard/department-heatmap",
        "/admin/api/dashboard/project-metrics"
    ]
    
    for endpoint in chart_endpoints:
        response = requests.get(f"{base_url}{endpoint}", allow_redirects=False)
        if response.status_code == 302:
            print(f"✓ {endpoint} correctly redirects unauthenticated users")
        elif response.status_code == 200:
            print(f"✓ {endpoint} loads successfully")
            try:
                data = response.json()
                print(f"  Data keys: {list(data.keys())}")
            except:
                print("  Response is not JSON")
        else:
            print(f"❌ {endpoint} returned status {response.status_code}")
    
    # Test 3: Dashboard demo endpoints (should be accessible)
    print("\n3. Testing demo dashboard endpoints...")
    demo_endpoints = [
        "/admin/api/dashboard/problems-trend-demo",
        "/admin/api/dashboard/status-breakdown-demo",
        "/admin/api/dashboard/case-conversion-demo",
        "/admin/api/dashboard/department-heatmap-demo",
        "/admin/api/dashboard/project-metrics-demo"
    ]
    
    for endpoint in demo_endpoints:
        response = requests.get(f"{base_url}{endpoint}")
        if response.status_code == 200:
            print(f"✓ {endpoint} accessible")
            try:
                data = response.json()
                if isinstance(data, dict) and data:
                    print(f"  Demo data available with {len(data)} keys")
                else:
                    print("  Empty or invalid demo data")
            except:
                print("  Response is not valid JSON")
        else:
            print(f"❌ {endpoint} failed with status {response.status_code}")
    
    # Test 4: Check session status
    print("\n4. Checking session status...")
    index_response = requests.get(f"{base_url}/")
    if "Logout" in index_response.text:
        print("✓ Active user session detected")
        if "Dashboard" in index_response.text:
            print("✓ Dashboard navigation available")
        if "Departments" in index_response.text:
            print("✓ Department navigation available")
    else:
        print("❌ No active session - user needs to log in")
    
    print("\nTest Summary:")
    print("- Department navigation: Protected with authentication redirect")
    print("- Dashboard charts: Authentication-protected API endpoints")
    print("- Demo endpoints: Should provide sample data for testing")
    print("- Navigation links: Available in authenticated interface")

if __name__ == "__main__":
    test_navigation_and_dashboard()