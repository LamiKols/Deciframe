"""
AI Review Insights for DeciFrame
Provides approval confidence scoring and risk assessment for business cases, epics, and projects
"""

import os
import openai
import re
from typing import Dict, Optional, List

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_ai_review_insights(content_type: str, title: str, description: str, 
                          cost: Optional[float] = None, benefit: Optional[float] = None,
                          additional_context: str = "") -> Dict[str, any]:
    """
    Get AI-powered review insights including confidence score and risk assessment
    
    Args:
        content_type: Type of content being reviewed (business case, epic, project)
        title: Title of the item
        description: Description/details
        cost: Estimated cost (optional)
        benefit: Expected benefit (optional)
        additional_context: Additional context for analysis
    
    Returns:
        Dict containing confidence_score, risks, and raw_output
    """
    
    # Build the prompt with available information
    cost_info = f"Estimated Cost: ${cost:,.2f}" if cost else "Estimated Cost: Not specified"
    benefit_info = f"Expected Benefit: ${benefit:,.2f}" if benefit else "Expected Benefit: Not specified"
    
    prompt = f"""You are an expert enterprise solution evaluator with 20+ years of experience reviewing {content_type}s for approval.

Analyze this {content_type} for approval readiness and provide structured insights:

Title: {title}
Description: {description}
{cost_info}
{benefit_info}
{f"Additional Context: {additional_context}" if additional_context else ""}

Please provide your analysis in the following exact format:

CONFIDENCE SCORE: [number]%

TOP RISKS:
- [Risk 1 with brief explanation]
- [Risk 2 with brief explanation] 
- [Risk 3 with brief explanation]

APPROVAL RECOMMENDATION:
[Brief recommendation with key factors]

Focus on business viability, implementation feasibility, resource requirements, and strategic alignment."""

    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert enterprise solution evaluator. Provide structured, actionable insights for business decision makers."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        raw_output = response.choices[0].message.content
        
        # Parse the structured response
        confidence_score = _extract_confidence_score(raw_output)
        risks = _extract_risks(raw_output)
        recommendation = _extract_recommendation(raw_output)
        
        return {
            "confidence_score": confidence_score,
            "risks": risks,
            "recommendation": recommendation,
            "raw_output": raw_output,
            "success": True
        }
        
    except Exception as e:
        return {
            "confidence_score": None,
            "risks": [],
            "recommendation": "AI analysis unavailable",
            "raw_output": f"Error generating AI insights: {str(e)}",
            "success": False,
            "error": str(e)
        }

def _extract_confidence_score(text: str) -> Optional[int]:
    """Extract confidence score from AI response"""
    match = re.search(r'CONFIDENCE SCORE:\s*(\d+)%', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def _extract_risks(text: str) -> List[str]:
    """Extract risk list from AI response"""
    risks = []
    
    # Find the TOP RISKS section
    risks_match = re.search(r'TOP RISKS:\s*(.*?)(?=\n[A-Z]|\Z)', text, re.DOTALL | re.IGNORECASE)
    if risks_match:
        risks_text = risks_match.group(1)
        # Extract bullet points
        risk_lines = re.findall(r'-\s*(.+)', risks_text)
        risks = [risk.strip() for risk in risk_lines if risk.strip()]
    
    return risks

def _extract_recommendation(text: str) -> str:
    """Extract approval recommendation from AI response"""
    match = re.search(r'APPROVAL RECOMMENDATION:\s*(.*?)(?=\Z)', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "No specific recommendation provided"

def get_confidence_badge_class(score: Optional[int]) -> str:
    """Get Bootstrap badge class based on confidence score"""
    if score is None:
        return "bg-secondary"
    elif score >= 80:
        return "bg-success"
    elif score >= 60:
        return "bg-warning"
    else:
        return "bg-danger"

def get_confidence_label(score: Optional[int]) -> str:
    """Get human-readable confidence label"""
    if score is None:
        return "Unknown"
    elif score >= 80:
        return "High Confidence"
    elif score >= 60:
        return "Medium Confidence"
    else:
        return "Low Confidence"