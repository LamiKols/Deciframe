#!/usr/bin/env python3
"""
Simple PDF Export Test Script
Tests the Executive Dashboard PDF export functionality
"""

import requests
import json

def test_pdf_export():
    """Test PDF export with admin authentication"""
    base_url = "http://0.0.0.0:5000"
    
    # Session for cookie persistence
    session = requests.Session()
    
    print("🧪 Testing PDF Export System")
    
    try:
        # Step 1: Get login page to establish session
        print("1. Getting login page...")
        response = session.get(f"{base_url}/auth/login")
        if response.status_code != 200:
            print(f"❌ Login page failed: {response.status_code}")
            return False
        
        # Step 2: Login as admin
        print("2. Logging in as admin...")
        login_data = {
            'email': 'testadmin@deciframe.com',
            'password': 'admin123'
        }
        
        response = session.post(f"{base_url}/auth/login", data=login_data, allow_redirects=False)
        if response.status_code not in [200, 302]:
            print(f"❌ Login failed: {response.status_code}")
            return False
        
        print("✅ Login successful")
        
        # Step 3: Test Executive Dashboard access
        print("3. Accessing Executive Dashboard...")
        response = session.get(f"{base_url}/dashboard/executive-dashboard")
        if response.status_code != 200:
            print(f"❌ Dashboard access failed: {response.status_code}")
            return False
        
        print("✅ Executive Dashboard accessible")
        
        # Step 4: Test PDF Export
        print("4. Testing PDF Export...")
        response = session.post(f"{base_url}/dashboard/executive-dashboard/export")
        
        if response.status_code == 200:
            # Check if response is PDF
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' in content_type:
                pdf_size = len(response.content)
                print(f"✅ PDF Export successful! Size: {pdf_size} bytes")
                print(f"📄 Content-Type: {content_type}")
                return True
            else:
                print(f"❌ Response is not PDF. Content-Type: {content_type}")
                print(f"📝 Response preview: {response.text[:200]}...")
                return False
        else:
            print(f"❌ PDF Export failed: {response.status_code}")
            print(f"📝 Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_pdf_export()
    if success:
        print("\n🎉 PDF Export Test PASSED")
    else:
        print("\n💥 PDF Export Test FAILED")