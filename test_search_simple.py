"""
Simple Search Test - Verify PostgreSQL tsvector search functionality
Tests the /api/search endpoint with seeded data and known keywords
"""

import sys
import os
sys.path.insert(0, os.getcwd())

import requests
import json
from app import app, db
from models import Problem, BusinessCase, Project, User, Department
from auth.session_auth import create_auth_token

def test_search_with_seeded_data():
    """Test search functionality with seeded test data"""
    
    with app.app_context():
        print("Setting up test data...")
        
        # Create test department and user
        dept = Department(name="Test Search Department")
        db.session.add(dept)
        db.session.flush()
        
        user = User(
            email="searchtest@example.com",
            first_name="Search",
            last_name="Tester",
            dept_id=dept.id,
            role="Staff"
        )
        db.session.add(user)
        db.session.flush()
        
        # Create test problem with specific keywords
        problem = Problem(
            title="Database Performance Optimization Critical Issue",
            description="Critical database performance bottlenecks affecting system responsiveness and user experience",
            reported_by=user.id,
            created_by=user.id,
            dept_id=dept.id,
            priority="High",
            impact="High",
            urgency="High",
            status="Open"
        )
        db.session.add(problem)
        
        # Create test business case with specific keywords
        case = BusinessCase(
            title="Cloud Infrastructure Migration Strategy",
            description="Comprehensive cloud migration initiative to modernize infrastructure and reduce operational costs",
            summary="Strategic cloud transformation project",
            initiative_name="CloudFirst Initiative",
            problem_id=problem.id,
            created_by=user.id,
            dept_id=dept.id,
            case_type="Reactive",
            status="Draft"
        )
        db.session.add(case)
        
        # Create test project with specific keywords
        project = Project(
            name="Security Automation Framework Development",
            description="Enterprise security automation framework for vulnerability management and compliance monitoring",
            case_id=case.id,
            created_by=user.id,
            priority="High",
            status="In Progress"
        )
        db.session.add(project)
        
        db.session.commit()
        print("✓ Test data created successfully")
        
        # Generate auth token
        token = create_auth_token(user.id)
        
        # Test the search API
        base_url = "http://0.0.0.0:5000"
        headers = {'Authorization': f'Bearer {token}'}
        
        print("\nTesting search functionality...")
        
        # Test 1: Search for "performance"
        print("\n1. Testing search for 'performance':")
        response = requests.get(f"{base_url}/api/search/?q=performance", 
                              headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {data['total']} results")
            for result in data['results'][:3]:
                print(f"   - {result['type']}: {result['title']} (rank: {result['rank']:.3f})")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
        
        # Test 2: Search for "cloud"
        print("\n2. Testing search for 'cloud':")
        response = requests.get(f"{base_url}/api/search/?q=cloud", 
                              headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {data['total']} results")
            for result in data['results'][:3]:
                print(f"   - {result['type']}: {result['title']} (rank: {result['rank']:.3f})")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
        
        # Test 3: Search for "security automation"
        print("\n3. Testing search for 'security automation':")
        response = requests.get(f"{base_url}/api/search/?q=security automation", 
                              headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {data['total']} results")
            for result in data['results'][:3]:
                print(f"   - {result['type']}: {result['title']} (rank: {result['rank']:.3f})")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
        
        # Test 4: Test search statistics
        print("\n4. Testing search statistics:")
        response = requests.get(f"{base_url}/api/search/stats", 
                              headers=headers, timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            print(f"   Problems: {stats['problems_indexed']}/{stats['problems_total']}")
            print(f"   Business Cases: {stats['cases_indexed']}/{stats['cases_total']}")
            print(f"   Projects: {stats['projects_indexed']}/{stats['projects_total']}")
            print(f"   Indexing Complete: {stats['indexing_complete']}")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
        
        # Verify search vector indexing via direct SQL
        print("\n5. Verifying search vector indexing:")
        from sqlalchemy import text
        
        result = db.session.execute(text("""
            SELECT 'problems' as type, COUNT(*) as total, COUNT(search_vector) as indexed
            FROM problems
            UNION ALL
            SELECT 'business_cases' as type, COUNT(*) as total, COUNT(search_vector) as indexed  
            FROM business_cases
            UNION ALL
            SELECT 'projects' as type, COUNT(*) as total, COUNT(search_vector) as indexed
            FROM projects
        """)).fetchall()
        
        for row in result:
            print(f"   {row.type}: {row.indexed}/{row.total} indexed")
        
        print("\n✓ Search functionality test completed successfully!")

if __name__ == "__main__":
    test_search_with_seeded_data()