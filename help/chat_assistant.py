"""
Help Assistant Chat Widget
Provides intelligent responses to user queries by indexing help article content
"""
import os
from flask import Blueprint, request, jsonify, render_template
from models import HelpArticle, HelpCategory
from openai import OpenAI
import markdown
import re

help_chat_bp = Blueprint('help_chat', __name__, url_prefix='/help/chat')

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def get_indexed_help_content():
    """Get all help articles indexed for LLM processing"""
    articles = HelpArticle.query.join(HelpCategory).order_by(
        HelpCategory.sort_order, HelpArticle.sort_order
    ).all()
    
    indexed_content = []
    for article in articles:
        # Convert markdown to plain text for better LLM processing
        plain_content = markdown.markdown(article.content, extensions=['tables'])
        # Remove HTML tags for cleaner text
        clean_content = re.sub(r'<[^>]+>', '', plain_content)
        clean_content = re.sub(r'\n+', '\n', clean_content).strip()
        
        indexed_content.append({
            'title': article.title,
            'slug': article.slug,
            'category': article.category.name,
            'content': clean_content
        })
    
    return indexed_content

def generate_help_response(user_query, help_content):
    """Generate intelligent response using LLM with indexed help content"""
    if not openai_client:
        return {
            'response': 'I\'m sorry, but the AI assistant is currently unavailable. Please browse the help articles directly or contact support.',
            'relevant_articles': []
        }
    
    # Create context from all help articles
    context = "DeciFrame Help Articles:\n\n"
    for article in help_content:
        context += f"**{article['title']}** (Category: {article['category']})\n"
        context += f"{article['content']}\n\n"
    
    # Create the prompt for intelligent response
    prompt = f"""You are DeciFrame's Help Assistant. Based on the help articles provided, answer the user's question with VERY BRIEF, actionable guidance.

Help Articles Context:
{context}

User Question: {user_query}

IMPORTANT: Keep your response SHORT and use this format:
1. Give a 1-2 sentence direct answer
2. Provide 2-4 numbered steps maximum
3. Each step should be one short line (under 15 words)
4. End with "See the help articles below for more details"

Example good response:
"To assign a BA to a business case:
1. Open the business case details page
2. Click Edit and select a BA from the dropdown
3. Save your changes
See the help articles below for more details."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=[
                {"role": "system", "content": "You are DeciFrame's Help Assistant, providing helpful guidance based on the help documentation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content
        
        # Find relevant articles based on response content
        relevant_articles = []
        for article in help_content:
            if (article['title'].lower() in ai_response.lower() or 
                any(keyword in article['content'].lower() for keyword in user_query.lower().split())):
                relevant_articles.append({
                    'title': article['title'],
                    'slug': article['slug'],
                    'category': article['category']
                })
        
        return {
            'response': ai_response,
            'relevant_articles': relevant_articles[:3]  # Limit to top 3 relevant articles
        }
        
    except Exception as e:
        return {
            'response': 'I encountered an error processing your question. Please try rephrasing your question or browse the help articles directly.',
            'relevant_articles': [],
            'error': str(e)
        }

@help_chat_bp.route('/ask', methods=['POST'])
def ask_assistant():
    """Handle chat queries from the help assistant widget"""
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({
                'error': 'Please provide a question'
            }), 400
        
        # Get indexed help content
        help_content = get_indexed_help_content()
        
        if not help_content:
            return jsonify({
                'response': 'No help articles are currently available. Please contact support for assistance.',
                'relevant_articles': []
            })
        
        # Generate intelligent response
        result = generate_help_response(user_query, help_content)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': 'An error occurred processing your question. Please try again.',
            'details': str(e)
        }), 500

@help_chat_bp.route('/widget')
def widget():
    """Render the help assistant chat widget"""
    return render_template('help/chat_widget.html')

@help_chat_bp.route('/status')
def status():
    """Check help assistant availability status"""
    help_articles_count = HelpArticle.query.count()
    ai_available = bool(OPENAI_API_KEY)
    
    return jsonify({
        'ai_available': ai_available,
        'articles_indexed': help_articles_count,
        'status': 'operational' if ai_available and help_articles_count > 0 else 'limited'
    })