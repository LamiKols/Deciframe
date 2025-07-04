"""
Search Routes for DeciFrame
Full-text search API endpoints and web interface
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from auth.session_auth import require_session_auth, get_current_session_user
from search.search_service import SearchService
import logging

logger = logging.getLogger(__name__)

# Create search blueprint
search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/')
@require_session_auth
def search_page():
    """Main search interface"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    
    results = []
    if query:
        try:
            user = get_current_session_user()
            
            if search_type == 'problems':
                results = SearchService.search_problems(query, limit=20, user_id=user.id)
            elif search_type == 'business_cases':
                results = SearchService.search_business_cases(query, limit=20, user_id=user.id)
            elif search_type == 'projects':
                results = SearchService.search_projects(query, limit=20, user_id=user.id)
            else:
                results = SearchService.search_all(query, limit=20, user_id=user.id)
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            flash("Search temporarily unavailable. Please try again.", "error")
    
    return render_template('search.html', 
                         query=query, 
                         results=results,
                         search_type=search_type,
                         total_results=len(results))

@search_bp.route('/api/search')
@require_session_auth
def api_search():
    """API endpoint for search functionality"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    limit = min(int(request.args.get('limit', 20)), 100)  # Max 100 results
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Query parameter required',
            'results': []
        })
    
    try:
        user = get_current_session_user()
        
        if search_type == 'problems':
            results = SearchService.search_problems(query, limit=limit, user_id=user.id)
        elif search_type == 'business_cases':
            results = SearchService.search_business_cases(query, limit=limit, user_id=user.id)
        elif search_type == 'projects':
            results = SearchService.search_projects(query, limit=limit, user_id=user.id)
        else:
            results = SearchService.search_all(query, limit=limit, user_id=user.id)
        
        return jsonify({
            'success': True,
            'query': query,
            'type': search_type,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"API search error: {e}")
        return jsonify({
            'success': False,
            'error': 'Search failed',
            'results': []
        }), 500

@search_bp.route('/api/suggestions')
@require_session_auth
def api_suggestions():
    """API endpoint for search suggestions"""
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 5)), 20)
    
    if not query or len(query) < 2:
        return jsonify({
            'success': True,
            'suggestions': []
        })
    
    try:
        suggestions = SearchService.search_suggestions(query, limit=limit)
        
        return jsonify({
            'success': True,
            'query': query,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        return jsonify({
            'success': False,
            'suggestions': []
        })

@search_bp.route('/api/stats')
@require_session_auth
def api_stats():
    """API endpoint for search statistics"""
    try:
        stats = SearchService.get_search_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({
            'success': False,
            'error': 'Unable to retrieve search statistics'
        })

# Quick search functionality for navigation bar
@search_bp.route('/quick')
@require_session_auth  
def quick_search():
    """Quick search for navigation bar"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('search.search_page'))
    
    try:
        user = get_current_session_user()
        results = SearchService.search_all(query, limit=5, user_id=user.id)
        
        # If only one result, redirect directly to it
        if len(results) == 1:
            result = results[0]
            if result['type'] == 'problem':
                return redirect(url_for('problems.problem_detail', id=result['id']))
            elif result['type'] == 'business_case':
                return redirect(url_for('business.case_detail', id=result['id']))
            elif result['type'] == 'project':
                return redirect(url_for('projects.project_detail', id=result['id']))
        
        # Otherwise, show search results page
        return redirect(url_for('search.search_page', q=query))
        
    except Exception as e:
        logger.error(f"Quick search error: {e}")
        return redirect(url_for('search.search_page', q=query))

# Admin endpoint for search indexing status
@search_bp.route('/admin/indexing-status')
@require_session_auth
def admin_indexing_status():
    """Admin page for search indexing status"""
    user = get_current_session_user()
    
    if user.role.value not in ['Admin', 'Director', 'CEO']:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for('index'))
    
    try:
        stats = SearchService.get_search_stats()
        
        return render_template('search/admin_status.html', stats=stats)
        
    except Exception as e:
        logger.error(f"Admin status error: {e}")
        flash("Unable to retrieve indexing status.", "error")
        return redirect(url_for('admin.admin_dashboard'))