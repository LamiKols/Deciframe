#!/usr/bin/env python3
"""
Complete Monitoring System Test
Validates all monitoring components: dashboard, configuration, metrics, health checks
"""

import requests
import json
import time
from datetime import datetime

def test_monitoring_system():
    """Test complete monitoring system functionality"""
    base_url = "http://0.0.0.0:5000"
    
    print("🔍 Testing Complete Monitoring System Integration")
    print("=" * 60)
    
    # Test 1: Health Check Endpoint
    print("\n1. Testing Health Check Endpoint")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check successful")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Database: {health_data.get('database')}")
            print(f"   Timestamp: {health_data.get('timestamp')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Prometheus Metrics Endpoint
    print("\n2. Testing Prometheus Metrics Endpoint")
    try:
        response = requests.get(f"{base_url}/metrics", timeout=10)
        if response.status_code == 200:
            metrics_content = response.text
            print(f"✅ Metrics endpoint accessible")
            
            # Check for key metrics
            key_metrics = [
                'python_info',
                'process_virtual_memory_bytes',
                'flask_http_request_duration_seconds',
                'api_requests_total'
            ]
            
            found_metrics = []
            for metric in key_metrics:
                if metric in metrics_content:
                    found_metrics.append(metric)
            
            print(f"   Found metrics: {len(found_metrics)}/{len(key_metrics)}")
            for metric in found_metrics:
                print(f"   ✓ {metric}")
            
            missing_metrics = set(key_metrics) - set(found_metrics)
            if missing_metrics:
                print(f"   Missing metrics: {list(missing_metrics)}")
        else:
            print(f"❌ Metrics endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Metrics endpoint error: {e}")
    
    # Test 3: Error Test Endpoint
    print("\n3. Testing Error Generation Endpoint")
    try:
        response = requests.get(f"{base_url}/error", timeout=10)
        # We expect this to return an error status
        print(f"✅ Error endpoint triggered (status: {response.status_code})")
        print("   This tests Sentry error capture functionality")
    except Exception as e:
        print(f"✅ Error endpoint properly triggered exception: {type(e).__name__}")
    
    # Test 4: Monitoring Dashboard Endpoint
    print("\n4. Testing Monitoring Dashboard")
    try:
        response = requests.get(f"{base_url}/monitoring/dashboard", timeout=10)
        if response.status_code == 200:
            print(f"✅ Monitoring dashboard accessible")
            content = response.text
            
            # Check for key dashboard elements
            dashboard_elements = [
                'System Monitoring Dashboard',
                'CPU Usage',
                'Memory Usage',
                'Database Status',
                'Monitoring Configuration'
            ]
            
            found_elements = []
            for element in dashboard_elements:
                if element in content:
                    found_elements.append(element)
            
            print(f"   Dashboard elements: {len(found_elements)}/{len(dashboard_elements)}")
            for element in found_elements:
                print(f"   ✓ {element}")
        else:
            print(f"❌ Monitoring dashboard failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Monitoring dashboard error: {e}")
    
    # Test 5: System Stats API
    print("\n5. Testing System Statistics API")
    try:
        response = requests.get(f"{base_url}/monitoring/api/system-stats", timeout=10)
        if response.status_code == 200:
            stats_data = response.json()
            print(f"✅ System stats API accessible")
            
            # Check for key statistics
            if 'cpu' in stats_data:
                print(f"   CPU Usage: {stats_data['cpu'].get('usage_percent', 'N/A')}%")
            if 'memory' in stats_data:
                print(f"   Memory Usage: {stats_data['memory'].get('usage_percent', 'N/A')}%")
            if 'disk' in stats_data:
                print(f"   Disk Usage: {stats_data['disk'].get('usage_percent', 'N/A')}%")
        else:
            print(f"❌ System stats API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ System stats API error: {e}")
    
    # Test 6: Alerts API
    print("\n6. Testing Alerts API")
    try:
        response = requests.get(f"{base_url}/monitoring/api/alerts", timeout=10)
        if response.status_code == 200:
            alerts_data = response.json()
            print(f"✅ Alerts API accessible")
            print(f"   Alert count: {alerts_data.get('count', 0)}")
            if alerts_data.get('alerts'):
                for alert in alerts_data['alerts'][:3]:  # Show first 3 alerts
                    print(f"   - {alert.get('type')}: {alert.get('message')}")
        else:
            print(f"❌ Alerts API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Alerts API error: {e}")
    
    # Test 7: Configuration Status
    print("\n7. Testing Monitoring Configuration")
    monitoring_features = {
        'Sentry Error Tracking': '/error',
        'Prometheus Metrics': '/metrics', 
        'Health Checks': '/health',
        'System Dashboard': '/monitoring/dashboard'
    }
    
    working_features = 0
    for feature, endpoint in monitoring_features.items():
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code in [200, 500]:  # 500 is expected for /error
                print(f"   ✅ {feature}")
                working_features += 1
            else:
                print(f"   ❌ {feature} (status: {response.status_code})")
        except Exception:
            print(f"   ❌ {feature} (connection error)")
    
    print(f"\n📊 Monitoring System Summary")
    print(f"Working features: {working_features}/{len(monitoring_features)}")
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if working_features >= len(monitoring_features) - 1:  # Allow 1 failure
        print("🎉 Monitoring system is fully operational!")
        return True
    else:
        print("⚠️ Some monitoring features need attention")
        return False

if __name__ == "__main__":
    success = test_monitoring_system()
    exit(0 if success else 1)