#!/usr/bin/env python3
"""
Debug script to test search functionality for 'automation' query
"""

from app import app, db
from models import Problem, BusinessCase, Project
from sqlalchemy import func, text
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_search_automation():
    """Test search for automation across all entities"""
    with app.app_context():
        print("=== Testing Search for 'automation' ===")
        
        # Test 1: Direct SQL query with search vectors
        print("\n1. Testing direct SQL with search vectors:")
        sql_query = text("""
            SELECT id, title, ts_rank(search_vector, query) as rank
            FROM business_cases,
            to_tsquery('english', 'automation') query
            WHERE search_vector @@ query
            ORDER BY rank DESC
            LIMIT 5
        """)
        
        results = db.session.execute(sql_query).fetchall()
        print(f"Found {len(results)} business cases with direct SQL:")
        for row in results:
            print(f"  ID: {row.id}, Title: {row.title}, Rank: {row.rank}")
        
        # Test 2: SQLAlchemy with plainto_tsquery
        print("\n2. Testing SQLAlchemy with plainto_tsquery:")
        tsq = func.plainto_tsquery('english', 'automation')
        
        business_cases = BusinessCase.query\
            .filter(BusinessCase.search_vector.op('@@')(tsq))\
            .add_columns(func.ts_rank(BusinessCase.search_vector, tsq).label('rank'))\
            .order_by(func.ts_rank(BusinessCase.search_vector, tsq).desc())\
            .limit(10).all()
        
        print(f"Found {len(business_cases)} business cases with SQLAlchemy:")
        for item in business_cases:
            if isinstance(item, tuple) and len(item) == 2:
                obj, rank = item
                print(f"  ID: {obj.id}, Title: {obj.title}, Rank: {rank}")
        
        # Test 3: Simple ILIKE search as fallback
        print("\n3. Testing simple ILIKE search:")
        simple_results = BusinessCase.query\
            .filter(BusinessCase.title.ilike('%automation%'))\
            .all()
        
        print(f"Found {len(simple_results)} business cases with ILIKE:")
        for case in simple_results:
            print(f"  ID: {case.id}, Title: {case.title}")
        
        # Test 4: Check if search vectors exist
        print("\n4. Checking search vector status:")
        vector_check = db.session.execute(text("""
            SELECT COUNT(*) as total_cases,
                   COUNT(CASE WHEN search_vector IS NOT NULL THEN 1 END) as with_vectors
            FROM business_cases
        """)).fetchone()
        
        print(f"Total business cases: {vector_check.total_cases}")
        print(f"Cases with search vectors: {vector_check.with_vectors}")
        
        # Test 5: Manual tsquery test
        print("\n5. Testing manual tsquery:")
        manual_query = text("""
            SELECT 'automation'::text, 
                   to_tsquery('english', 'automation'),
                   plainto_tsquery('english', 'automation')
        """)
        
        query_result = db.session.execute(manual_query).fetchone()
        print(f"Raw query: {query_result[0]}")
        print(f"to_tsquery result: {query_result[1]}")
        print(f"plainto_tsquery result: {query_result[2]}")

if __name__ == '__main__':
    test_search_automation()