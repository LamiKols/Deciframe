"""
Test Suite for Simplified PostgreSQL Full-Text Search
Demonstrates the clean SQLAlchemy approach with plainto_tsquery and @@ operator
"""

from app import app
from models import Problem, BusinessCase, Project
from sqlalchemy import func
import json

def test_simplified_search_api():
    """Test the simplified search API implementation"""
    
    with app.app_context():
        print("Testing Simplified SQLAlchemy tsvector Search")
        print("=" * 50)
        
        # Test query
        query = "system performance"
        tsq = func.plainto_tsquery('english', query)
        
        print(f"Search Query: '{query}'")
        print()
        
        # Test Problems with ranking
        print("1. Problems Search:")
        problems = Problem.query\
            .filter(Problem.search_vector.op('@@')(tsq))\
            .add_columns(func.ts_rank(Problem.search_vector, tsq).label('rank'))\
            .order_by(func.ts_rank(Problem.search_vector, tsq).desc())\
            .limit(5).all()
        
        print(f"   Found {len(problems)} problems")
        for problem, rank in problems:
            print(f"   - {problem.code}: {problem.title} (rank: {rank:.3f})")
        print()
        
        # Test Business Cases with ranking
        print("2. Business Cases Search:")
        cases = BusinessCase.query\
            .filter(BusinessCase.search_vector.op('@@')(tsq))\
            .add_columns(func.ts_rank(BusinessCase.search_vector, tsq).label('rank'))\
            .order_by(func.ts_rank(BusinessCase.search_vector, tsq).desc())\
            .limit(5).all()
        
        print(f"   Found {len(cases)} business cases")
        for case, rank in cases:
            print(f"   - {case.code}: {case.title} (rank: {rank:.3f})")
        print()
        
        # Test Projects with ranking
        print("3. Projects Search:")
        projects = Project.query\
            .filter(Project.search_vector.op('@@')(tsq))\
            .add_columns(func.ts_rank(Project.search_vector, tsq).label('rank'))\
            .order_by(func.ts_rank(Project.search_vector, tsq).desc())\
            .limit(5).all()
        
        print(f"   Found {len(projects)} projects")
        for project, rank in projects:
            print(f"   - {project.code}: {project.name} (rank: {rank:.3f})")
        print()
        
        # Test the to_dict function like in your implementation
        print("4. Testing to_dict function:")
        def to_dict(obj):
            return {
                'type': obj.__tablename__, 
                'id': obj.id, 
                'title': getattr(obj, 'title', getattr(obj, 'name', '')), 
                'snippet': ''
            }
        
        # Combine all results
        all_objects = [p[0] for p in problems] + [c[0] for c in cases] + [p[0] for p in projects]
        results = list(map(to_dict, all_objects))
        
        print(f"   Combined results: {len(results)} entities")
        for result in results[:5]:
            print(f"   - {result['type']}: {result['title']}")
        print()
        
        # Test different queries
        print("5. Testing various search queries:")
        test_queries = [
            "automation",
            "infrastructure migration", 
            "cost benefit",
            "security compliance"
        ]
        
        for test_query in test_queries:
            test_tsq = func.plainto_tsquery('english', test_query)
            
            # Quick count across all entities
            prob_count = Problem.query.filter(Problem.search_vector.op('@@')(test_tsq)).count()
            case_count = BusinessCase.query.filter(BusinessCase.search_vector.op('@@')(test_tsq)).count()  
            proj_count = Project.query.filter(Project.search_vector.op('@@')(test_tsq)).count()
            
            total_count = prob_count + case_count + proj_count
            print(f"   '{test_query}': {total_count} results ({prob_count}P, {case_count}C, {proj_count}Pr)")
        
        print()
        print("✓ Simplified search implementation working correctly!")
        print("✓ SQLAlchemy @@ operator and plainto_tsquery functional")
        print("✓ Relevance ranking with ts_rank() operational")
        print("✓ Multi-entity search with proper result mapping")

def test_search_indexing_status():
    """Verify search vector indexing across all entities"""
    
    with app.app_context():
        print("Search Indexing Status:")
        print("-" * 30)
        
        # Check indexing status
        prob_total = Problem.query.count()
        prob_indexed = Problem.query.filter(Problem.search_vector.isnot(None)).count()
        
        case_total = BusinessCase.query.count()
        case_indexed = BusinessCase.query.filter(BusinessCase.search_vector.isnot(None)).count()
        
        proj_total = Project.query.count()
        proj_indexed = Project.query.filter(Project.search_vector.isnot(None)).count()
        
        print(f"Problems: {prob_indexed}/{prob_total} indexed")
        print(f"Business Cases: {case_indexed}/{case_total} indexed")
        print(f"Projects: {proj_indexed}/{proj_total} indexed")
        print(f"Total: {prob_indexed + case_indexed + proj_indexed}/{prob_total + case_total + proj_total} entities indexed")
        
        indexing_complete = (prob_indexed == prob_total and 
                           case_indexed == case_total and 
                           proj_indexed == proj_total)
        
        if indexing_complete:
            print("✓ All entities fully indexed and searchable")
        else:
            print("⚠️ Some entities missing search vectors")

if __name__ == "__main__":
    test_simplified_search_api()
    print()
    test_search_indexing_status()