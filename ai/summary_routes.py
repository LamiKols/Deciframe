"""
AI Summary Generation Routes
Generates executive summaries for business cases
"""

from flask import Blueprint, request, jsonify, current_app
import logging
import os

# Import OpenAI conditionally
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Create blueprint
summary_bp = Blueprint('ai_summary', __name__)

@summary_bp.route('/api/ai/generate-summary', methods=['POST'])
@login_required
def generate_summary():
    """Generate AI-powered executive summary for business case"""
    
    try:
        user = current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Check if AI is available
        if not current_app.config.get('AI_AVAILABLE') or not OPENAI_AVAILABLE:
            # Provide fallback summary
            fallback_summary = generate_fallback_summary(data)
            return jsonify({
                'success': True, 
                'summary': fallback_summary,
                'source': 'fallback'
            })
        
        # Generate AI summary
        openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Create prompt from business case data
        prompt = create_summary_prompt(data)
        
        logging.info(f"Generating AI summary for user {user.id}")
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Latest OpenAI model
            messages=[
                {
                    "role": "system", 
                    "content": "You are a business analyst expert. Generate concise, professional executive summaries for business cases. Focus on key value propositions, benefits, and strategic impact. Keep summaries between 100-200 words."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=300,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        
        logging.info(f"AI summary generated successfully for user {user.id}")
        
        return jsonify({
            'success': True,
            'summary': summary,
            'source': 'openai'
        })
        
    except Exception as e:
        logging.error(f"Error generating AI summary: {str(e)}")
        
        # Provide fallback on any error
        try:
            fallback_summary = generate_fallback_summary(data)
            return jsonify({
                'success': True,
                'summary': fallback_summary,
                'source': 'fallback',
                'note': 'AI temporarily unavailable, generated template summary'
            })
        except Exception as fallback_error:
            logging.error(f"Fallback summary generation failed: {str(fallback_error)}")
            return jsonify({
                'success': False,
                'error': 'Unable to generate summary at this time'
            }), 500

def create_summary_prompt(data):
    """Create a prompt for AI summary generation"""
    
    title = data.get('title', '')
    description = data.get('description', '')
    business_justification = data.get('business_justification', '')
    cost_estimate = data.get('cost_estimate', '')
    benefit_estimate = data.get('benefit_estimate', '')
    case_type = data.get('case_type', '')
    initiative_name = data.get('initiative_name', '')
    
    prompt = f"""
    Generate a professional executive summary for this business case:
    
    Title: {title}
    Type: {case_type}
    Initiative: {initiative_name}
    
    Description: {description}
    
    Business Justification: {business_justification}
    
    Financial Overview:
    - Estimated Cost: ${cost_estimate}
    - Estimated Benefit: ${benefit_estimate}
    
    Please create a concise executive summary that highlights:
    1. The business problem or opportunity
    2. The proposed solution approach
    3. Key financial benefits and ROI potential
    4. Strategic value to the organization
    
    Keep the summary professional, actionable, and between 100-200 words.
    """
    
    return prompt

def generate_fallback_summary(data):
    """Generate a template-based summary when AI is unavailable"""
    
    title = data.get('title', 'Business Initiative')
    case_type = data.get('case_type', 'Business Case')
    cost_estimate = data.get('cost_estimate', '0')
    benefit_estimate = data.get('benefit_estimate', '0')
    
    # Calculate ROI if possible
    roi_text = ""
    try:
        cost = float(cost_estimate) if cost_estimate else 0
        benefit = float(benefit_estimate) if benefit_estimate else 0
        if cost > 0:
            roi = ((benefit - cost) / cost) * 100
            roi_text = f" with an estimated ROI of {roi:.1f}%"
    except:
        pass
    
    summary = f"""
    This {case_type.lower()} case presents "{title}" as a strategic initiative requiring organizational investment. 
    
    The proposed solution addresses key business requirements while delivering measurable value to stakeholders. 
    With an estimated investment of ${cost_estimate:,} and projected benefits of ${benefit_estimate:,}{roi_text}, 
    this initiative aligns with organizational priorities and supports long-term growth objectives.
    
    Implementation will require careful planning, stakeholder coordination, and phased execution to ensure 
    successful delivery and realization of anticipated benefits. Regular monitoring and evaluation will 
    track progress against defined success metrics and business outcomes.
    """.strip()
    
    return summary