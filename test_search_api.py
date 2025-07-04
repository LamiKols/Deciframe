#!/usr/bin/env python3
"""
Simple test script to verify search API functionality
"""

import requests
import sys
from app import app
from auth.session_auth import create_auth_token
from models import User

def test_search_api():
    """Test the search API with proper authentication"""
    with app.app_context():
        # Get authenticated user
        user = User.query.filter_by(email='lami.kolade@gmail.com').first()
        if not user:
            print("User not found")
            return False
        
        # Create auth token
        token = create_auth_token(user.id)
        
        # Test search API
        headers = {'Authorization': f'Bearer {token}'}
        
        try:
            response = requests.get(
                'http://0.0.0.0:5000/api/search/?q=automation',
                headers=headers,
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Query: {data.get('query', 'N/A')}")
                print(f"Total Results: {data.get('total', 0)}")
                
                results = data.get('results', [])
                for i, result in enumerate(results[:3]):  # Show first 3 results
                    print(f"\nResult {i+1}:")
                    print(f"  Type: {result.get('type', 'N/A')}")
                    print(f"  ID: {result.get('id', 'N/A')}")
                    print(f"  Title: {result.get('title', 'N/A')}")
                    print(f"  Rank: {result.get('rank', 0):.4f}")
                
                return len(results) > 0
            else:
                print(f"Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"Request failed: {e}")
            return False

if __name__ == '__main__':
    success = test_search_api()
    sys.exit(0 if success else 1)