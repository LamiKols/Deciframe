"""
AI Helper Functions for DeciFrame
Provides OpenAI-powered insights for business reviews and approvals
"""

import os
import logging
from openai import OpenAI

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

logger = logging.getLogger(__name__)

def generate_reviewer_summary(content_type, content_data, additional_context=None):
    """
    Generate AI-powered reviewer insights for business content
    
    Args:
        content_type (str): Type of content ('epic', 'business_case', 'project')
        content_data (dict): Content data including title, description, etc.
        additional_context (dict): Optional additional context for analysis
    
    Returns:
        dict: Contains 'summary', 'considerations', and 'success' status
    """
    if not openai_client:
        return {
            'success': False,
            'error': 'OpenAI API not configured',
            'summary': 'AI reviewer assistant is not available. Please configure OpenAI API key.',
            'considerations': []
        }
    
    try:
        # Build content description based on type
        if content_type == 'epic':
            content_desc = f"""Title: {content_data.get('title', 'N/A')}
Description: {content_data.get('description', 'N/A')}
Status: {content_data.get('status', 'N/A')}
Priority: {content_data.get('priority', 'N/A')}"""
            
        elif content_type == 'business_case':
            content_desc = f"""Title: {content_data.get('title', 'N/A')}
Description: {content_data.get('description', 'N/A')}
Problem Statement: {content_data.get('problem_statement', 'N/A')}
Proposed Solution: {content_data.get('proposed_solution', 'N/A')}
Expected Benefits: {content_data.get('expected_benefits', 'N/A')}
Cost Estimate: {content_data.get('cost_estimate', 'N/A')}
ROI Analysis: {content_data.get('roi_analysis', 'N/A')}"""
            
        elif content_type == 'project':
            content_desc = f"""Name: {content_data.get('name', 'N/A')}
Description: {content_data.get('description', 'N/A')}
Budget: {content_data.get('budget', 'N/A')}
Start Date: {content_data.get('start_date', 'N/A')}
End Date: {content_data.get('end_date', 'N/A')}
Scope: {content_data.get('scope', 'N/A')}"""
        else:
            content_desc = str(content_data)
        
        # Add additional context if provided
        if additional_context:
            context_str = "\n".join([f"{k}: {v}" for k, v in additional_context.items()])
            content_desc += f"\n\nAdditional Context:\n{context_str}"
        
        # Create the prompt
        prompt = f"""You are an expert business analyst and executive reviewer evaluating a submitted {content_type.replace('_', ' ')} for approval.

Content Details:
{content_desc}

Your Task:
1. Provide a concise 2-3 sentence executive summary highlighting the key value proposition and strategic alignment
2. Identify exactly 3 critical factors the reviewing executive should carefully evaluate before approval
3. Focus on business impact, feasibility, risk assessment, and strategic fit

Please respond in this exact format:

EXECUTIVE SUMMARY:
[Your 2-3 sentence summary here]

CRITICAL REVIEW FACTORS:
1. [First critical factor]
2. [Second critical factor] 
3. [Third critical factor]

Keep your response professional, actionable, and focused on executive decision-making."""

        # Call OpenAI API
        # Note: Using gpt-4o as it's the newest model (released May 13, 2024)
        # Do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": "You are an expert business analyst providing executive-level insights for approval decisions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3  # Lower temperature for more consistent business analysis
        )
        
        # Parse the response
        ai_response = response.choices[0].message.content
        
        # Extract summary and considerations
        lines = ai_response.split('\n')
        summary = ""
        considerations = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('EXECUTIVE SUMMARY:'):
                current_section = 'summary'
                continue
            elif line.startswith('CRITICAL REVIEW FACTORS:'):
                current_section = 'considerations'
                continue
            elif line and current_section == 'summary':
                summary += line + " "
            elif line and current_section == 'considerations' and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
                considerations.append(line[2:].strip())  # Remove number prefix
        
        return {
            'success': True,
            'summary': summary.strip(),
            'considerations': considerations,
            'raw_response': ai_response
        }
        
    except Exception as e:
        logger.error(f"Error generating reviewer summary: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'summary': f'AI analysis temporarily unavailable: {str(e)}',
            'considerations': []
        }

def generate_epic_insights(epic):
    """Generate specific insights for Epic review"""
    content_data = {
        'title': epic.title,
        'description': epic.description,
        'status': epic.status if epic.status else 'Unknown',
        'priority': getattr(epic, 'priority', 'Not specified')
    }
    
    # Add business case context if available
    additional_context = {}
    if hasattr(epic, 'business_case') and epic.business_case:
        additional_context['business_case'] = epic.business_case.title
        additional_context['case_description'] = epic.business_case.description[:200] + "..." if len(epic.business_case.description) > 200 else epic.business_case.description
    
    return generate_reviewer_summary('epic', content_data, additional_context)

def generate_business_case_insights(business_case):
    """Generate specific insights for Business Case review"""
    content_data = {
        'title': business_case.title,
        'description': business_case.description,
        'problem_statement': getattr(business_case, 'problem_statement', 'Not specified'),
        'proposed_solution': getattr(business_case, 'proposed_solution', 'Not specified'),
        'expected_benefits': getattr(business_case, 'expected_benefits', 'Not specified'),
        'cost_estimate': getattr(business_case, 'cost_estimate', 'Not specified'),
        'roi_analysis': getattr(business_case, 'roi_analysis', 'Not specified')
    }
    
    # Add problem context if available
    additional_context = {}
    if hasattr(business_case, 'problem') and business_case.problem:
        additional_context['related_problem'] = business_case.problem.title
        additional_context['problem_impact'] = business_case.problem.impact.value if business_case.problem.impact else 'Unknown'
    
    return generate_reviewer_summary('business_case', content_data, additional_context)

def generate_project_insights(project):
    """Generate specific insights for Project review"""
    content_data = {
        'name': project.name,
        'description': project.description,
        'budget': getattr(project, 'budget', 'Not specified'),
        'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else 'Not specified',
        'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else 'Not specified',
        'scope': getattr(project, 'scope', 'Not specified')
    }
    
    # Add business case context if available
    additional_context = {}
    if hasattr(project, 'business_case') and project.business_case:
        additional_context['business_case'] = project.business_case.title
        additional_context['expected_roi'] = getattr(project.business_case, 'roi_analysis', 'Not specified')
    
    return generate_reviewer_summary('project', content_data, additional_context)