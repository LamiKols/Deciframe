"""
AI-Powered Problem Classification Service
Analyzes problem titles and descriptions to suggest issue types
"""
import os
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

def classify_problem(title: str, description: str) -> Tuple[str, float]:
    """
    Classify a problem based on title and description
    Returns: (issue_type, confidence_score)
    """
    try:
        from openai import OpenAI
        
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("OpenAI API key not available for problem classification")
            return 'PROCESS', 0.5  # Default fallback
        
        client = OpenAI(api_key=openai_api_key)
        
        # Create classification prompt
        prompt = f"""
Analyze this problem report and classify it into one of these categories:

SYSTEM - Technical issues related to software, hardware, infrastructure, IT systems, networks, databases, applications, or technology failures
PROCESS - Workflow issues, procedural problems, business process inefficiencies, training gaps, policy issues, or organizational challenges  
OTHER - Issues that don't clearly fit into system or process categories, such as external factors, vendor issues, or unclear problems

Problem Title: {title}
Problem Description: {description}

Based on the content, determine:
1. The most appropriate category (SYSTEM, PROCESS, or OTHER)
2. Your confidence level (0.0 to 1.0)

Respond with JSON in this exact format:
{{"issue_type": "SYSTEM", "confidence": 0.85}}
"""

        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert problem classifier for business systems. Provide accurate classifications with confidence scores."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=100,
            temperature=0.1
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        issue_type = result.get('issue_type', 'PROCESS')
        confidence = float(result.get('confidence', 0.5))
        
        # Validate issue type
        if issue_type not in ['SYSTEM', 'PROCESS', 'OTHER']:
            issue_type = 'PROCESS'
            confidence = 0.5
            
        # Ensure confidence is in valid range
        confidence = max(0.0, min(1.0, confidence))
        
        logger.info(f"AI classified problem as {issue_type} with {confidence:.2f} confidence")
        return issue_type, confidence
        
    except Exception as e:
        logger.error(f"Error in AI problem classification: {e}")
        # Return safe default
        return 'PROCESS', 0.5

def get_classification_explanation(issue_type: str) -> str:
    """Get human-readable explanation for issue type"""
    explanations = {
        'SYSTEM': 'Technical or infrastructure-related issue',
        'PROCESS': 'Workflow or procedural issue', 
        'OTHER': 'Issue requiring further analysis'
    }
    return explanations.get(issue_type, 'Unknown issue type')