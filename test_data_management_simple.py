"""
Simple test script for Data Export & Retention System
"""
import requests
import sys
from datetime import datetime, timedelta

# Simple date formatting utility for testing (mirrors organization preferences)
def format_test_date(dt):
    """Format date for testing purposes using ISO format"""
    return dt.strftime('%Y-%m-%d')

def test_data_management():
    """Test data management functionality"""
    base_url = "http://0.0.0.0:5000"
    
    print("🧪 Testing Data Export & Retention System")
    print("=" * 50)
    
    # Test 1: Export page accessibility
    print("\n1. Testing Export Page Access...")
    try:
        response = requests.get(f"{base_url}/admin/data-management/export")
        if response.status_code == 200:
            if b'Data Export' in response.content:
                print("✅ Export page renders correctly")
            else:
                print("❌ Export page missing expected content")
        else:
            print(f"❌ Export page returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Export page test failed: {e}")
    
    # Test 2: Retention page accessibility
    print("\n2. Testing Retention Page Access...")
    try:
        response = requests.get(f"{base_url}/admin/data-management/retention")
        if response.status_code == 200:
            if b'Data Retention' in response.content:
                print("✅ Retention page renders correctly")
            else:
                print("❌ Retention page missing expected content")
        else:
            print(f"❌ Retention page returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Retention page test failed: {e}")
    
    # Test 3: CSV Download endpoints
    print("\n3. Testing CSV Download Endpoints...")
    data_types = ['problems', 'cases', 'projects', 'audit']
    
    for data_type in data_types:
        try:
            response = requests.get(f"{base_url}/admin/data-management/download-direct?type={data_type}")
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'text/csv' in content_type:
                    print(f"✅ {data_type.title()} CSV export working")
                else:
                    print(f"❌ {data_type.title()} export wrong content type: {content_type}")
            else:
                print(f"❌ {data_type.title()} export returned status {response.status_code}")
        except Exception as e:
            print(f"❌ {data_type.title()} export test failed: {e}")
    
    # Test 4: Invalid export type
    print("\n4. Testing Invalid Export Type...")
    try:
        response = requests.get(f"{base_url}/admin/data-management/download-direct?type=invalid")
        if response.status_code == 400:
            print("✅ Invalid export type properly rejected")
        else:
            print(f"❌ Invalid export type returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Invalid export type test failed: {e}")
    
    # Test 5: Date range filtering
    print("\n5. Testing Date Range Filtering...")
    try:
        start_date = format_test_date(datetime.now() - timedelta(days=30))
        end_date = format_test_date(datetime.now())
        
        response = requests.get(f"{base_url}/admin/data-management/download-direct?type=problems&start={start_date}&end={end_date}")
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'text/csv' in content_type:
                print("✅ Date range filtering working")
            else:
                print(f"❌ Date range filtering wrong content type: {content_type}")
        else:
            print(f"❌ Date range filtering returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Date range filtering test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Data Management Testing Complete")

if __name__ == "__main__":
    test_data_management()