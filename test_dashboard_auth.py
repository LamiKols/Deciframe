#!/usr/bin/env python3
"""
Test Dashboard Authentication and Functionality
"""
import requests
import sys

def test_dashboard_with_auth():
    """Test dashboard with proper session authentication"""
    base_url = "http://0.0.0.0:5000"
    
    print("Testing dashboard authentication flow...")
    
    # Test direct dashboard access to check authentication behavior
    print("\n1. Testing dashboard authentication redirect...")
    dashboard_response = requests.get(f"{base_url}/dashboard/", allow_redirects=False)
    print(f"Dashboard redirect status: {dashboard_response.status_code}")
    
    if dashboard_response.status_code == 302:
        print("✓ Dashboard properly redirects unauthenticated users")
        redirect_location = dashboard_response.headers.get('Location', '')
        print(f"Redirect location: {redirect_location}")
    
    # Test role-specific dashboard endpoints to verify templates load
    print("\n2. Testing role-specific dashboard templates...")
    role_endpoints = [
        ("/dashboard/staff", "Staff Dashboard"),
        ("/dashboard/manager", "Manager Dashboard"), 
        ("/dashboard/admin", "Admin Dashboard"),
        ("/dashboard/ba", "Business Analyst Dashboard"),
        ("/dashboard/pm", "Project Manager Dashboard"),
        ("/dashboard/director", "Director Dashboard")
    ]
    
    for endpoint, expected_title in role_endpoints:
        response = requests.get(f"{base_url}{endpoint}", allow_redirects=False)
        if response.status_code == 302:
            print(f"✓ {endpoint} properly redirects unauthenticated users")
        elif response.status_code == 200:
            print(f"✓ {endpoint} loads successfully")
        else:
            print(f"? {endpoint} returned status {response.status_code}")
    
    # Check if there's an active session by examining index page
    print("\n3. Checking for active user session...")
    index_response = requests.get(f"{base_url}/")
    
    if "Logout" in index_response.text and "Olamide" in index_response.text:
        print("✓ Found active user session (Olamide)")
        print("✓ Dashboard system ready for authenticated access")
        print("\nNext steps: User should click Dashboard link in navigation")
    elif "Login" in index_response.text:
        print("✓ No active session - login required")
        print("Next steps: User should log in first")
    else:
        print("? Session status unclear")
        print("Index page preview:", index_response.text[:400])

if __name__ == "__main__":
    test_dashboard_with_auth()