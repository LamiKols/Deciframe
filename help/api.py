"""
Help Center REST API
Provides comprehensive API endpoints for help articles management
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from models import HelpArticle, HelpCategory, HelpArticleRoleEnum, db
from datetime import datetime
import markdown

help_api_bp = Blueprint('help_api', __name__, url_prefix='/api/help-articles')

@help_api_bp.route('', methods=['GET'])
def list_articles():
    """
    GET /api/help-articles – list/search articles (by module, tag, or role)
    Query parameters:
    - module: filter by module_name
    - tag: filter by tag
    - role: filter by role (admin, user, both)
    - search: search in title and content
    - category_id: filter by category
    - organization_id: filter by organization (admin only)
    """
    try:
        # Base query - filter by organization
        if current_user.is_authenticated:
            query = HelpArticle.query.filter_by(organization_id=current_user.organization_id)
        else:
            # Public access - return empty for now (can be modified for public help)
            return jsonify({'articles': [], 'total': 0})
        
        # Apply filters
        module = request.args.get('module')
        if module:
            query = query.filter(HelpArticle.module_name == module)
        
        tag = request.args.get('tag')
        if tag:
            query = query.filter(HelpArticle.tags.contains(tag))
        
        role = request.args.get('role')
        if role and role in ['admin', 'user', 'both']:
            if role == 'both':
                # Show articles for both or specifically 'both'
                query = query.filter(or_(
                    HelpArticle.role == HelpArticleRoleEnum.both,
                    HelpArticle.role == getattr(HelpArticleRoleEnum, current_user.role.value.lower(), HelpArticleRoleEnum.both)
                ))
            else:
                query = query.filter(or_(
                    HelpArticle.role == HelpArticleRoleEnum.both,
                    HelpArticle.role == getattr(HelpArticleRoleEnum, role)
                ))
        
        # Role-based filtering for current user
        if current_user.is_authenticated:
            user_role = current_user.role.value.lower()
            if user_role not in ['admin', 'ceo', 'director']:
                # Non-admin users can only see 'user' and 'both' articles
                query = query.filter(or_(
                    HelpArticle.role == HelpArticleRoleEnum.user,
                    HelpArticle.role == HelpArticleRoleEnum.both
                ))
        
        category_id = request.args.get('category_id')
        if category_id:
            query = query.filter(HelpArticle.category_id == int(category_id))
        
        search = request.args.get('search')
        if search:
            search_term = f"%{search}%"
            query = query.filter(or_(
                HelpArticle.title.ilike(search_term),
                HelpArticle.content.ilike(search_term),
                HelpArticle.tags.ilike(search_term)
            ))
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 100)  # Limit to 100 items per page
        
        # Order by sort_order, then by title
        query = query.order_by(HelpArticle.sort_order, HelpArticle.title)
        
        # Execute query with pagination
        paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        articles = [article.to_dict() for article in paginated.items]
        
        return jsonify({
            'articles': articles,
            'total': paginated.total,
            'page': page,
            'per_page': per_page,
            'pages': paginated.pages,
            'has_next': paginated.has_next,
            'has_prev': paginated.has_prev
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing help articles: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@help_api_bp.route('/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """GET /api/help-articles/<id> – get full article"""
    try:
        if current_user.is_authenticated:
            article = HelpArticle.query.filter_by(
                id=article_id,
                organization_id=current_user.organization_id
            ).first()
        else:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Check role permissions
        if current_user.is_authenticated:
            user_role = current_user.role.value.lower()
            if article.role == HelpArticleRoleEnum.admin and user_role not in ['admin', 'ceo', 'director']:
                return jsonify({'error': 'Access denied'}), 403
        
        # Increment view count
        article.increment_view_count()
        
        # Convert markdown to HTML if needed
        article_data = article.to_dict()
        if article.content:
            article_data['content_html'] = markdown.markdown(
                article.content, 
                extensions=['codehilite', 'fenced_code', 'tables', 'toc']
            )
        
        return jsonify(article_data)
        
    except Exception as e:
        current_app.logger.error(f"Error getting help article {article_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@help_api_bp.route('', methods=['POST'])
@login_required
def create_article():
    """POST /api/help-articles – create article (admin only)"""
    try:
        # Check admin permissions
        if current_user.role.value not in ['Admin', 'CEO', 'Director']:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        # Validate required fields
        required_fields = ['title', 'content', 'category_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate category exists and belongs to organization
        category = HelpCategory.query.filter_by(
            id=data['category_id'],
            organization_id=current_user.organization_id
        ).first()
        if not category:
            return jsonify({'error': 'Invalid category'}), 400
        
        # Validate role
        role = data.get('role', 'both')
        if role not in ['admin', 'user', 'both']:
            return jsonify({'error': 'Invalid role. Must be admin, user, or both'}), 400
        
        # Create article
        article = HelpArticle(
            organization_id=current_user.organization_id,
            category_id=data['category_id'],
            module_name=data.get('module_name'),
            title=data['title'],
            content=data['content'],
            role=getattr(HelpArticleRoleEnum, role),
            tags=','.join(data.get('tags', [])) if data.get('tags') else None,
            faq=data.get('faq', []),
            sort_order=data.get('sort_order', 0),
            created_by=current_user.id
        )
        
        # Generate slug
        article.slug = article.generate_slug()
        
        db.session.add(article)
        db.session.commit()
        
        return jsonify(article.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating help article: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@help_api_bp.route('/<int:article_id>', methods=['PUT'])
@login_required
def update_article(article_id):
    """PUT /api/help-articles/<id> – update article (admin only)"""
    try:
        # Check admin permissions
        if current_user.role.value not in ['Admin', 'CEO', 'Director']:
            return jsonify({'error': 'Admin access required'}), 403
        
        article = HelpArticle.query.filter_by(
            id=article_id,
            organization_id=current_user.organization_id
        ).first()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        # Update fields
        if 'title' in data:
            old_title = article.title
            article.title = data['title']
            if old_title != article.title:
                article.slug = article.generate_slug()
        
        if 'content' in data:
            article.content = data['content']
        
        if 'module_name' in data:
            article.module_name = data['module_name']
        
        if 'role' in data:
            if data['role'] not in ['admin', 'user', 'both']:
                return jsonify({'error': 'Invalid role'}), 400
            article.role = getattr(HelpArticleRoleEnum, data['role'])
        
        if 'tags' in data:
            article.tags = ','.join(data['tags']) if data['tags'] else None
        
        if 'faq' in data:
            article.faq = data['faq']
        
        if 'sort_order' in data:
            article.sort_order = data['sort_order']
        
        if 'category_id' in data:
            category = HelpCategory.query.filter_by(
                id=data['category_id'],
                organization_id=current_user.organization_id
            ).first()
            if not category:
                return jsonify({'error': 'Invalid category'}), 400
            article.category_id = data['category_id']
        
        article.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(article.to_dict())
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating help article {article_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@help_api_bp.route('/<int:article_id>', methods=['DELETE'])
@login_required
def delete_article(article_id):
    """DELETE /api/help-articles/<id> – delete article (admin only)"""
    try:
        # Check admin permissions
        if current_user.role.value not in ['Admin', 'CEO', 'Director']:
            return jsonify({'error': 'Admin access required'}), 403
        
        article = HelpArticle.query.filter_by(
            id=article_id,
            organization_id=current_user.organization_id
        ).first()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        article_title = article.title
        db.session.delete(article)
        db.session.commit()
        
        return jsonify({
            'message': f'Article "{article_title}" deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting help article {article_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@help_api_bp.route('/<int:article_id>/feedback', methods=['POST'])
@login_required
def record_feedback(article_id):
    """POST /api/help-articles/<id>/feedback – record article feedback"""
    try:
        article = HelpArticle.query.filter_by(
            id=article_id,
            organization_id=current_user.organization_id
        ).first()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        data = request.get_json()
        if not data or 'helpful' not in data:
            return jsonify({'error': 'helpful field required (true/false)'}), 400
        
        article.record_feedback(helpful=data['helpful'])
        
        return jsonify({
            'message': 'Feedback recorded',
            'helpful_count': article.helpful_count,
            'not_helpful_count': article.not_helpful_count
        })
        
    except Exception as e:
        current_app.logger.error(f"Error recording feedback for article {article_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@help_api_bp.route('/modules', methods=['GET'])
def get_modules():
    """GET /api/help-articles/modules – get list of available modules"""
    try:
        if current_user.is_authenticated:
            modules = db.session.query(HelpArticle.module_name).filter(
                HelpArticle.organization_id == current_user.organization_id,
                HelpArticle.module_name.isnot(None)
            ).distinct().all()
        else:
            return jsonify({'modules': []})
        
        module_list = [module[0] for module in modules if module[0]]
        
        return jsonify({'modules': sorted(module_list)})
        
    except Exception as e:
        current_app.logger.error(f"Error getting modules: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@help_api_bp.route('/analytics', methods=['GET'])
@login_required
def get_analytics():
    """GET /api/help-articles/analytics – get help center analytics (admin only)"""
    try:
        # Check admin permissions
        if current_user.role.value not in ['Admin', 'CEO', 'Director']:
            return jsonify({'error': 'Admin access required'}), 403
        
        # Top viewed articles
        top_viewed = HelpArticle.query.filter_by(
            organization_id=current_user.organization_id
        ).order_by(HelpArticle.view_count.desc()).limit(10).all()
        
        # Top helpful articles
        top_helpful = HelpArticle.query.filter_by(
            organization_id=current_user.organization_id
        ).order_by(HelpArticle.helpful_count.desc()).limit(10).all()
        
        # Total stats
        total_articles = HelpArticle.query.filter_by(
            organization_id=current_user.organization_id
        ).count()
        
        total_views = db.session.query(db.func.sum(HelpArticle.view_count)).filter_by(
            organization_id=current_user.organization_id
        ).scalar() or 0
        
        return jsonify({
            'total_articles': total_articles,
            'total_views': total_views,
            'top_viewed': [
                {
                    'id': article.id,
                    'title': article.title,
                    'view_count': article.view_count,
                    'module_name': article.module_name
                } for article in top_viewed
            ],
            'top_helpful': [
                {
                    'id': article.id,
                    'title': article.title,
                    'helpful_count': article.helpful_count,
                    'not_helpful_count': article.not_helpful_count,
                    'module_name': article.module_name
                } for article in top_helpful
            ]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting help analytics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500