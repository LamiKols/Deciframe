from flask import Blueprint, render_template, abort, request, jsonify
from models import HelpCategory, HelpArticle
import markdown

help_bp = Blueprint('help', __name__, url_prefix='/help')

@help_bp.route('/')
def index():
    """Help Center main page with category listing"""
    categories = HelpCategory.query.order_by(HelpCategory.sort_order, HelpCategory.name).all()
    
    # Add article count to each category
    for category in categories:
        category.article_count = len([a for a in category.articles])
    
    return render_template('help/index.html', categories=categories)

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