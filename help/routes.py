from flask import Blueprint, render_template, abort, request, jsonify
from models import HelpCategory, HelpArticle
import markdown

help_bp = Blueprint('help', __name__, url_prefix='/help')

@help_bp.route('/')
def index():
    """Enhanced Help Center main page with search, filtering, and contextual help handling"""
    # Check if this is a contextual help request
    module = request.args.get('module')
    section = request.args.get('section')
    
    if module and section:
        # Handle contextual help request
        return render_template('help/contextual_content.html', module=module, section=section)
    
    # Enhanced help center with search and filtering
    search_query = request.args.get('search', '').strip()
    module_filter = request.args.get('module', '')
    role_filter = request.args.get('role', '')
    
    # Get all categories and articles
    categories = HelpCategory.query.order_by(HelpCategory.sort_order, HelpCategory.name).all()
    articles_query = HelpArticle.query.join(HelpCategory).order_by(HelpCategory.sort_order, HelpArticle.sort_order, HelpArticle.title)
    
    # Apply filters
    if search_query:
        articles_query = articles_query.filter(
            HelpArticle.title.ilike(f'%{search_query}%') |
            HelpArticle.content.ilike(f'%{search_query}%') |
            HelpArticle.tags.ilike(f'%{search_query}%')
        )
    
    if module_filter:
        articles_query = articles_query.filter(HelpArticle.module_name == module_filter)
    
    if role_filter:
        articles_query = articles_query.filter(HelpArticle.role == role_filter)
    
    articles = articles_query.all()
    
    # Get unique modules for filter dropdown
    modules = list(set([a.module_name for a in HelpArticle.query.all() if a.module_name]))
    modules.sort()
    
    # Add article count to each category
    for category in categories:
        category.article_count = len([a for a in category.articles])
    
    # Check if filters are applied
    has_filters = bool(search_query or module_filter or role_filter)
    
    return render_template('help/enhanced_index.html', 
                         categories=categories, 
                         articles=articles,
                         modules=modules,
                         total_articles=len(articles),
                         search_query=search_query,
                         module_filter=module_filter,
                         role_filter=role_filter,
                         has_filters=has_filters)

@help_bp.route('/<slug>')
def article(slug):
    """Display individual help article"""
    article = HelpArticle.query.filter_by(slug=slug).first_or_404()
    
    # Convert markdown content to HTML
    html_content = markdown.markdown(article.content, extensions=['codehilite', 'fenced_code', 'tables'])
    
    # Check if this is an AJAX request for modal content
    if request.args.get('partial') == '1':
        return jsonify({
            'title': article.title,
            'content': html_content
        })
    
    return render_template('help/article.html', article=article, content=html_content)

@help_bp.route('/category/<int:category_id>')
def category(category_id):
    """Display articles in a specific category"""
    category = HelpCategory.query.get_or_404(category_id)
    articles = HelpArticle.query.filter_by(category_id=category_id).order_by(HelpArticle.sort_order, HelpArticle.title).all()
    
    return render_template('help/category.html', category=category, articles=articles)

@help_bp.route('/contextual')
def contextual():
    """Handle contextual help requests with module and section parameters"""
    module = request.args.get('module', 'General')
    section = request.args.get('section', 'overview')
    
    # Check if this is an AJAX request for modal content
    if request.args.get('partial') == '1':
        return jsonify({
            'title': f'{module} - {section.title()}',
            'module': module,
            'section': section
        })
    
    return render_template('help/contextual_content.html', module=module, section=section)