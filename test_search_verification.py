#!/usr/bin/env python3
"""
Search Verification Script - Test PostgreSQL tsvector search with existing data
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from app import app, db
from models import Problem, BusinessCase, Project
from sqlalchemy import func, text

def verify_search_functionality():
    """Verify PostgreSQL tsvector search implementation"""
    
    with app.app_context():
        print("=== PostgreSQL tsvector Search Verification ===\n")
        
        # 1. Check search vector indexing status
        print("1. Checking search vector indexing status:")
        
        stats_query = text("""
            SELECT 
                'problems' as entity_type,
                COUNT(*) as total_records,
                COUNT(search_vector) as indexed_records
            FROM problems
            WHERE search_vector IS NOT NULL
            
            UNION ALL
            
            SELECT 
                'business_cases' as entity_type,
                COUNT(*) as total_records, 
                COUNT(search_vector) as indexed_records
            FROM business_cases
            WHERE search_vector IS NOT NULL
            
            UNION ALL
            
            SELECT 
                'projects' as entity_type,
                COUNT(*) as total_records,
                COUNT(search_vector) as indexed_records  
            FROM projects
            WHERE search_vector IS NOT NULL
        """)
        
        indexing_results = db.session.execute(stats_query).fetchall()
        
        for result in indexing_results:
            print(f"   {result.entity_type}: {result.indexed_records} indexed records")
        
        # 2. Test direct SQL tsvector search
        print("\n2. Testing direct PostgreSQL tsvector search:")
        
        # Search for "performance" across all entities
        performance_query = text("""
            SELECT 'problems' as type, id, title, ts_rank(search_vector, plainto_tsquery('english', :query)) as rank
            FROM problems 
            WHERE search_vector @@ plainto_tsquery('english', :query)
            
            UNION ALL
            
            SELECT 'business_cases' as type, id, title, ts_rank(search_vector, plainto_tsquery('english', :query)) as rank
            FROM business_cases
            WHERE search_vector @@ plainto_tsquery('english', :query)
            
            UNION ALL
            
            SELECT 'projects' as type, id, name as title, ts_rank(search_vector, plainto_tsquery('english', :query)) as rank
            FROM projects
            WHERE search_vector @@ plainto_tsquery('english', :query)
            
            ORDER BY rank DESC
            LIMIT 10
        """)
        
        performance_results = db.session.execute(performance_query, {"query": "performance"}).fetchall()
        
        if performance_results:
            print(f"   Found {len(performance_results)} results for 'performance':")
            for result in performance_results:
                print(f"   - {result.type}: {result.title} (rank: {result.rank:.4f})")
        else:
            print("   No results found for 'performance'")
        
        # 3. Test SQLAlchemy @@ operator implementation 
        print("\n3. Testing SQLAlchemy @@ operator implementation:")
        
        # Test Problems search
        problem_results = db.session.query(
            Problem.id,
            Problem.title,
            func.ts_rank(Problem.search_vector, func.plainto_tsquery('english', 'system')).label('rank')
        ).filter(
            Problem.search_vector.op('@@')(func.plainto_tsquery('english', 'system'))
        ).order_by(func.ts_rank(Problem.search_vector, func.plainto_tsquery('english', 'system')).desc()).limit(5).all()
        
        if problem_results:
            print(f"   Found {len(problem_results)} problems matching 'system':")
            for result in problem_results:
                print(f"   - Problem: {result.title} (rank: {result.rank:.4f})")
        else:
            print("   No problems found matching 'system'")
        
        # Test Business Cases search
        case_results = db.session.query(
            BusinessCase.id,
            BusinessCase.title,
            func.ts_rank(BusinessCase.search_vector, func.plainto_tsquery('english', 'management')).label('rank')
        ).filter(
            BusinessCase.search_vector.op('@@')(func.plainto_tsquery('english', 'management'))
        ).order_by(func.ts_rank(BusinessCase.search_vector, func.plainto_tsquery('english', 'management')).desc()).limit(5).all()
        
        if case_results:
            print(f"   Found {len(case_results)} business cases matching 'management':")
            for result in case_results:
                print(f"   - Business Case: {result.title} (rank: {result.rank:.4f})")
        else:
            print("   No business cases found matching 'management'")
        
        # Test Projects search
        project_results = db.session.query(
            Project.id,
            Project.name,
            func.ts_rank(Project.search_vector, func.plainto_tsquery('english', 'project')).label('rank')
        ).filter(
            Project.search_vector.op('@@')(func.plainto_tsquery('english', 'project'))
        ).order_by(func.ts_rank(Project.search_vector, func.plainto_tsquery('english', 'project')).desc()).limit(5).all()
        
        if project_results:
            print(f"   Found {len(project_results)} projects matching 'project':")
            for result in project_results:
                print(f"   - Project: {result.name} (rank: {result.rank:.4f})")
        else:
            print("   No projects found matching 'project'")
        
        # 4. Test sample entity data for search content
        print("\n4. Sample data content verification:")
        
        sample_problem = db.session.query(Problem).first()
        if sample_problem:
            print(f"   Sample Problem: {sample_problem.title}")
            print(f"   Description: {sample_problem.description[:100]}...")
        
        sample_case = db.session.query(BusinessCase).first()
        if sample_case:
            print(f"   Sample Business Case: {sample_case.title}")
            print(f"   Description: {sample_case.description[:100]}...")
        
        sample_project = db.session.query(Project).first()
        if sample_project:
            print(f"   Sample Project: {sample_project.name}")
            print(f"   Description: {sample_project.description[:100]}...")
        
        # 5. Test search vector trigger functionality
        print("\n5. Testing search vector trigger functionality:")
        
        # Check if search vectors are automatically populated
        vector_check_query = text("""
            SELECT 
                'problems' as type,
                COUNT(CASE WHEN search_vector IS NOT NULL THEN 1 END) as with_vectors,
                COUNT(*) as total
            FROM problems
            
            UNION ALL
            
            SELECT 
                'business_cases' as type,
                COUNT(CASE WHEN search_vector IS NOT NULL THEN 1 END) as with_vectors,
                COUNT(*) as total
            FROM business_cases
            
            UNION ALL
            
            SELECT 
                'projects' as type,
                COUNT(CASE WHEN search_vector IS NOT NULL THEN 1 END) as with_vectors,
                COUNT(*) as total
            FROM projects
        """)
        
        vector_results = db.session.execute(vector_check_query).fetchall()
        
        for result in vector_results:
            percentage = (result.with_vectors / result.total * 100) if result.total > 0 else 0
            print(f"   {result.type}: {result.with_vectors}/{result.total} have search vectors ({percentage:.1f}%)")
        
        print("\n=== Search Verification Complete ===")
        
        # Summary
        total_indexed = sum(r.with_vectors for r in vector_results)
        total_records = sum(r.total for r in vector_results)
        
        print(f"\nSummary:")
        print(f"- Total indexed entities: {total_indexed}/{total_records}")
        print(f"- PostgreSQL tsvector search: {'✓ Working' if any(performance_results) else '⚠ No results'}")
        print(f"- SQLAlchemy @@ operator: {'✓ Working' if any([problem_results, case_results, project_results]) else '⚠ No results'}")
        print(f"- Search vector triggers: {'✓ Active' if total_indexed > 0 else '⚠ Not working'}")

if __name__ == "__main__":
    verify_search_functionality()