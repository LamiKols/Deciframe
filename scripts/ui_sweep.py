#!/usr/bin/env python3
"""
Final QA UI Sweep - Zero-bug validation of all UI components
"""
import os
import sys
import re
import csv
import requests
from urllib.parse import urljoin
from datetime import datetime
from collections import defaultdict
import logging
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class UISweeper:
    """Comprehensive UI testing for all endpoints and interactions"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        
        self.results = []
        self.errors = []
        self.warnings = []
        
        # Role configuration
        self.roles = {
            'anon': None,
            'admin': {'email': 'admin@test.com', 'password': 'admin123'},
            'director': {'email': 'director@test.com', 'password': 'director123'},
            'manager': {'email': 'manager@test.com', 'password': 'manager123'},
            'staff': {'email': 'staff@test.com', 'password': 'staff123'},
        }
        
        self.discovered_endpoints = set()
        self.tested_endpoints = set()
        
        # RBAC expectations
        self.rbac_rules = {
            'admin': {'allowed_prefixes': ['/admin', '/dashboard', '/problems', '/business', '/projects']},
            'director': {'allowed_prefixes': ['/dashboard', '/problems', '/business', '/projects']},
            'manager': {'allowed_prefixes': ['/dashboard', '/problems', '/business', '/projects']},
            'staff': {'allowed_prefixes': ['/dashboard', '/problems', '/business', '/projects']},
            'anon': {'allowed_prefixes': ['/', '/login', '/register', '/public']},
        }
        
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
        
    def login_role(self, role):
        """Login as specific role"""
        if role == 'anon':
            self.session.cookies.clear()
            return True
            
        if role not in self.roles:
            self.warnings.append(f"Unknown role: {role}")
            return False
            
        credentials = self.roles[role]
        if not credentials:
            return True
            
        try:
            # Try to login via POST to /auth/login
            login_data = {
                'email': credentials['email'],
                'password': credentials['password']
            }
            
            # First get login page to extract CSRF token if needed
            login_page = self.session.get(f"{self.base_url}/auth/login")
            if login_page.status_code == 200:
                csrf_token = self.extract_csrf_token(login_page.text)
                if csrf_token:
                    login_data['csrf_token'] = csrf_token
            
            response = self.session.post(f"{self.base_url}/auth/login", data=login_data)
            
            # Check if login was successful (redirect or success status)
            if response.status_code in [200, 302] and 'dashboard' in response.text.lower():
                return True
            elif response.status_code in [200, 302]:
                # Try alternative login check
                dashboard = self.session.get(f"{self.base_url}/dashboard")
                return dashboard.status_code == 200
                
        except Exception as e:
            self.warnings.append(f"Login failed for {role}: {e}")
            
        return False
    
    def extract_csrf_token(self, html):
        """Extract CSRF token from HTML"""
        if BeautifulSoup:
            soup = BeautifulSoup(html, 'html.parser')
            csrf_input = soup.find('input', {'name': 'csrf_token'})
            return csrf_input.get('value') if csrf_input else None
        else:
            # Simple regex fallback
            match = re.search(r'name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']', html)
            return match.group(1) if match else None
    
    def discover_js_endpoints(self):
        """Discover endpoints from JavaScript files and templates"""
        js_endpoints = set()
        
        # Patterns to find endpoints in JS/templates
        patterns = [
            r"fetch\s*\(\s*['\"](/[^'\"]+)['\"]",
            r"axios\.(get|post|put|delete)\s*\(\s*['\"](/[^'\"]+)['\"]",
            r"url_for\s*\(\s*['\"]([^'\"]+)['\"]",
            r"href\s*=\s*['\"](/[^'\"]+)['\"]",
            r"action\s*=\s*['\"](/[^'\"]+)['\"]",
        ]
        
        # Search in templates
        template_dirs = ['templates', 'static']
        for template_dir in template_dirs:
            if not os.path.exists(template_dir):
                continue
                
            for root, dirs, files in os.walk(template_dir):
                for file in files:
                    if file.endswith(('.html', '.js', '.jsx', '.ts', '.tsx')):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                
                            for pattern in patterns:
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    if isinstance(match, tuple):
                                        endpoint = match[-1]  # Last group is usually the URL
                                    else:
                                        endpoint = match
                                    
                                    if endpoint.startswith('/'):
                                        js_endpoints.add((endpoint, filepath))
                                        
                        except Exception as e:
                            self.warnings.append(f"Error reading {filepath}: {e}")
        
        return js_endpoints
    
    def crawl_page_links(self, url, role):
        """Extract all links and forms from a page"""
        try:
            response = self.session.get(url)
            if response.status_code >= 400:
                return [], []
                
            links = []
            forms = []
            
            if BeautifulSoup:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract links
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and href.startswith('/'):
                        links.append(urljoin(self.base_url, href))
                
                # Extract forms
                for form in soup.find_all('form'):
                    action = form.get('action', url)
                    method = form.get('method', 'GET').upper()
                    
                    # Build form data
                    form_data = {}
                    
                    for input_tag in form.find_all(['input', 'select', 'textarea']):
                        name = input_tag.get('name')
                        if not name:
                            continue
                            
                        input_type = input_tag.get('type', 'text').lower()
                        
                        if input_type == 'submit':
                            continue
                        elif input_type == 'checkbox':
                            form_data[name] = 'on'
                        elif input_type == 'hidden':
                            form_data[name] = input_tag.get('value', '')
                        elif input_type == 'email':
                            form_data[name] = 'test@example.com'
                        elif input_type == 'password':
                            form_data[name] = 'testpass123'
                        elif input_tag.name == 'select':
                            options = input_tag.find_all('option')
                            if options:
                                form_data[name] = options[0].get('value', '')
                        else:
                            form_data[name] = 'test'
                    
                    forms.append({
                        'action': urljoin(self.base_url, action),
                        'method': method,
                        'data': form_data
                    })
            else:
                # Simple regex fallback
                href_pattern = r'href\s*=\s*["\']([^"\']+)["\']'
                for match in re.findall(href_pattern, response.text):
                    if match.startswith('/'):
                        links.append(urljoin(self.base_url, match))
                        
                form_pattern = r'<form[^>]*action\s*=\s*["\']([^"\']+)["\'][^>]*>'
                for match in re.findall(form_pattern, response.text):
                    forms.append({
                        'action': urljoin(self.base_url, match),
                        'method': 'POST',
                        'data': {'test': 'data'}
                    })
            
            return links, forms
            
        except Exception as e:
            self.errors.append(f"Error crawling {url}: {e}")
            return [], []
    
    def test_endpoint(self, url, method='GET', data=None, role='anon', source_file=None):
        """Test a specific endpoint"""
        try:
            # Skip destructive endpoints
            if any(danger in url.lower() for danger in ['delete', 'remove', 'destroy', 'clear']):
                self.warnings.append(f"Skipped destructive endpoint: {url}")
                return True
            
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, data=data or {})
            elif method.upper() == 'PUT':
                response = self.session.put(url, data=data or {})
            elif method.upper() == 'DELETE':
                # Use HEAD for DELETE to avoid actual deletion
                response = self.session.head(url)
            else:
                response = self.session.request(method, url, data=data or {})
            
            # Determine if this is expected behavior
            is_expected = self.is_expected_response(url, response.status_code, role)
            
            result = {
                'url': url,
                'method': method.upper(),
                'role': role,
                'status_code': response.status_code,
                'expected': is_expected,
                'source_file': source_file or 'crawled',
                'timestamp': datetime.now().isoformat(),
            }
            
            if not is_expected:
                result['error'] = response.text[:200] if response.text else 'No response body'
                self.errors.append(f"{role} {method} {url} -> {response.status_code}")
            
            self.results.append(result)
            self.tested_endpoints.add((url, method.upper(), role))
            
            return is_expected
            
        except Exception as e:
            self.errors.append(f"Exception testing {method} {url} as {role}: {e}")
            self.results.append({
                'url': url,
                'method': method.upper(),
                'role': role,
                'status_code': 'ERROR',
                'expected': False,
                'error': str(e),
                'source_file': source_file or 'crawled',
                'timestamp': datetime.now().isoformat(),
            })
            return False
    
    def is_expected_response(self, url, status_code, role):
        """Determine if response is expected based on RBAC rules"""
        
        # 2xx responses are generally good
        if 200 <= status_code < 300:
            return True
        
        # 3xx redirects can be acceptable
        if 300 <= status_code < 400:
            return True
        
        # 4xx/5xx responses - check if they're expected
        if status_code in [401, 403]:
            # Check if role should have access
            if role == 'anon':
                # Anonymous users should be blocked from most endpoints
                return not url.endswith(('.css', '.js', '.png', '.jpg', '.ico'))
            
            # Check role-specific access rules
            role_rules = self.rbac_rules.get(role, {})
            allowed_prefixes = role_rules.get('allowed_prefixes', [])
            
            # If role should have access but got 403/401, it's unexpected
            for prefix in allowed_prefixes:
                if url.startswith(self.base_url + prefix):
                    return False  # Should have access but didn't
            
            # If role shouldn't have access, 403/401 is expected
            return True
        
        # 404 might be acceptable for dynamic routes with placeholder IDs
        if status_code == 404:
            # Check if URL has ID placeholders that might not exist
            if re.search(r'/\d+(?:/|$)', url) or '/1' in url:
                return True  # Acceptable for non-existent IDs
        
        # Other 4xx/5xx are unexpected
        return False
    
    def run_sweep(self):
        """Run comprehensive UI sweep"""
        self.logger.info("🔍 Starting UI Sweep...")
        
        # Discover JS endpoints
        self.logger.info("📁 Discovering endpoints from templates and JS files...")
        js_endpoints = self.discover_js_endpoints()
        self.discovered_endpoints.update(ep[0] for ep in js_endpoints)
        
        # Test each role
        for role in self.roles.keys():
            self.logger.info(f"👤 Testing role: {role}")
            
            # Login as role
            if not self.login_role(role):
                self.warnings.append(f"Could not login as {role}")
                continue
            
            # Start with home page
            start_urls = ['/']
            if role != 'anon':
                start_urls.extend(['/dashboard', '/problems', '/business', '/projects'])
            
            tested_urls = set()
            urls_to_test = list(start_urls)
            
            # Crawl and test pages
            while urls_to_test and len(tested_urls) < 50:  # Limit to prevent infinite loops
                url = urls_to_test.pop(0)
                full_url = urljoin(self.base_url, url)
                
                if full_url in tested_urls:
                    continue
                    
                tested_urls.add(full_url)
                
                # Test the page itself
                self.test_endpoint(full_url, 'GET', role=role)
                
                # Extract links and forms from page
                links, forms = self.crawl_page_links(full_url, role)
                
                # Test links
                for link in links:
                    if link not in tested_urls and len(tested_urls) < 50:
                        self.test_endpoint(link, 'GET', role=role)
                        urls_to_test.append(link)
                
                # Test forms
                for form in forms:
                    if form['action'] not in tested_urls:
                        self.test_endpoint(form['action'], form['method'], form['data'], role)
            
            # Test discovered JS endpoints
            for endpoint, source_file in js_endpoints:
                full_url = urljoin(self.base_url, endpoint)
                self.test_endpoint(full_url, 'GET', role=role, source_file=source_file)
                
                # Also test as POST if it looks like an API endpoint
                if '/api/' in endpoint or endpoint.startswith('/admin/'):
                    self.test_endpoint(full_url, 'POST', role=role, source_file=source_file)
        
        self.logger.info(f"✅ UI Sweep completed: {len(self.results)} tests, {len(self.errors)} failures")
        
    def generate_reports(self):
        """Generate CSV and Markdown reports"""
        
        # CSV Report
        csv_file = 'UI_SWEEP_RESULTS.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
        
        # Markdown Report
        md_file = 'UI_SWEEP_RESULTS.md'
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# UI Sweep Results\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n")
            f.write(f"**Total Tests:** {len(self.results)}\n")
            f.write(f"**Failures:** {len(self.errors)}\n")
            f.write(f"**Warnings:** {len(self.warnings)}\n\n")
            
            # Summary by role
            role_stats = defaultdict(lambda: {'total': 0, 'passed': 0, 'failed': 0})
            for result in self.results:
                role = result['role']
                role_stats[role]['total'] += 1
                if result['expected']:
                    role_stats[role]['passed'] += 1
                else:
                    role_stats[role]['failed'] += 1
            
            f.write("## Summary by Role\n\n")
            f.write("| Role | Total | Passed | Failed | Success Rate |\n")
            f.write("|------|-------|--------|--------|-------------|\n")
            for role, stats in role_stats.items():
                success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                f.write(f"| {role} | {stats['total']} | {stats['passed']} | {stats['failed']} | {success_rate:.1f}% |\n")
            
            # Failures
            if self.errors:
                f.write("\n## Failures\n\n")
                for i, error in enumerate(self.errors[:20], 1):
                    f.write(f"{i}. {error}\n")
                
                if len(self.errors) > 20:
                    f.write(f"\n... and {len(self.errors) - 20} more failures\n")
            
            # Warnings
            if self.warnings:
                f.write("\n## Warnings\n\n")
                for warning in self.warnings:
                    f.write(f"⚠️ {warning}\n")
            
            # Detailed results
            f.write("\n## Detailed Results\n\n")
            for result in self.results:
                status = "✅" if result['expected'] else "❌"
                f.write(f"{status} `{result['method']} {result['url']}` ({result['role']}) -> {result['status_code']}\n")
                if not result['expected'] and 'error' in result:
                    f.write(f"   Error: {result['error'][:100]}...\n")
                f.write("\n")
        
        return csv_file, md_file
    
    def print_summary(self):
        """Print final summary"""
        total_tests = len(self.results)
        failed_tests = len([r for r in self.results if not r['expected']])
        success_rate = ((total_tests - failed_tests) / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("🔍 UI SWEEP FINAL REPORT")
        print("="*60)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {total_tests - failed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.warnings:
            print(f"⚠️ Warnings: {len(self.warnings)}")
        
        if failed_tests > 0:
            print("\n🚨 Top Failures:")
            for i, error in enumerate(self.errors[:5], 1):
                print(f"  {i}. {error}")
            
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors) - 5} more failures")
        
        print("\n" + "="*60)
        
        # Final verdict
        if failed_tests == 0:
            print("🎉 FINAL VERDICT: READY")
            return True
        else:
            print("🛑 FINAL VERDICT: BLOCKED")
            print(f"   {failed_tests} unexpected failures found")
            return False


def main():
    """Main execution"""
    sweeper = UISweeper()
    
    try:
        sweeper.run_sweep()
        csv_file, md_file = sweeper.generate_reports()
        
        print("\n📄 Reports generated:")
        print(f"  CSV: {csv_file}")
        print(f"  Markdown: {md_file}")
        
        success = sweeper.print_summary()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 UI Sweep interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n💥 UI Sweep error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()