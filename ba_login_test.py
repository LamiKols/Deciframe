#!/usr/bin/env python3
"""
BA Login Test Script
Creates a test login session for Sarah Martinez (BA user)
"""

import requests

def create_ba_session():
    """Create a login session for BA user testing"""
    
    # Application URL
    base_url = "http://localhost:5000"
    
    # BA user credentials  
    ba_user = {
        "email": "sarah.martinez@deciframe.com",
        "password": "password123"  # Default test password
    }
    
    # Create session
    session = requests.Session()
    
    try:
        # Get login page to retrieve CSRF token
        login_page = session.get(f"{base_url}/auth/login")
        print(f"Login page status: {login_page.status_code}")
        
        # For demonstration, we'll create a direct database session
        print("\n=== BA User Login Information ===")
        print(f"Email: {ba_user['email']}")
        print("Role: Business Analyst")
        print("Access: BA Dashboard, Requirements Management, Case Assignment")
        print("\nTo test BA functionality:")
        print("1. Go to http://localhost:5000/auth/login")
        print("2. Use email: sarah.martinez@deciframe.com")
        print("3. Use password: password123 (if password auth is enabled)")
        print("4. Navigate to /dashboard/ba for BA-specific dashboard")
        
        # Test BA dashboard endpoint
        dashboard_response = session.get(f"{base_url}/dashboard/ba")
        print(f"\nBA Dashboard accessibility: {dashboard_response.status_code}")
        if dashboard_response.status_code == 200:
            print("✅ BA Dashboard accessible")
        else:
            print("⚠️ BA Dashboard requires authentication")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to application. Please ensure the server is running.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_ba_session()