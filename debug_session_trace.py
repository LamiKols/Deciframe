#!/usr/bin/env python3
"""
Flask-Login Session Persistence Debugging Script
Traces session data flow and identifies persistence issues
"""
import requests
import json
from urllib.parse import urljoin

class SessionTracer:
    def __init__(self, base_url="http://0.0.0.0:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_session_flow(self):
        """Test complete authentication flow with session tracing"""
        print("🔍 Starting Flask-Login Session Persistence Test")
        print("=" * 50)
        
        # Step 1: Check initial session state
        print("\n1. Initial session state:")
        self._check_debug_endpoint()
        
        # Step 2: Access login page
        print("\n2. Accessing login page:")
        login_response = self.session.get(urljoin(self.base_url, "/auth/login"))
        print(f"   Status: {login_response.status_code}")
        print(f"   Cookies: {dict(login_response.cookies)}")
        
        # Step 3: Submit login form
        print("\n3. Submitting login credentials:")
        login_data = {
            'email': 'lami.kolade@gmail.com',
            'password': 'password123',
            'submit': 'Sign In'
        }
        
        post_response = self.session.post(
            urljoin(self.base_url, "/auth/login"),
            data=login_data,
            allow_redirects=False
        )
        
        print(f"   Status: {post_response.status_code}")
        print(f"   Location: {post_response.headers.get('Location', 'None')}")
        print(f"   Cookies after login: {dict(post_response.cookies)}")
        
        # Step 4: Follow redirect
        if post_response.status_code in [301, 302, 303, 307, 308]:
            print("\n4. Following redirect:")
            redirect_url = post_response.headers['Location']
            redirect_response = self.session.get(redirect_url)
            print(f"   Status: {redirect_response.status_code}")
            print(f"   Final URL: {redirect_response.url}")
            
        # Step 5: Check session after login
        print("\n5. Session state after login:")
        self._check_debug_endpoint()
        
        # Step 6: Test direct access to protected area
        print("\n6. Testing direct access to home page:")
        home_response = self.session.get(urljoin(self.base_url, "/"))
        print(f"   Status: {home_response.status_code}")
        print(f"   Final URL: {home_response.url}")
        
        # Step 7: Final session check
        print("\n7. Final session state:")
        self._check_debug_endpoint()
        
    def _check_debug_endpoint(self):
        """Check session debug endpoint"""
        try:
            debug_response = self.session.get(urljoin(self.base_url, "/debug-session"))
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                print(f"   Flask Session: {debug_data.get('flask_session', {})}")
                print(f"   JWT Auth: {debug_data.get('jwt_user', {})}")
                print(f"   Request Args: {debug_data.get('request_args', {})}")
            else:
                print(f"   Debug endpoint error: {debug_response.status_code}")
        except Exception as e:
            print(f"   Debug endpoint exception: {e}")
    
    def test_flask_login_specific(self):
        """Test Flask-Login specific behavior"""
        print("\n🔍 Flask-Login Specific Tests")
        print("=" * 30)
        
        # Test remember me functionality
        print("\n1. Testing 'Remember Me' functionality:")
        login_data = {
            'email': 'lami.kolade@gmail.com',
            'password': 'password123',
            'remember_me': True,
            'submit': 'Sign In'
        }
        
        response = self.session.post(
            urljoin(self.base_url, "/auth/login"),
            data=login_data
        )
        
        print(f"   Response cookies: {dict(response.cookies)}")
        
        # Check for Flask-Login session keys
        debug_response = self.session.get(urljoin(self.base_url, "/debug-session"))
        if debug_response.status_code == 200:
            session_data = debug_response.json().get('flask_session', {})
            flask_login_keys = [k for k in session_data.keys() if k.startswith('_')]
            print(f"   Flask-Login keys found: {flask_login_keys}")

if __name__ == "__main__":
    tracer = SessionTracer()
    
    print("Flask-Login Session Persistence Debugging")
    print("This script will trace the complete authentication flow")
    print("and identify where session data is lost.\n")
    
    try:
        # Test current JWT implementation
        tracer.test_session_flow()
        
        # Test Flask-Login specific features
        tracer.test_flask_login_specific()
        
        print("\n" + "=" * 50)
        print("✅ Session tracing complete!")
        print("Review the output above to identify persistence issues.")
        
    except Exception as e:
        print(f"\n❌ Error during session tracing: {e}")
        print("Make sure the Flask application is running on http://0.0.0.0:5000")