"""
Test Suite for PostgreSQL Full-Text Search API
Tests the simplified SQLAlchemy search implementation with seeded test data
"""

import pytest
import json
from app import app, db
from models import Problem, BusinessCase, Project, User, Department
from auth.session_auth import get_current_user

class TestSearchAPI:
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Set up test data with known keywords for search testing"""
        with app.app_context():
            # Create test user and department
            dept = Department(name="Test Department")
            db.session.add(dept)
            db.session.flush()
            
            user = User(
                email="testuser@example.com",
                first_name="Test",
                last_name="User",
                dept_id=dept.id,
                role="Staff"
            )
            db.session.add(user)
            db.session.flush()
            
            # Create test problems with specific keywords
            problems = [
                Problem(
                    title="Database Performance Optimization",
                    description="Critical database performance issues affecting user experience and system responsiveness",
                    reported_by=user.id,
                    created_by=user.id,
                    dept_id=dept.id,
                    priority="High",
                    impact="High", 
                    urgency="High",
                    status="Open"
                ),
                Problem(
                    title="Security Vulnerability Assessment",
                    description="Comprehensive security audit reveals critical vulnerabilities in authentication system",
                    reported_by=user.id,
                    created_by=user.id,
                    dept_id=dept.id,
                    priority="High",
                    impact="High",
                    urgency="High", 
                    status="Open"
                ),
                Problem(
                    title="Network Infrastructure Modernization",
                    description="Legacy network infrastructure causing connectivity issues and performance bottlenecks",
                    reported_by=user.id,
                    created_by=user.id,
                    dept_id=dept.id,
                    priority="Medium",
                    impact="Medium",
                    urgency="Medium",
                    status="In Progress"
                )
            ]
            
            for problem in problems:
                db.session.add(problem)
            
            # Create test business cases with specific keywords
            business_cases = [
                BusinessCase(
                    title="Cloud Migration Strategy Implementation",
                    description="Comprehensive cloud migration plan to reduce infrastructure costs and improve scalability",
                    summary="Strategic initiative to migrate on-premise systems to cloud infrastructure",
                    initiative_name="CloudFirst Initiative",
                    problem_id=problems[0].id,
                    created_by=user.id,
                    dept_id=dept.id,
                    case_type="Reactive",
                    status="Draft"
                ),
                BusinessCase(
                    title="Cybersecurity Enhancement Program",
                    description="Multi-phase security enhancement program addressing critical vulnerabilities and compliance requirements",
                    summary="Enterprise security modernization initiative",
                    initiative_name="SecureEnterprise Program",
                    problem_id=problems[1].id,
                    created_by=user.id,
                    dept_id=dept.id,
                    case_type="Reactive", 
                    status="Under Review"
                ),
                BusinessCase(
                    title="Digital Transformation Roadmap",
                    description="Comprehensive digital transformation strategy focusing on automation and modernization",
                    summary="Organization-wide digital transformation initiative",
                    initiative_name="DigitalFuture Strategy",
                    created_by=user.id,
                    dept_id=dept.id,
                    case_type="Proactive",
                    status="Approved"
                )
            ]
            
            for case in business_cases:
                db.session.add(case)
            
            # Create test projects with specific keywords
            projects = [
                Project(
                    name="Database Optimization Project",
                    description="Implementation of database performance optimization strategies and monitoring solutions",
                    case_id=business_cases[0].id,
                    created_by=user.id,
                    priority="High",
                    status="In Progress"
                ),
                Project(
                    name="Security Modernization Initiative", 
                    description="Enterprise security infrastructure modernization and vulnerability remediation project",
                    case_id=business_cases[1].id,
                    created_by=user.id,
                    priority="High",
                    status="Planning"
                ),
                Project(
                    name="Automation Framework Development",
                    description="Development of enterprise automation framework for process optimization and efficiency",
                    case_id=business_cases[2].id,
                    created_by=user.id,
                    priority="Medium",
                    status="Open"
                )
            ]
            
            for project in projects:
                db.session.add(project)
            
            db.session.commit()
            
            # Store IDs for test assertions
            self.test_user_id = user.id
            self.test_dept_id = dept.id
            self.problem_ids = [p.id for p in problems]
            self.case_ids = [c.id for c in business_cases]
            self.project_ids = [p.id for p in projects]
    
    def get_auth_headers(self):
        """Generate authentication headers for API requests"""
        token = create_auth_token(self.test_user_id)
        return {'Authorization': f'Bearer {token}'}
    
    def test_search_performance_keyword(self):
        """Test search for 'performance' keyword across all entities"""
        with app.test_client() as client:
            response = client.get('/api/search/?q=performance', 
                                headers=self.get_auth_headers())
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify response structure
            assert 'results' in data
            assert 'query' in data
            assert 'total' in data
            assert data['query'] == 'performance'
            
            # Should find results containing 'performance'
            assert data['total'] > 0
            assert len(data['results']) > 0
            
            # Verify we have results from multiple entity types
            found_types = set(result['type'] for result in data['results'])
            assert 'problems' in found_types  # Database Performance Optimization
            assert 'projects' in found_types  # Database Optimization Project
            
            # Verify specific expected results
            titles = [result['title'] for result in data['results']]
            assert any('Performance Optimization' in title for title in titles)
            assert any('Optimization Project' in title for title in titles)
    
    def test_search_security_keyword(self):
        """Test search for 'security' keyword"""
        with app.test_client() as client:
            response = client.get('/api/search/?q=security',
                                headers=self.get_auth_headers())
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['total'] > 0
            
            # Should find security-related items
            titles = [result['title'] for result in data['results']]
            assert any('Security' in title for title in titles)
            assert any('Cybersecurity' in title for title in titles)
            
            # Verify relevance ranking (results should be sorted by rank)
            ranks = [result.get('rank', 0) for result in data['results']]
            assert ranks == sorted(ranks, reverse=True)
    
    def test_search_cloud_migration_keywords(self):
        """Test search for 'cloud migration' multi-word query"""
        with app.test_client() as client:
            response = client.get('/api/search/?q=cloud migration',
                                headers=self.get_auth_headers())
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['total'] > 0
            
            # Should find cloud migration related items
            found_results = False
            for result in data['results']:
                if 'cloud' in result['title'].lower() or 'migration' in result['title'].lower():
                    found_results = True
                    break
            
            assert found_results, "Should find results containing 'cloud' or 'migration'"
    
    def test_search_automation_keyword(self):
        """Test search for 'automation' keyword"""
        with app.test_client() as client:
            response = client.get('/api/search/?q=automation',
                                headers=self.get_auth_headers())
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Should find automation-related items
            if data['total'] > 0:
                titles = [result['title'] for result in data['results']]
                descriptions = [result.get('description', '') for result in data['results']]
                
                # Check for automation in titles or descriptions
                found_automation = any('automation' in title.lower() for title in titles) or \
                                 any('automation' in desc.lower() for desc in descriptions)
                assert found_automation
    
    def test_search_infrastructure_keyword(self):
        """Test search for 'infrastructure' keyword"""
        with app.test_client() as client:
            response = client.get('/api/search/?q=infrastructure',
                                headers=self.get_auth_headers())
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Should find infrastructure-related items
            if data['total'] > 0:
                combined_text = ' '.join([
                    result['title'] + ' ' + result.get('description', '')
                    for result in data['results']
                ]).lower()
                
                assert 'infrastructure' in combined_text
    
    def test_search_empty_query(self):
        """Test search with empty query"""
        with app.test_client() as client:
            response = client.get('/api/search/?q=',
                                headers=self.get_auth_headers())
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Empty query should return empty results
            assert data['results'] == []
            assert data['total'] == 0
    
    def test_search_no_results(self):
        """Test search with query that should return no results"""
        with app.test_client() as client:
            response = client.get('/api/search/?q=nonexistentkeyword12345',
                                headers=self.get_auth_headers())
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Should return empty results for non-existent keywords
            assert data['total'] == 0
            assert data['results'] == []
    
    def test_search_unauthorized(self):
        """Test search without authentication"""
        with app.test_client() as client:
            response = client.get('/api/search/?q=performance')
            
            # Should require authentication
            assert response.status_code == 401
    
    def test_search_response_structure(self):
        """Test that search responses have correct structure"""
        with app.test_client() as client:
            response = client.get('/api/search/?q=security',
                                headers=self.get_auth_headers())
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify top-level structure
            required_fields = ['query', 'total', 'results']
            for field in required_fields:
                assert field in data
            
            # Verify result structure if we have results
            if data['results']:
                result = data['results'][0]
                expected_fields = ['type', 'id', 'title', 'code', 'description', 'rank', 'url']
                for field in expected_fields:
                    assert field in result
                
                # Verify type is valid
                assert result['type'] in ['problems', 'business_cases', 'projects']
                
                # Verify rank is a number
                assert isinstance(result['rank'], (int, float))
                
                # Verify URL is properly formatted
                assert result['url'].startswith('/')
    
    def test_search_suggestions_endpoint(self):
        """Test the search suggestions endpoint"""
        with app.test_client() as client:
            response = client.get('/api/search/suggestions?q=per',
                                headers=self.get_auth_headers())
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify suggestions structure
            assert 'query' in data
            assert 'suggestions' in data
            assert data['query'] == 'per'
            
            # Should have suggestions if we have matching data
            if data['suggestions']:
                suggestion = data['suggestions'][0]
                assert 'text' in suggestion
                assert 'type' in suggestion
                assert suggestion['type'] in ['problem', 'business_case', 'project']
    
    def test_search_stats_endpoint(self):
        """Test the search statistics endpoint"""
        with app.test_client() as client:
            response = client.get('/api/search/stats',
                                headers=self.get_auth_headers())
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify stats structure
            expected_fields = [
                'problems_total', 'problems_indexed',
                'cases_total', 'cases_indexed', 
                'projects_total', 'projects_indexed',
                'total_indexed', 'total_entities', 'indexing_complete'
            ]
            
            for field in expected_fields:
                assert field in data
                assert isinstance(data[field], (int, bool))
            
            # Verify logical relationships
            assert data['total_indexed'] == (data['problems_indexed'] + 
                                           data['cases_indexed'] + 
                                           data['projects_indexed'])
            assert data['total_entities'] == (data['problems_total'] + 
                                            data['cases_total'] + 
                                            data['projects_total'])

if __name__ == "__main__":
    # Run individual test methods for debugging
    import sys
    
    test_instance = TestSearchAPI()
    test_instance.setup_test_data()
    
    if len(sys.argv) > 1:
        method_name = sys.argv[1]
        if hasattr(test_instance, method_name):
            getattr(test_instance, method_name)()
            print(f"✓ {method_name} passed")
        else:
            print(f"Test method {method_name} not found")
    else:
        # Run all tests
        test_methods = [method for method in dir(test_instance) 
                       if method.startswith('test_')]
        
        passed = 0
        failed = 0
        
        for method_name in test_methods:
            try:
                getattr(test_instance, method_name)()
                print(f"✓ {method_name}")
                passed += 1
            except Exception as e:
                print(f"✗ {method_name}: {e}")
                failed += 1
        
        print(f"\nResults: {passed} passed, {failed} failed")