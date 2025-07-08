"""
Simplified Search API Routes using SQLAlchemy tsvector operators
Clean implementation with plainto_tsquery for natural language queries
"""

from flask import Blueprint, request, jsonify
from auth.session_auth import require_session_auth
from models import Problem, BusinessCase, Project, HelpArticle
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

search_api_bp = Blueprint('search_api', __name__, url_prefix='/api/search')

@search_api_bp.route('/', methods=['GET'])
@require_session_auth
def global_search():
    """Global search across all entities using PostgreSQL tsvector"""
    q = request.args.get('q', '').strip()
    logger.info(f"🔍 Search query received: '{q}'")
    
    if not q:
        return jsonify(results=[])
    
    try:
        # Use plainto_tsquery for natural language query processing
        tsq = func.plainto_tsquery('english', q)
        logger.info(f"🔍 PostgreSQL tsquery generated for: '{q}'")
        
        # Search across all entity types with relevance ranking
        problems = Problem.query\
            .filter(Problem.search_vector.op('@@')(tsq))\
            .add_columns(func.ts_rank(Problem.search_vector, tsq).label('rank'))\
            .order_by(func.ts_rank(Problem.search_vector, tsq).desc())\
            .limit(10).all()
        logger.info(f"🔍 Problems found: {len(problems)}")
        
        business_cases = BusinessCase.query\
            .filter(BusinessCase.search_vector.op('@@')(tsq))\
            .add_columns(func.ts_rank(BusinessCase.search_vector, tsq).label('rank'))\
            .order_by(func.ts_rank(BusinessCase.search_vector, tsq).desc())\
            .limit(10).all()
        logger.info(f"🔍 Business cases found: {len(business_cases)}")
        
        projects = Project.query\
            .filter(Project.search_vector.op('@@')(tsq))\
            .add_columns(func.ts_rank(Project.search_vector, tsq).label('rank'))\
            .order_by(func.ts_rank(Project.search_vector, tsq).desc())\
            .limit(10).all()
        logger.info(f"🔍 Projects found: {len(projects)}")
        
        # Add Help articles using simple text search (no search_vector needed)
        help_articles = []
        if query:
            from sqlalchemy import or_
            help_query = HelpArticle.query.filter(
                or_(
                    HelpArticle.title.ilike(f'%{query}%'),
                    HelpArticle.content.ilike(f'%{query}%')
                )
            ).limit(5).all()
            # Convert to same format as other results (entity, rank)
            help_articles = [(article, 0.5) for article in help_query]  # Default rank for text search
        logger.info(f"🔍 Help articles found: {len(help_articles)}")
        
        def to_dict(item):
            # Handle SQLAlchemy query results with rank
            if hasattr(item, '_fields'):  # SQLAlchemy Row object
                # Row object has attributes accessible by index or name
                obj = item[0]  # First column is the entity
                rank = item[1] if len(item) > 1 else 0  # Second column is rank
            elif isinstance(item, tuple) and len(item) == 2:
                obj, rank = item
            else:
                obj = item
                rank = 0
            
            # Safely get object attributes
            try:
                entity_id = getattr(obj, 'id', None)
                if entity_id is None:
                    logger.error(f"🔍 No ID found for object: {type(obj)}")
                    return None
                
                logger.debug(f"🔍 Processing entity {entity_id} of type {type(obj)}")
                
                # Map entity types properly
                entity_type = 'unknown'
                if hasattr(obj, '__class__'):
                    class_name = obj.__class__.__name__
                    if class_name == 'Problem':
                        entity_type = 'problems'
                    elif class_name == 'BusinessCase':
                        entity_type = 'business_cases'
                    elif class_name == 'Project':
                        entity_type = 'projects'
                    elif class_name == 'HelpArticle':
                        entity_type = 'help_articles'
                
                title = getattr(obj, 'title', getattr(obj, 'name', ''))
                description = getattr(obj, 'description', '')
                if description and len(description) > 200:
                    description = description[:200] + '...'
                
                return {
                    'type': entity_type,
                    'id': entity_id,
                    'title': title,
                    'code': getattr(obj, 'code', ''),
                    'description': description,
                    'rank': float(rank) if rank else 0,
                    'url': _get_entity_url(obj)
                }
            except Exception as e:
                logger.error(f"Error processing search result: {e}")
                logger.error(f"Object details: type={type(obj)}, id={getattr(obj, 'id', 'None')}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return None
        
        # Combine results and sort by relevance, filtering out None values
        all_results = []
        for result_list, list_name in [(problems, 'problems'), (business_cases, 'business_cases'), (projects, 'projects'), (help_articles, 'help_articles')]:
            mapped_results = [to_dict(item) for item in result_list]
            valid_results = [r for r in mapped_results if r is not None]
            logger.info(f"🔍 {list_name}: {len(result_list)} raw → {len(valid_results)} processed")
            all_results.extend(valid_results)
        
        all_results.sort(key=lambda x: x['rank'], reverse=True)
        
        response_data = {
            'query': q,
            'total': len(all_results),
            'results': all_results[:20]  # Limit to top 20 results
        }
        logger.info(f"🔍 Returning {len(response_data['results'])} results to frontend")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({
            'error': 'Search failed',
            'results': []
        }), 500

@search_api_bp.route('/suggestions', methods=['GET'])
@require_session_auth
def search_suggestions():
    """Get search suggestions for autocomplete"""
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify(suggestions=[])
    
    try:
        # Simple ILIKE search for suggestions
        suggestions = []
        
        # Get problem titles
        problem_suggestions = Problem.query\
            .filter(Problem.title.ilike(f'%{q}%'))\
            .with_entities(Problem.title)\
            .limit(5).all()
        suggestions.extend([{'text': p.title, 'type': 'problem'} for p in problem_suggestions])
        
        # Get business case titles
        case_suggestions = BusinessCase.query\
            .filter(BusinessCase.title.ilike(f'%{q}%'))\
            .with_entities(BusinessCase.title)\
            .limit(5).all()
        suggestions.extend([{'text': c.title, 'type': 'business_case'} for c in case_suggestions])
        
        # Get project names
        project_suggestions = Project.query\
            .filter(Project.name.ilike(f'%{q}%'))\
            .with_entities(Project.name)\
            .limit(5).all()
        suggestions.extend([{'text': p.name, 'type': 'project'} for p in project_suggestions])
        
        return jsonify({
            'query': q,
            'suggestions': suggestions[:10]
        })
        
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        return jsonify(suggestions=[])

@search_api_bp.route('/stats', methods=['GET'])
@require_session_auth
def search_stats():
    """Get search indexing statistics"""
    try:
        stats = {
            'problems_total': Problem.query.count(),
            'problems_indexed': Problem.query.filter(Problem.search_vector.isnot(None)).count(),
            'cases_total': BusinessCase.query.count(),
            'cases_indexed': BusinessCase.query.filter(BusinessCase.search_vector.isnot(None)).count(),
            'projects_total': Project.query.count(),
            'projects_indexed': Project.query.filter(Project.search_vector.isnot(None)).count()
        }
        
        stats['total_indexed'] = stats['problems_indexed'] + stats['cases_indexed'] + stats['projects_indexed']
        stats['total_entities'] = stats['problems_total'] + stats['cases_total'] + stats['projects_total']
        stats['indexing_complete'] = (stats['total_indexed'] == stats['total_entities'])
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': 'Unable to retrieve statistics'}), 500

def _get_entity_url(obj):
    """Generate URL for entity based on type"""
    if isinstance(obj, Problem):
        return f"/problems/{obj.id}"
    elif isinstance(obj, BusinessCase):
        return f"/business/cases/{obj.id}"
    elif isinstance(obj, Project):
        return f"/projects/{obj.id}"
    elif isinstance(obj, HelpArticle):
        return f"/help/{obj.slug}"
    return "#"