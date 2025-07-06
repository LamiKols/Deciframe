"""
Full-Text Search Service for DeciFrame
PostgreSQL tsvector-powered search across Problems, Business Cases, and Projects
"""

from sqlalchemy import text, func
from flask import current_app
from app import db
from models import Problem, BusinessCase, Project, User, Department
import logging

logger = logging.getLogger(__name__)

class SearchService:
    """Service class for full-text search operations"""
    
    @staticmethod
    def search_problems(query, limit=20, user_id=None, department_id=None):
        """
        Search problems using PostgreSQL full-text search
        Args:
            query: Search query string
            limit: Maximum results to return
            user_id: Filter by user (optional)
            department_id: Filter by department (optional)
        """
        try:
            # Build the search query
            search_query = SearchService._prepare_search_query(query)
            
            # Base query with search vector matching
            sql_query = text("""
                SELECT p.*, 
                       u.name as reporter_name,
                       d.name as department_name,
                       ts_rank(p.search_vector, query) as rank
                FROM problems p
                LEFT JOIN users u ON p.reported_by = u.id
                LEFT JOIN departments d ON p.department_id = d.id,
                to_tsquery('english', :search_query) query
                WHERE p.search_vector @@ query
                ORDER BY rank DESC, p.created_at DESC
                LIMIT :limit
            """)
            
            result = db.session.execute(sql_query, {
                'search_query': search_query,
                'limit': limit
            }).fetchall()
            
            return [{
                'id': row.id,
                'code': row.code,
                'title': row.title,
                'description': row.description,
                'status': row.status if hasattr(row.status, 'value') else str(row.status) if row.status else None,
                'priority': row.priority if hasattr(row.priority, 'value') else str(row.priority) if row.priority else None,
                'reporter_name': row.reporter_name,
                'department_name': row.department_name,
                'created_at': row.created_at,
                'rank': float(row.rank),
                'type': 'problem'
            } for row in result]
            
        except Exception as e:
            logger.error(f"Error searching problems: {e}")
            return []
    
    @staticmethod
    def search_business_cases(query, limit=20, user_id=None, department_id=None):
        """Search business cases using PostgreSQL full-text search"""
        try:
            search_query = SearchService._prepare_search_query(query)
            
            sql_query = text("""
                SELECT bc.*, 
                       u.name as creator_name,
                       d.name as department_name,
                       ts_rank(bc.search_vector, query) as rank
                FROM business_cases bc
                LEFT JOIN users u ON bc.created_by = u.id
                LEFT JOIN departments d ON bc.dept_id = d.id,
                to_tsquery('english', :search_query) query
                WHERE bc.search_vector @@ query
                ORDER BY rank DESC, bc.created_at DESC
                LIMIT :limit
            """)
            
            result = db.session.execute(sql_query, {
                'search_query': search_query,
                'limit': limit
            }).fetchall()
            
            return [{
                'id': row.id,
                'code': row.code,
                'title': row.title,
                'description': row.description,
                'summary': row.summary,
                'status': row.status if hasattr(row.status, 'value') else str(row.status) if row.status else None,
                'case_type': row.case_type if hasattr(row.case_type, 'value') else str(row.case_type) if row.case_type else None,
                'cost_estimate': row.cost_estimate,
                'benefit_estimate': row.benefit_estimate,
                'roi': row.roi,
                'creator_name': row.creator_name,
                'department_name': row.department_name,
                'created_at': row.created_at,
                'rank': float(row.rank),
                'type': 'business_case'
            } for row in result]
            
        except Exception as e:
            logger.error(f"Error searching business cases: {e}")
            return []
    
    @staticmethod
    def search_projects(query, limit=20, user_id=None, department_id=None):
        """Search projects using PostgreSQL full-text search"""
        try:
            search_query = SearchService._prepare_search_query(query)
            
            sql_query = text("""
                SELECT p.*, 
                       u.name as manager_name,
                       d.name as department_name,
                       ts_rank(p.search_vector, query) as rank
                FROM projects p
                LEFT JOIN users u ON p.project_manager_id = u.id
                LEFT JOIN departments d ON p.department_id = d.id,
                to_tsquery('english', :search_query) query
                WHERE p.search_vector @@ query
                ORDER BY rank DESC, p.created_at DESC
                LIMIT :limit
            """)
            
            result = db.session.execute(sql_query, {
                'search_query': search_query,
                'limit': limit
            }).fetchall()
            
            return [{
                'id': row.id,
                'code': row.code,
                'name': row.name,
                'description': row.description,
                'status': row.status if hasattr(row.status, 'value') else str(row.status) if row.status else None,
                'priority': row.priority if hasattr(row.priority, 'value') else str(row.priority) if row.priority else None,
                'budget': row.budget,
                'start_date': row.start_date,
                'end_date': row.end_date,
                'manager_name': row.manager_name,
                'department_name': row.department_name,
                'created_at': row.created_at,
                'rank': float(row.rank),
                'type': 'project'
            } for row in result]
            
        except Exception as e:
            logger.error(f"Error searching projects: {e}")
            return []
    
    @staticmethod
    def search_all(query, limit=20, user_id=None, department_id=None):
        """
        Search across all entities (problems, business cases, projects)
        Returns combined results sorted by relevance
        """
        try:
            # Get results from each entity type
            problems = SearchService.search_problems(query, limit//3, user_id, department_id)
            business_cases = SearchService.search_business_cases(query, limit//3, user_id, department_id)
            projects = SearchService.search_projects(query, limit//3, user_id, department_id)
            
            # Combine and sort by rank
            all_results = problems + business_cases + projects
            all_results.sort(key=lambda x: x['rank'], reverse=True)
            
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"Error in unified search: {e}")
            return []
    
    @staticmethod
    def search_suggestions(query, limit=5):
        """
        Get search suggestions based on existing titles and descriptions
        """
        try:
            search_query = SearchService._prepare_search_query(query)
            
            sql_query = text("""
                (SELECT title as suggestion, 'problem' as type FROM problems 
                 WHERE title ILIKE :partial_query LIMIT :limit)
                UNION ALL
                (SELECT title as suggestion, 'business_case' as type FROM business_cases 
                 WHERE title ILIKE :partial_query LIMIT :limit)
                UNION ALL
                (SELECT name as suggestion, 'project' as type FROM projects 
                 WHERE name ILIKE :partial_query LIMIT :limit)
                ORDER BY suggestion
                LIMIT :total_limit
            """)
            
            result = db.session.execute(sql_query, {
                'partial_query': f'%{query}%',
                'limit': limit,
                'total_limit': limit * 3
            }).fetchall()
            
            return [{'suggestion': row.suggestion, 'type': row.type} for row in result]
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []
    
    @staticmethod
    def _prepare_search_query(query):
        """
        Prepare search query for PostgreSQL to_tsquery
        Handles special characters and creates proper tsquery format
        """
        if not query or not query.strip():
            return ''
        
        # Clean the query
        query = query.strip()
        
        # Replace common separators with spaces
        query = query.replace(',', ' ').replace('.', ' ').replace('!', ' ').replace('?', ' ')
        
        # Split into words and filter out empty strings
        words = [word.strip() for word in query.split() if word.strip()]
        
        if not words:
            return ''
        
        # Join words with OR operator for broader matching
        return ' | '.join(words)
    
    @staticmethod
    def get_search_stats():
        """Get statistics about searchable content"""
        try:
            stats_query = text("""
                SELECT 
                    (SELECT COUNT(*) FROM problems WHERE search_vector IS NOT NULL) as problems_indexed,
                    (SELECT COUNT(*) FROM business_cases WHERE search_vector IS NOT NULL) as cases_indexed,
                    (SELECT COUNT(*) FROM projects WHERE search_vector IS NOT NULL) as projects_indexed,
                    (SELECT COUNT(*) FROM problems) as total_problems,
                    (SELECT COUNT(*) FROM business_cases) as total_cases,
                    (SELECT COUNT(*) FROM projects) as total_projects
            """)
            
            result = db.session.execute(stats_query).fetchone()
            
            return {
                'problems_indexed': result.problems_indexed,
                'cases_indexed': result.cases_indexed,
                'projects_indexed': result.projects_indexed,
                'total_problems': result.total_problems,
                'total_cases': result.total_cases,
                'total_projects': result.total_projects,
                'indexing_complete': (
                    result.problems_indexed == result.total_problems and
                    result.cases_indexed == result.total_cases and
                    result.projects_indexed == result.total_projects
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting search stats: {e}")
            return {
                'problems_indexed': 0,
                'cases_indexed': 0,
                'projects_indexed': 0,
                'total_problems': 0,
                'total_cases': 0,
                'total_projects': 0,
                'indexing_complete': False
            }