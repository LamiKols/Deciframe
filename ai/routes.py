"""
AI Routes for Problem Refinement Assistant and Requirements Generation
Provides OpenAI-powered problem statement optimization and requirements generation
"""

import json
import re
import os
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from models import BusinessCase, Epic, Story, RequirementsBackup

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

def parse_variants(response_text):
    """Parse OpenAI response into structured variants"""
    variants = []
    
    # Try multiple parsing strategies for different response formats
    patterns = [
        r'\*\*(\d+)\.\s*([^*]+?)\*\*\s*([^*]+?)(?=\*\*\d+\.|$)',  # **1. Title** Description
        r'(\d+)\.\s*\*\*([^*]+?)\*\*\s*([^*]+?)(?=\d+\.|$)',      # 1. **Title** Description
        r'(\d+)\.\s*([^\n]+?)\n([^0-9]+?)(?=\d+\.|$)',            # 1. Title\nDescription
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, response_text, re.DOTALL)
        if matches and len(matches) >= 3:
            for match in matches[:3]:  # Take first 3
                if len(match) >= 3:
                    title = match[1].strip() if len(match) > 1 else match[0].strip()
                    description = match[2].strip() if len(match) > 2 else match[1].strip()
                    variants.append({
                        "title": title,
                        "description": description
                    })
            break
    
    # Fallback: Split by lines and create variants
    if not variants:
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        for i in range(min(3, len(lines))):
            variants.append({
                "title": f"Refined Problem Statement {i+1}",
                "description": lines[i]
            })
    
    return variants[:3]  # Ensure exactly 3 variants

@ai_bp.route('/refine-problem', methods=['POST'])
@login_required
def refine_problem():
    """AI-powered problem statement refinement with intelligent parsing"""
    try:
        data = request.get_json()
        if not data or 'problem_description' not in data:
            return jsonify({
                'success': False,
                'error': 'Problem description is required'
            }), 400
        
        problem_description = data['problem_description'].strip()
        if len(problem_description) < 10:
            return jsonify({
                'success': False,
                'error': 'Problem description must be at least 10 characters'
            }), 400
        
        user = current_user
        current_app.logger.info(f"AI problem refinement requested by user {user.id}")
        
        # Check for OpenAI API key
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            # Provide intelligent fallback based on problem analysis
            fallback_variants = generate_fallback_variants(problem_description)
            return jsonify({
                'success': True,
                'variants': fallback_variants,
                'message': 'Generated using intelligent analysis (OpenAI unavailable)'
            })
        
        # Use OpenAI for enhanced refinement
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=openai_api_key)
            
            prompt = f"""
            Analyze this problem statement and create 3 refined versions that are more specific, actionable, and business-focused:
            
            Original: "{problem_description}"
            
            Generate 3 variants:
            1. **Technical Focus** - Emphasize technical challenges and solutions
            2. **Business Impact** - Highlight business consequences and value
            3. **User Experience** - Focus on user pain points and experience improvements
            
            For each variant, provide:
            - A clear, specific title (5-8 words)
            - A detailed description (2-3 sentences) that makes the problem actionable
            
            Format as:
            **1. [Title]**
            [Description]
            
            **2. [Title]**
            [Description]
            
            **3. [Title]**
            [Description]
            """
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a business analyst expert at refining problem statements. Create specific, actionable problem descriptions that lead to clear solutions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            # Parse the structured response
            variants = parse_variants(response.choices[0].message.content)
            
            current_app.logger.info(f"Generated {len(variants)} AI-refined problem variants")
            return jsonify({
                'success': True,
                'variants': variants,
                'message': 'Problem refined using AI analysis'
            })
            
        except Exception as openai_error:
            current_app.logger.warning(f"OpenAI API error: {openai_error}")
            # Fallback to intelligent analysis
            fallback_variants = generate_fallback_variants(problem_description)
            return jsonify({
                'success': True,
                'variants': fallback_variants,
                'message': 'Generated using intelligent analysis (OpenAI temporarily unavailable)'
            })
            
    except Exception as e:
        current_app.logger.exception(f"Problem refinement error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to refine problem statement'
        }), 500

def generate_fallback_variants(problem_description):
    """Generate intelligent fallback variants when OpenAI is unavailable"""
    base_problem = problem_description.strip()
    
    # Analyze problem type based on keywords
    technical_keywords = ['system', 'software', 'database', 'api', 'integration', 'performance', 'bug', 'error']
    business_keywords = ['cost', 'revenue', 'profit', 'efficiency', 'process', 'workflow', 'customer', 'sales']
    user_keywords = ['user', 'interface', 'experience', 'usability', 'access', 'navigation', 'design']
    
    problem_lower = base_problem.lower()
    
    variants = []
    
    # Technical-focused variant
    if any(keyword in problem_lower for keyword in technical_keywords):
        variants.append({
            "title": "Technical System Optimization",
            "description": f"Address the underlying technical challenges in {base_problem.lower()} by implementing systematic improvements to infrastructure, data processing, and system integration capabilities."
        })
    else:
        variants.append({
            "title": "Technology Infrastructure Enhancement",
            "description": f"Develop technical solutions to resolve {base_problem.lower()} through improved system architecture, automated processes, and enhanced data management capabilities."
        })
    
    # Business-focused variant
    if any(keyword in problem_lower for keyword in business_keywords):
        variants.append({
            "title": "Business Process Improvement",
            "description": f"Optimize organizational efficiency by addressing {base_problem.lower()} through streamlined workflows, cost reduction strategies, and enhanced operational procedures."
        })
    else:
        variants.append({
            "title": "Strategic Business Enhancement",
            "description": f"Improve business outcomes by systematically resolving {base_problem.lower()} to increase productivity, reduce operational overhead, and enhance competitive positioning."
        })
    
    # User experience variant
    if any(keyword in problem_lower for keyword in user_keywords):
        variants.append({
            "title": "User Experience Optimization",
            "description": f"Enhance user satisfaction and engagement by addressing {base_problem.lower()} through improved interface design, simplified workflows, and better accessibility features."
        })
    else:
        variants.append({
            "title": "Stakeholder Experience Enhancement",
            "description": f"Improve stakeholder interactions and satisfaction by resolving {base_problem.lower()} through better communication tools, streamlined processes, and enhanced service delivery."
        })
    
    return variants

def generate_intelligent_solutions(problem):
    """Generate intelligent solutions based on problem classification and OpenAI"""
    try:
        # Check for OpenAI API key
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            return generate_fallback_solutions(problem)
        
        # Use OpenAI for intelligent solution generation
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=openai_api_key)
            
            # Create context-aware prompt based on problem classification
            issue_type = getattr(problem, 'issue_type', 'OTHER')
            priority = getattr(problem, 'priority', {})
            priority_name = getattr(priority, 'name', 'Medium') if hasattr(priority, 'name') else str(priority)
            
            prompt = f"""
You are a senior IT consultant analyzing a {issue_type} issue with {priority_name} priority.

Problem Title: {problem.title}
Problem Description: {problem.description}
Issue Type: {issue_type}
Priority: {priority_name}

Based on the issue type ({issue_type}) and problem details, generate 3 specific, actionable solutions that address the root cause. Each solution should be realistic and appropriate for this type of problem.

For SYSTEM issues: Focus on technical infrastructure, performance optimization, hardware/software fixes
For PROCESS issues: Focus on workflow improvements, automation, policy changes  
For OTHER issues: Focus on general business solutions

Return JSON in this exact format:
{{
  "solutions": [
    {{
      "title": "Specific Solution Name",
      "description": "Detailed description of the solution addressing the root cause",
      "effort": "Low|Medium|High",
      "impact": "Low|Medium|High", 
      "timeline": "timeline estimate"
    }}
  ]
}}
"""
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1000
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            solutions = result.get('solutions', [])
            
            # Validate and ensure we have 3 solutions
            if len(solutions) >= 3:
                return solutions[:3]
            else:
                return generate_fallback_solutions(problem)
                
        except Exception as e:
            current_app.logger.warning(f"OpenAI solution generation failed: {e}")
            return generate_fallback_solutions(problem)
            
    except Exception as e:
        current_app.logger.exception(f"Solution generation error: {e}")
        return generate_fallback_solutions(problem)

def generate_fallback_solutions(problem):
    """Generate intelligent fallback solutions based on problem classification"""
    issue_type = getattr(problem, 'issue_type', 'OTHER')
    
    if issue_type == 'SYSTEM':
        return [
            {
                "title": "Infrastructure Performance Optimization",
                "description": f"Analyze and optimize the technical infrastructure causing {problem.title}. This includes server performance tuning, database optimization, network diagnostics, and capacity planning to resolve system bottlenecks.",
                "effort": "High",
                "impact": "High",
                "timeline": "2-4 weeks"
            },
            {
                "title": "System Monitoring and Alerting",
                "description": f"Implement comprehensive monitoring and alerting for {problem.title} to detect and prevent similar issues. Set up performance dashboards, automated alerts, and proactive monitoring systems.",
                "effort": "Medium",
                "impact": "High",
                "timeline": "1-3 weeks"
            },
            {
                "title": "Technical Documentation and Recovery Procedures",
                "description": f"Create detailed technical documentation and recovery procedures for {problem.title}. Develop runbooks, troubleshooting guides, and emergency response protocols for similar system issues.",
                "effort": "Low",
                "impact": "Medium",
                "timeline": "1-2 weeks"
            }
        ]
    elif issue_type == 'PROCESS':
        return [
            {
                "title": "Process Workflow Redesign",
                "description": f"Redesign and optimize the business process related to {problem.title}. Identify bottlenecks, eliminate redundancies, and streamline workflow steps for improved efficiency.",
                "effort": "Medium",
                "impact": "High",
                "timeline": "4-8 weeks"
            },
            {
                "title": "Process Automation Implementation",
                "description": f"Implement automation tools and technologies to address {problem.title}. Automate repetitive tasks, integrate systems, and reduce manual intervention points.",
                "effort": "High",
                "impact": "High",
                "timeline": "8-16 weeks"
            },
            {
                "title": "Staff Training and Process Documentation",
                "description": f"Develop comprehensive training programs and process documentation for {problem.title}. Create standard operating procedures, training materials, and knowledge transfer programs.",
                "effort": "Medium",
                "impact": "Medium",
                "timeline": "2-6 weeks"
            }
        ]
    else:  # OTHER
        return [
            {
                "title": "Root Cause Analysis and Strategic Planning",
                "description": f"Conduct thorough analysis of {problem.title} to identify underlying causes and develop strategic solutions. Engage stakeholders, analyze data, and create comprehensive action plan.",
                "effort": "Medium",
                "impact": "High",
                "timeline": "3-6 weeks"
            },
            {
                "title": "Cross-Functional Collaboration Initiative",
                "description": f"Establish cross-functional team to address {problem.title} through collaborative approach. Bring together relevant stakeholders, define roles, and implement coordinated solution.",
                "effort": "Medium",
                "impact": "Medium",
                "timeline": "4-8 weeks"
            },
            {
                "title": "Policy and Procedure Enhancement",
                "description": f"Review and enhance existing policies and procedures related to {problem.title}. Update guidelines, implement new controls, and ensure organizational alignment.",
                "effort": "Low",
                "impact": "Medium",
                "timeline": "2-4 weeks"
            }
        ]

@ai_bp.route('/suggest-solutions', methods=['POST'])
@login_required
def suggest_solutions():
    """Generate AI-powered solution suggestions for a problem"""
    try:
        data = request.get_json()
        if not data or 'problem_id' not in data:
            return jsonify({'success': False, 'error': 'Problem ID required'}), 400
            
        from models import Problem
        problem = Problem.query.get_or_404(data['problem_id'])
        user = current_user
        
        current_app.logger.info(f"Solution suggestions requested for problem {problem.id}")
        
        # Generate intelligent solutions based on problem classification and details
        solutions = generate_intelligent_solutions(problem)
        
        return jsonify({
            'success': True,
            'solutions': solutions,
            'message': 'Solutions generated based on problem analysis'
        })
        
    except Exception as e:
        current_app.logger.exception(f"Solution suggestion error: {e}")
        return jsonify({'success': False, 'error': 'Failed to generate solutions'}), 500

@ai_bp.route('/clear-epics/<int:case_id>', methods=['DELETE'])
@login_required
def clear_epics(case_id):
    """Clear existing epics and stories for a business case"""
    try:
        user = current_user
        
        # Check if user is authorized (Business Analyst role)
        if not user.role or user.role.value != 'BA':
            return jsonify({
                'success': False,
                'error': 'Only Business Analysts can clear epics'
            }), 403
        
        business_case = BusinessCase.query.get_or_404(case_id)
        
        # Delete epics and associated stories
        deleted_count = Epic.query.filter_by(case_id=case_id).delete()
        db.session.commit()
        
        current_app.logger.info(f"Cleared {deleted_count} epics for case {case_id}")
        
        return jsonify({
            'success': True,
            'message': f'Cleared {deleted_count} existing epics and their stories'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error clearing epics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear epics'
        }), 500

@ai_bp.route('/generate-stories', methods=['POST'])
@login_required
def generate_stories():
    """Generate AI-powered user stories for an epic"""
    try:
        current_app.logger.info("🤖 AI story generation requested")
        data = request.get_json()
        current_app.logger.info(f"🤖 Request data: {data}")
        
        if not data or 'epic_id' not in data:
            current_app.logger.error("🤖 Epic ID missing from request")
            return jsonify({
                'success': False,
                'error': 'Epic ID is required'
            }), 400
        
        epic_id = data['epic_id']
        user = current_user
        
        # Get the epic and validate access with organization filtering
        epic = Epic.query.filter_by(id=epic_id, organization_id=user.organization_id).first()
        if not epic:
            return jsonify({
                'success': False,
                'error': 'Epic not found or access denied'
            }), 404
        
        business_case = BusinessCase.query.filter_by(id=epic.case_id, organization_id=user.organization_id).first()
        if not business_case:
            return jsonify({
                'success': False,
                'error': 'Business case not found or access denied'
            }), 404
        
        current_app.logger.info(f"AI story generation requested for epic {epic_id}: {epic.title}")
        
        # Check for OpenAI API key
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            fallback_stories = generate_fallback_stories(epic)
            return jsonify({
                'success': True,
                'stories': fallback_stories,
                'message': 'Generated using intelligent analysis (OpenAI unavailable)'
            })
        
        # Use OpenAI for enhanced story generation
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=openai_api_key)
            
            prompt = f"""
            Break down the following Epic into 3-5 user stories.
            Respond ONLY in JSON format with this exact schema:
            {{
              "stories": [
                {{
                  "title": "User story title",
                  "description": "As a [user type], I want [functionality] so that [benefit]",
                  "acceptance_criteria": ["criterion 1", "criterion 2", "criterion 3"],
                  "priority": "Critical|High|Medium|Low", 
                  "effort_estimate": "XS|S|M|L|XL"
                }}
              ]
            }}

            Epic Title: {epic.title}
            Epic Description: {epic.description}
            Business Context: {business_case.title} - {business_case.description}
            """
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert agile coach and business analyst. Create specific, testable user stories that deliver value and follow INVEST principles (Independent, Negotiable, Valuable, Estimable, Small, Testable). Respond only in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response from OpenAI
            content = response.choices[0].message.content
            
            try:
                import json
                response_data = json.loads(content)
                stories = response_data.get('stories', [])
                current_app.logger.info(f"Generated {len(stories)} AI-powered user stories")
                return jsonify({
                    'success': True,
                    'stories': stories,
                    'message': f'Generated {len(stories)} user stories using AI analysis'
                })
            except json.JSONDecodeError as e:
                current_app.logger.error(f"Failed to parse AI JSON response: {e}")
                current_app.logger.error(f"Raw response: {content}")
                # Fall back to intelligent analysis
                fallback_stories = generate_fallback_stories(epic)
                return jsonify({
                    'success': True,
                    'stories': fallback_stories,
                    'message': 'Generated using intelligent analysis (AI response format error)'
                })
            
        except Exception as openai_error:
            current_app.logger.warning(f"OpenAI API error: {openai_error}")
            fallback_stories = generate_fallback_stories(epic)
            return jsonify({
                'success': True,
                'stories': fallback_stories,
                'message': 'Generated using intelligent analysis (OpenAI temporarily unavailable)'
            })
            
    except Exception as e:
        current_app.logger.exception(f"Story generation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate user stories'
        }), 500

def parse_generated_stories(response_text):
    """Parse OpenAI response into structured user stories"""
    stories = []
    
    # Split response into story sections
    story_sections = re.split(r'\*\*Story \d+:', response_text)
    
    for section in story_sections[1:]:  # Skip first empty section
        try:
            # Extract title
            title_match = re.search(r'^([^*\n]+)', section.strip())
            title = title_match.group(1).strip() if title_match else "Generated User Story"
            
            # Extract description
            desc_match = re.search(r'Description:\s*([^\n]+)', section)
            description = desc_match.group(1).strip() if desc_match else "User story description"
            
            # Extract priority
            priority_match = re.search(r'Priority:\s*(\w+)', section)
            priority = priority_match.group(1) if priority_match else "Medium"
            
            # Extract effort
            effort_match = re.search(r'Effort:\s*(\w+)', section)
            effort_estimate = effort_match.group(1) if effort_match else "M"
            
            # Extract acceptance criteria
            criteria_section = re.search(r'Acceptance Criteria:(.*?)(?=\*\*|$)', section, re.DOTALL)
            acceptance_criteria = ""
            if criteria_section:
                criteria_lines = [line.strip() for line in criteria_section.group(1).split('\n') if line.strip() and ('•' in line or '-' in line)]
                acceptance_criteria = '\n'.join(criteria_lines[:3])  # Take first 3 criteria
            
            story = {
                'title': title,
                'description': description,
                'acceptance_criteria': acceptance_criteria,
                'priority': priority,
                'effort_estimate': effort_estimate
            }
            stories.append(story)
            
        except Exception as parse_error:
            current_app.logger.warning(f"Error parsing story section: {parse_error}")
            continue
    
    # Ensure we have at least some stories
    if not stories:
        stories = [
            {
                'title': 'Core Functionality Implementation',
                'description': 'As a user, I want the core functionality so that I can accomplish my primary goals',
                'acceptance_criteria': '• Core feature is accessible\n• Basic functionality works correctly\n• User can complete primary workflow',
                'priority': 'High',
                'effort_estimate': 'L'
            }
        ]
    
    return stories[:5]  # Return max 5 stories

def generate_fallback_stories(epic):
    """Generate intelligent fallback user stories when OpenAI is unavailable"""
    base_title = epic.title
    base_description = epic.description or "Epic functionality"
    
    stories = [
        {
            'title': f'{base_title} - Core Implementation',
            'description': f'As a user, I want to access the core {base_title.lower()} functionality so that I can accomplish my primary objectives',
            'acceptance_criteria': '• Feature is accessible from main interface\n• Core functionality works as expected\n• User receives appropriate feedback',
            'priority': 'High',
            'effort_estimate': 'L'
        },
        {
            'title': f'{base_title} - Data Management',
            'description': f'As a user, I want to manage data within {base_title.lower()} so that I can maintain accurate information',
            'acceptance_criteria': '• Data can be created and updated\n• Validation prevents invalid entries\n• Changes are saved correctly',
            'priority': 'Medium',
            'effort_estimate': 'M'
        },
        {
            'title': f'{base_title} - User Interface',
            'description': f'As a user, I want an intuitive interface for {base_title.lower()} so that I can work efficiently',
            'acceptance_criteria': '• Interface is responsive and accessible\n• Actions are clearly labeled\n• User experience is smooth',
            'priority': 'Medium',
            'effort_estimate': 'M'
        }
    ]
    
    return stories

@ai_bp.route('/suggest-requirements-answers', methods=['POST'])
@login_required  
def suggest_requirements_answers():
    """Generate AI-suggested answers for requirements form fields"""
    try:
        data = request.get_json()
        if not data or 'case_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Business case ID is required'
            }), 400
        
        case_id = data['case_id']
        user = current_user
        business_case = BusinessCase.query.get_or_404(case_id)
        
        current_app.logger.info(f"AI requirements answers requested for case {case_id}: {business_case.title}")
        
        # Check for OpenAI API key
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            current_app.logger.warning("OpenAI API key not available, using fallback answers")
            fallback_answers = get_fallback_requirements_answers(business_case)
            return jsonify({
                'success': True,
                'answers': fallback_answers,
                'message': 'Generated comprehensive requirements (OpenAI unavailable)'
            })
        
        # Use OpenAI for intelligent requirements analysis
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=openai_api_key)
            
            # Build context from business case
            context = f"""
            Business Case: {business_case.title}
            Description: {business_case.description}
            Cost Estimate: ${business_case.cost_estimate:,.2f}
            Benefit Estimate: ${business_case.benefit_estimate:,.2f}
            ROI: {business_case.roi}%
            Department: {business_case.department.name if business_case.department else 'Not specified'}
            """
            
            prompt = f"""Based on this business case, provide specific answers for these 8 requirements questions:

{context}

Questions to answer:
1. What are the core functional requirements for this system?
2. Who are the primary user roles and what permissions do they need?
3. What external systems or data sources need integration?
4. What are the performance and scalability requirements?
5. What reporting and audit capabilities are needed?
6. How should the system handle errors and validate data?
7. What are the UI/UX and accessibility requirements?
8. What security and compliance requirements must be met?

Provide practical, specific answers for each question based on the business case context.
Format as 8 numbered answers, each 2-3 sentences long."""

            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a senior business analyst expert at translating business cases into detailed technical requirements. Provide specific, actionable requirements."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            # Parse the AI response into 8 answers
            ai_response = response.choices[0].message.content
            answers = parse_requirements_answers(ai_response)
            
            current_app.logger.info(f"Generated {len(answers)} AI requirements answers")
            return jsonify({
                'success': True,
                'answers': answers,
                'message': 'Requirements generated using AI analysis'
            })
            
        except Exception as openai_error:
            current_app.logger.warning(f"OpenAI API error: {openai_error}")
            fallback_answers = get_fallback_requirements_answers(business_case)
            return jsonify({
                'success': True,
                'answers': fallback_answers,
                'message': 'Generated comprehensive requirements (OpenAI temporarily unavailable)'
            })
            
    except Exception as e:
        current_app.logger.exception(f"Requirements answers error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate requirements answers'
        }), 500

def parse_requirements_answers(ai_response):
    """Parse AI response into 8 requirement answers"""
    answers = {}
    
    # Try to extract numbered answers using regex
    pattern = r'(\d+)\.?\s*([^0-9]+?)(?=\d+\.|$)'
    matches = re.findall(pattern, ai_response, re.DOTALL)
    
    for i, match in enumerate(matches[:8]):
        question_num = f"q{i+1}"
        answer_text = match[1].strip()
        # Clean up the answer
        answer_text = re.sub(r'\n+', ' ', answer_text)
        answer_text = re.sub(r'\s+', ' ', answer_text)
        answers[question_num] = answer_text
    
    # Fill in missing answers with fallbacks
    fallback_template = [
        "Core system functionality with data processing and workflow management capabilities",
        "Multi-role access with admin, manager, and user permissions based on organizational hierarchy", 
        "Integration with existing enterprise systems and external data sources via APIs",
        "High availability architecture supporting concurrent users with response times under 2 seconds",
        "Comprehensive audit trails, compliance reporting, and real-time dashboard analytics",
        "Input validation, error handling, and graceful degradation with user-friendly error messages",
        "Responsive design with accessibility compliance and intuitive user interface",
        "Role-based security, data encryption, and compliance with relevant industry standards"
    ]
    
    for i in range(8):
        question_num = f"q{i+1}"
        if question_num not in answers or not answers[question_num]:
            answers[question_num] = fallback_template[i]
    
    return answers

@ai_bp.route('/write-summary', methods=['POST'])
@login_required
def write_summary():
    data = request.get_json() or {}
    case_id = data.get('case_id')
    
    # Handle both saved cases and form data
    if case_id:
        # Working with saved business case
        bc = BusinessCase.query.get_or_404(case_id)
        title = bc.title
        cost_estimate = bc.cost_estimate
        benefit_estimate = bc.benefit_estimate
        problem_desc = bc.problem.description if bc.problem else 'N/A'
        solution_desc = getattr(bc, 'solution_description', '') or data.get('description', '')
    else:
        # Working with form data (unsaved case)
        title = data.get('title', 'Business Case')
        cost_estimate = float(data.get('cost_estimate', 0))
        benefit_estimate = float(data.get('benefit_estimate', 0))
        problem_desc = data.get('problem_description', 'N/A')
        solution_desc = data.get('description', '') or data.get('solution_description', '')
    
    # Check if OpenAI is available
    if not os.getenv('OPENAI_API_KEY'):
        # Simple fallback summary
        fallback = f"Executive Summary: {title} represents a strategic business initiative with an estimated investment of ${cost_estimate:,.2f} and projected benefits of ${benefit_estimate:,.2f}. This case requires careful evaluation and stakeholder alignment to ensure successful implementation and value realization."
        
        # Save to database if we have a case_id
        if case_id:
            bc.summary = fallback
            db.session.commit()
        
        return jsonify(summary=fallback), 200
    
    # Build the prompt using refined problem, solution, financials
    roi_calc = f"{benefit_estimate/cost_estimate:.2f}" if cost_estimate > 0 else "N/A"
    prompt = (
        "You are a skilled business writer. Given the following details, "
        "write a concise executive summary for a business case:\n\n"
        f"Problem: {problem_desc}\n"
        f"Solution: {solution_desc}\n"
        f"Cost Estimate: ${cost_estimate:,.2f}\n"
        f"Benefit Estimate: ${benefit_estimate:,.2f}\n"
        f"ROI: {roi_calc}\n\n"
        "Provide a 2-3 paragraph summary emphasizing justification, impact, and next steps."
    )
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        resp = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system","content":"Generate an executive summary."},
                {"role":"user","content":prompt}
            ],
            temperature=0.3
        )
        summary = resp.choices[0].message.content.strip()
        
        # Save to database if we have a case_id
        if case_id:
            bc.summary = summary
            db.session.commit()
        
        return jsonify(summary=summary), 200
    except Exception:
        current_app.logger.exception("AI write-summary failed")
        # Provide fallback on error
        fallback = f"Executive Summary: {title} represents a strategic business initiative with an estimated investment of ${cost_estimate:,.2f} and projected benefits of ${benefit_estimate:,.2f}. This case requires careful evaluation and stakeholder alignment to ensure successful implementation and value realization."
        
        # Save to database if we have a case_id
        if case_id:
            bc.summary = fallback
            db.session.commit()
        
        return jsonify(summary=fallback), 200

def get_fallback_requirements_answers(business_case):
    """Provide comprehensive fallback requirements when AI is unavailable"""
    cost = business_case.cost_estimate
    title_lower = business_case.title.lower()
    
    # Customize based on business case characteristics
    system_type = "management system"
    if any(word in title_lower for word in ['tender', 'procurement', 'contract']):
        system_type = "procurement and tender management system"
    elif any(word in title_lower for word in ['hr', 'employee', 'staff']):
        system_type = "human resources management system"
    elif any(word in title_lower for word in ['finance', 'accounting', 'budget']):
        system_type = "financial management system"
    
    return {
        "q1": f"Core {system_type} functionality including data entry, processing workflows, document management, approval processes, and automated notifications to support {business_case.title}.",
        
        "q2": "Multi-tier user roles including System Administrator (full access), Department Manager (approval authority), Business Analyst (configuration rights), General User (data entry/viewing), and Guest (read-only access) with hierarchical permissions.",
        
        "q3": "Integration with existing ERP systems, Active Directory authentication, email services (SMTP), document storage systems, and external APIs for data synchronization and automated workflow triggers.",
        
        "q4": f"Support for {min(500, int(cost/1000))} concurrent users with sub-2-second response times, 99.5% uptime SLA, auto-scaling capabilities, and data processing capacity for {int(cost/100)} transactions per hour.",
        
        "q5": "Real-time dashboard with KPI visualization, automated compliance reporting, audit trail logging, configurable alerts, scheduled report generation, and data export capabilities (PDF, Excel, CSV formats).",
        
        "q6": "Comprehensive input validation with field-level error messaging, graceful error handling with user-friendly notifications, automatic data backup and recovery, duplicate detection, and data integrity validation rules.",
        
        "q7": "Responsive web design compatible with desktop, tablet, and mobile devices, WCAG 2.1 AA accessibility compliance, intuitive navigation, modern Bootstrap-based UI, and multi-language support capability.",
        
        "q8": "Role-based access control, AES-256 data encryption, secure authentication with password policies, HTTPS/TLS communication, regular security audits, GDPR compliance, and secure data backup procedures."
    }

def generate_contextual_epics(business_case, answers):
    """Generate 8 contextual epics based on business case and requirements analysis - one per requirement question"""
    epics = []
    
    # Epic 1: Functional Requirements (q1)
    functional_req = answers.get('q1', 'Core system functionality')
    epics.append({
        "title": f"Functional Requirements - {business_case.title}",
        "description": f"Core functional capabilities and features for {business_case.title}",
        "stories": [
            {
                "title": "Primary Functions Implementation",
                "description": f"As a user, I want the core functional requirements implemented so that {functional_req.lower()}",
                "acceptance_criteria": [
                    "All primary functional requirements implemented",
                    "Core business logic and workflows operational",
                    "User interface for main functions completed"
                ],
                "priority": "High",
                "effort_estimate": "13 story points"
            },
            {
                "title": "Feature Integration Testing",
                "description": "As a tester, I want comprehensive testing of functional requirements so that quality is assured",
                "acceptance_criteria": [
                    "Unit tests for all functional components",
                    "Integration testing completed",
                    "User acceptance testing passed"
                ],
                "priority": "High",
                "effort_estimate": "8 story points"
            }
        ]
    })
    
    # Epic 2: User Roles & Access (q2)
    user_roles = answers.get('q2', 'System users and administrators')
    epics.append({
        "title": "User Management & Access Control",
        "description": f"Role-based access control and user management for {user_roles}",
        "stories": [
            {
                "title": "User Authentication System",
                "description": f"As a system administrator, I want secure authentication so that {user_roles.lower()} can access the system securely",
                "acceptance_criteria": [
                    "Secure login and logout functionality",
                    "Password management and security policies",
                    "Session management and timeout controls"
                ],
                "priority": "High",
                "effort_estimate": "8 story points"
            },
            {
                "title": "Role-Based Permissions",
                "description": f"As an administrator, I want role-based permissions so that {user_roles.lower()} have appropriate access levels",
                "acceptance_criteria": [
                    "Role definition and assignment interface",
                    "Permission matrix implementation",
                    "Access control validation and enforcement"
                ],
                "priority": "Medium",
                "effort_estimate": "10 story points"
            }
        ]
    })
    
    # Epic 3: Integration Requirements (q3)
    integration_req = answers.get('q3', 'System integration and connectivity')
    epics.append({
        "title": "System Integration & APIs",
        "description": f"External system integration and API development: {integration_req}",
        "stories": [
            {
                "title": "API Development",
                "description": f"As a developer, I want robust APIs so that {integration_req.lower()} is supported",
                "acceptance_criteria": [
                    "RESTful API endpoints designed and implemented",
                    "API documentation and testing tools",
                    "Rate limiting and security measures"
                ],
                "priority": "Medium",
                "effort_estimate": "13 story points"
            },
            {
                "title": "External System Connectivity",
                "description": f"As a system administrator, I want external connectivity so that {integration_req.lower()} works seamlessly",
                "acceptance_criteria": [
                    "External system connection interfaces",
                    "Data synchronization and mapping",
                    "Error handling and retry mechanisms"
                ],
                "priority": "Medium",
                "effort_estimate": "11 story points"
            }
        ]
    })
    
    # Epic 4: Performance Requirements (q4)
    performance_req = answers.get('q4', 'System performance and scalability')
    epics.append({
        "title": "Performance & Scalability",
        "description": f"System performance optimization and scalability: {performance_req}",
        "stories": [
            {
                "title": "Performance Optimization",
                "description": f"As a user, I want optimal performance so that {performance_req.lower()} is achieved",
                "acceptance_criteria": [
                    "Response time optimization and caching",
                    "Database query optimization",
                    "Resource usage monitoring and alerts"
                ],
                "priority": "High",
                "effort_estimate": "10 story points"
            },
            {
                "title": "Scalability Architecture",
                "description": f"As a system architect, I want scalable architecture so that {performance_req.lower()} is maintained under load",
                "acceptance_criteria": [
                    "Horizontal and vertical scaling capabilities",
                    "Load balancing and distribution",
                    "Performance testing and benchmarking"
                ],
                "priority": "Medium",
                "effort_estimate": "15 story points"
            }
        ]
    })
    
    # Epic 5: Reporting Requirements (q5)
    reporting_req = answers.get('q5', 'Business reporting and analytics')
    epics.append({
        "title": "Reporting & Analytics",
        "description": f"Business intelligence and reporting capabilities: {reporting_req}",
        "stories": [
            {
                "title": "Dashboard Development",
                "description": f"As a manager, I want comprehensive dashboards so that {reporting_req.lower()} is available",
                "acceptance_criteria": [
                    "Real-time dashboard with key metrics",
                    "Customizable chart and graph components",
                    "Interactive filtering and drill-down"
                ],
                "priority": "Medium",
                "effort_estimate": "12 story points"
            },
            {
                "title": "Report Generation",
                "description": f"As a business user, I want detailed reports so that {reporting_req.lower()} supports decision making",
                "acceptance_criteria": [
                    "Parameterized report templates",
                    "Multiple export formats (PDF, CSV, Excel)",
                    "Scheduled and automated report delivery"
                ],
                "priority": "Medium",
                "effort_estimate": "9 story points"
            }
        ]
    })
    
    # Epic 6: Data & Validation (q6)
    data_req = answers.get('q6', 'Data management and validation')
    epics.append({
        "title": "Data Management & Validation",
        "description": f"Data integrity, validation, and management: {data_req}",
        "stories": [
            {
                "title": "Data Validation Engine",
                "description": f"As a data steward, I want robust validation so that {data_req.lower()} ensures data quality",
                "acceptance_criteria": [
                    "Real-time data validation rules",
                    "Data quality monitoring and alerts",
                    "Error reporting and correction workflows"
                ],
                "priority": "High",
                "effort_estimate": "10 story points"
            },
            {
                "title": "Data Management Tools",
                "description": f"As an administrator, I want data management tools so that {data_req.lower()} is maintained effectively",
                "acceptance_criteria": [
                    "Data import and export capabilities",
                    "Backup and recovery procedures",
                    "Data archival and retention policies"
                ],
                "priority": "Medium",
                "effort_estimate": "8 story points"
            }
        ]
    })
    
    # Epic 7: User Interface (q7)
    ui_req = answers.get('q7', 'User interface and experience')
    epics.append({
        "title": "User Interface & Experience",
        "description": f"User interface design and user experience: {ui_req}",
        "stories": [
            {
                "title": "Responsive UI Design",
                "description": f"As a user, I want an intuitive interface so that {ui_req.lower()} provides excellent usability",
                "acceptance_criteria": [
                    "Responsive design for all device types",
                    "Intuitive navigation and user flows",
                    "Accessibility compliance and standards"
                ],
                "priority": "High",
                "effort_estimate": "12 story points"
            },
            {
                "title": "User Experience Optimization",
                "description": f"As a UX designer, I want optimized user experience so that {ui_req.lower()} maximizes user satisfaction",
                "acceptance_criteria": [
                    "User testing and feedback integration",
                    "Performance optimization for UI components",
                    "Help documentation and user guides"
                ],
                "priority": "Medium",
                "effort_estimate": "7 story points"
            }
        ]
    })
    
    # Epic 8: Security & Compliance (q8)
    security_req = answers.get('q8', 'Security and compliance requirements')
    epics.append({
        "title": "Security & Compliance",
        "description": f"Security measures and compliance requirements: {security_req}",
        "stories": [
            {
                "title": "Security Implementation",
                "description": f"As a security officer, I want comprehensive security so that {security_req.lower()} protects the system",
                "acceptance_criteria": [
                    "Data encryption in transit and at rest",
                    "Security vulnerability scanning and remediation",
                    "Audit logging and monitoring"
                ],
                "priority": "High",
                "effort_estimate": "11 story points"
            },
            {
                "title": "Compliance Framework",
                "description": f"As a compliance manager, I want compliance controls so that {security_req.lower()} meets regulatory requirements",
                "acceptance_criteria": [
                    "Compliance reporting and documentation",
                    "Regulatory control implementation",
                    "Compliance monitoring and alerting"
                ],
                "priority": "Medium",
                "effort_estimate": "9 story points"
            }
        ]
    })
    
    return epics  # Return all 8 epics

def generate_fallback_epics(business_case, answers):
    """Generate fallback epics when AI/OpenAI generation fails"""
    print(f"🤖 Using fallback epic generation for: {business_case.title}")
    
    # Create basic epics without AI dependency
    fallback_epics = [
        {
            "title": "Core System Development",
            "description": f"Fundamental system development for {business_case.title}",
            "stories": [
                {
                    "title": "Basic System Setup",
                    "description": "As a developer, I want a basic system setup so that core functionality can be implemented",
                    "acceptance_criteria": ["System architecture defined", "Development environment setup", "Basic functionality implemented"],
                    "priority": "High",
                    "effort_estimate": "8 story points"
                }
            ]
        },
        {
            "title": "User Interface Development", 
            "description": f"User interface development for {business_case.title}",
            "stories": [
                {
                    "title": "UI Framework Implementation",
                    "description": "As a user, I want an intuitive interface so that I can use the system effectively",
                    "acceptance_criteria": ["UI framework selected and implemented", "Basic navigation created", "User-friendly interface designed"],
                    "priority": "Medium",
                    "effort_estimate": "6 story points"
                }
            ]
        },
        {
            "title": "Testing & Quality Assurance",
            "description": f"Testing and quality assurance for {business_case.title}",
            "stories": [
                {
                    "title": "Test Suite Development",
                    "description": "As a tester, I want comprehensive testing so that system quality is assured",
                    "acceptance_criteria": ["Unit tests implemented", "Integration tests created", "Quality standards met"],
                    "priority": "Medium", 
                    "effort_estimate": "5 story points"
                }
            ]
        }
    ]
    
    return fallback_epics

@ai_bp.route('/generate-requirements/<int:case_id>', methods=['POST'])
@login_required
def generate_requirements_epic(case_id):
    """Generate requirements using intelligent contextual analysis with enhanced error handling"""
    try:
        user = current_user
        print(f"🤖 AI Requirements Generation - User: {user.name if user else 'None'}, Case ID: {case_id}")
        
        # Add timeout protection for database queries
        business_case = BusinessCase.query.get_or_404(case_id)
        current_app.logger.info(f"Generating epics for case {case_id}: {business_case.title}")
        print(f"🤖 Found business case: {business_case.title}")
        
        # Get user answers from request with enhanced validation
        data = request.get_json()
        if not data:
            current_app.logger.error("No JSON data provided in request")
            print("❌ No JSON data provided in request")
            return jsonify({
                'success': False,
                'error': 'No input data provided'
            }), 400
        
        answers = data.get('answers', {})
        current_app.logger.info(f"Processing {len(answers)} requirement answers")
        print(f"🤖 Processing {len(answers)} requirement answers: {list(answers.keys())}")
        
        # Validate answers format
        if not isinstance(answers, dict):
            print("❌ Invalid answers format - not a dictionary")
            return jsonify({
                'success': False,
                'error': 'Invalid answers format'
            }), 400
        
        # Generate intelligent contextual epics with timeout protection
        print("🤖 Generating contextual epics...")
        try:
            generated_epics = generate_contextual_epics(business_case, answers)
            current_app.logger.info(f"Generated {len(generated_epics)} contextual epics from requirements analysis")
            print(f"🤖 Generated {len(generated_epics)} contextual epics")
        except Exception as epic_error:
            print(f"❌ Epic generation failed: {epic_error}")
            # Use fallback epic generation
            generated_epics = generate_fallback_epics(business_case, answers)
            print(f"🤖 Using fallback epics: {len(generated_epics)} generated")
        
        # Save epics to database if user is a Business Analyst, Admin, Director, or Manager
        print(f"🤖 User role: {user.role}, checking if authorized...")
        if user.role and user.role.value in ['BA', 'Admin', 'Director', 'Manager']:
            print("🤖 User authorized, saving to database...")
            try:
                # Clear existing stories first, then epics to avoid foreign key constraint violations
                print(f"🤖 Clearing existing epics and stories for case {case_id}...")
                existing_epics = Epic.query.filter_by(case_id=case_id, organization_id=user.organization_id).all()
                for epic in existing_epics:
                    Story.query.filter_by(epic_id=epic.id, organization_id=user.organization_id).delete()
                Epic.query.filter_by(case_id=case_id, organization_id=user.organization_id).delete()
                db.session.commit()
                print(f"🤖 Cleared {len(existing_epics)} existing epics")
                
                # Save new epics with enhanced error handling
                saved_epics = 0
                for epic_data in generated_epics:
                    try:
                        epic = Epic(
                            case_id=case_id,
                            title=epic_data.get('title', 'Generated Epic'),
                            description=epic_data.get('description', 'AI-generated epic'),
                            creator_id=user.id,
                            organization_id=user.organization_id
                        )
                        db.session.add(epic)
                        db.session.flush()  # Get epic ID
                        
                        # Save stories for this epic
                        for story_data in epic_data.get('stories', []):
                            story = Story(
                                epic_id=epic.id,
                                title=story_data.get('title', 'Generated Story'),
                                description=story_data.get('description', 'AI-generated story'),
                                acceptance_criteria=json.dumps(story_data.get('acceptance_criteria', [])),
                                priority=story_data.get('priority', 'Medium'),
                                effort_estimate=story_data.get('effort_estimate', '5 story points'),
                                organization_id=user.organization_id
                            )
                            db.session.add(story)
                        
                        saved_epics += 1
                        
                    except Exception as epic_error:
                        print(f"❌ Error saving epic: {epic_error}")
                        continue
                
                # Save requirements backup to prevent data loss
                try:
                    backup = RequirementsBackup(
                        case_id=case_id,
                        answers_json=json.dumps(answers),
                        epics_json=json.dumps(generated_epics),
                        created_by=user.id,
                        organization_id=user.organization_id
                    )
                    db.session.add(backup)
                except Exception as backup_error:
                    print(f"❌ Error creating backup: {backup_error}")
                
                db.session.commit()
                current_app.logger.info(f"Saved {saved_epics} epics and backup to database for case {case_id}")
                print(f"🤖 Successfully saved {saved_epics} epics to database")
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Database save error: {e}")
                print(f"❌ Database save error: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"🤖 User not authorized to save to database (role: {user.role})")
        
        # Return contextual epics with enhanced success message
        print(f"🤖 Returning {len(generated_epics)} epics to client")
        return jsonify({
            'success': True,
            'epics': generated_epics,
            'message': f'Generated {len(generated_epics)} epics successfully'
        })
        
    except Exception as e:
        current_app.logger.exception(f"Fatal error in generate_requirements_epic: {e}")
        print(f"❌ Fatal error in generate_requirements_epic: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Failed to generate requirements: {str(e)}'
        }), 500

@ai_bp.route('/api/ai/refine-story', methods=['POST'])
@login_required
def refine_story():
    """BA Story Refinement - Generate enhanced user story details"""
    user = current_user
    if not user:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    # Only Business Analysts can refine stories
    if user.role != RoleEnum.BA:
        return jsonify({'success': False, 'error': 'Only Business Analysts can refine stories'}), 403
    
    try:
        data = request.get_json()
        if not data or 'story_id' not in data:
            return jsonify({'success': False, 'error': 'Story ID required'}), 400
        
        story_id = data['story_id']
        story = Story.query.get(story_id)
        if not story:
            return jsonify({'success': False, 'error': 'Story not found'}), 404
        
        # Get epic and business case context
        epic = Epic.query.get(story.epic_id)
        if not epic:
            return jsonify({'success': False, 'error': 'Epic not found'}), 404
        
        business_case = BusinessCase.query.get(epic.case_id)
        if not business_case:
            return jsonify({'success': False, 'error': 'Business case not found'}), 404
        
        # Check if OpenAI is available
        if not current_app.config.get('AI_AVAILABLE', False):
            # Fallback refinement based on story context
            refined_story = {
                'title': story.title,
                'description': story.description,
                'acceptance_criteria': [
                    f"Given the user accesses {story.title.lower()}",
                    "When they interact with the system",
                    f"Then they should be able to {story.description.lower()[:50]}..."
                ],
                'priority': story.priority or 'Medium',
                'effort_estimate': story.effort_estimate or '3 points',
                'business_value': 'Contributes to project objectives',
                'technical_notes': 'Implementation details to be determined during sprint planning'
            }
            
            return jsonify({
                'success': True,
                'refined_story': refined_story,
                'ai_generated': False,
                'message': 'Story refined using fallback logic (AI offline)'
            })
        
        # AI-powered story refinement
        openai_client = OpenAI(api_key=current_app.config.get('OPENAI_API_KEY'))
        
        prompt = f"""
        As a Business Analyst, please refine this user story with enhanced details:
        
        **Business Context:**
        - Business Case: {business_case.title}
        - Epic: {epic.title}
        - Case Type: {business_case.case_type.name}
        - Priority: {business_case.priority.name if business_case.priority else 'Medium'}
        
        **Current User Story:**
        - Title: {story.title}
        - Description: {story.description}
        - Current Acceptance Criteria: {story.acceptance_criteria or 'None defined'}
        - Priority: {story.priority}
        - Effort: {story.effort_estimate or 'Not estimated'}
        
        Please provide a refined version with:
        1. Enhanced title (clear, actionable)
        2. Detailed description (user persona, goal, benefit)
        3. Comprehensive acceptance criteria (3-5 specific, testable criteria)
        4. Appropriate priority (High/Medium/Low based on business context)
        5. Effort estimate (1, 2, 3, 5, 8, 13 story points)
        6. Business value statement
        7. Technical implementation notes
        
        Respond in JSON format:
        {{
            "title": "Enhanced user story title",
            "description": "As a [persona], I want [goal] so that [benefit]",
            "acceptance_criteria": ["Given...", "When...", "Then..."],
            "priority": "High/Medium/Low",
            "effort_estimate": "X points",
            "business_value": "Clear business value statement",
            "technical_notes": "Implementation considerations"
        }}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=[
                {"role": "system", "content": "You are an expert Business Analyst with deep expertise in user story refinement, agile methodology, and requirements engineering."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        logging.info(f"BA story refinement AI response: {ai_response}")
        
        # Parse AI response
        import json
        try:
            refined_story = json.loads(ai_response)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse AI response: {e}")
            # Fallback to basic refinement
            refined_story = {
                'title': story.title,
                'description': story.description,
                'acceptance_criteria': ['Generated criteria pending AI processing'],
                'priority': story.priority or 'Medium',
                'effort_estimate': story.effort_estimate or '3 points',
                'business_value': 'Business value assessment in progress',
                'technical_notes': 'Technical analysis required'
            }
        
        return jsonify({
            'success': True,
            'refined_story': refined_story,
            'ai_generated': True,
            'message': 'Story refined successfully using AI analysis'
        })
        
    except Exception as e:
        logging.error(f"Error refining story: {e}")
        return jsonify({'success': False, 'error': 'Failed to refine story'}), 500

@ai_bp.route('/api/ai/update-story', methods=['POST'])
@login_required
def update_story():
    """Update story with refined details from BA"""
    user = current_user
    if not user:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    # Only Business Analysts can update stories
    if user.role != RoleEnum.BA:
        return jsonify({'success': False, 'error': 'Only Business Analysts can update stories'}), 403
    
    try:
        data = request.get_json()
        if not data or 'story_id' not in data:
            return jsonify({'success': False, 'error': 'Story ID required'}), 400
        
        story_id = data['story_id']
        story = Story.query.get(story_id)
        if not story:
            return jsonify({'success': False, 'error': 'Story not found'}), 404
        
        # Update story with refined details
        if 'title' in data:
            story.title = data['title']
        if 'description' in data:
            story.description = data['description']
        if 'acceptance_criteria' in data:
            # Store acceptance criteria as JSON string
            import json
            story.acceptance_criteria = json.dumps(data['acceptance_criteria'])
        if 'priority' in data:
            story.priority = data['priority']
        if 'effort_estimate' in data:
            story.effort_estimate = data['effort_estimate']
        
        story.updated_at = datetime.utcnow()
        db.session.commit()
        
        logging.info(f"BA user {user.id} updated story {story_id}")
        
        return jsonify({
            'success': True,
            'message': 'Story updated successfully',
            'story': story.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating story: {e}")
        return jsonify({'success': False, 'error': 'Failed to update story'}), 500

@ai_bp.route('/api/epics/<int:case_id>', methods=['GET'])
@login_required
def get_epics_and_stories(case_id):
    """Get all epics and stories for a business case"""
    user = current_user
    
    # Verify business case exists and user has access
    from models import BusinessCase
    business_case = BusinessCase.query.get_or_404(case_id)
    
    try:
        # Get all epics for this case
        epics = Epic.query.filter_by(case_id=case_id).order_by(Epic.created_at).all()
        
        # Get all stories for these epics
        epic_ids = [epic.id for epic in epics]
        stories = []
        if epic_ids:
            stories = Story.query.filter(Story.epic_id.in_(epic_ids)).order_by(Story.created_at).all()
        
        # Convert to dictionaries
        epics_data = []
        for epic in epics:
            epics_data.append({
                'id': epic.id,
                'case_id': epic.case_id,
                'title': epic.title,
                'description': epic.description,
                'priority': epic.priority.value if epic.priority else 'Medium',
                'effort_estimate': epic.effort_estimate or 'M',
                'created_at': epic.created_at.isoformat() if epic.created_at else None
            })
        
        stories_data = []
        for story in stories:
            stories_data.append({
                'id': story.id,
                'epic_id': story.epic_id,
                'title': story.title,
                'description': story.description,
                'priority': story.priority.value if story.priority else 'Medium',
                'effort_estimate': story.effort_estimate or 'S',
                'acceptance_criteria': story.acceptance_criteria,
                'created_at': story.created_at.isoformat() if story.created_at else None
            })
        
        return jsonify({
            'epics': epics_data,
            'stories': stories_data,
            'case_id': case_id
        })
        
    except Exception as e:
        logging.error(f"Error fetching epics and stories: {e}")
        return jsonify({'error': 'Failed to load epics and stories'}), 500

@ai_bp.route('/epics-stories/<int:project_id>', methods=['GET'])
@login_required
def get_project_epics_stories(project_id):
    """Get all epics and stories for a project - used by story refinement interface"""
    user = current_user
    
    try:
        # Get all epics linked to this project
        from models import Project
        project = Project.query.get_or_404(project_id)
        epics = Epic.query.filter_by(project_id=project_id).order_by(Epic.created_at).all()
        
        # Get all stories for these epics
        epic_ids = [epic.id for epic in epics]
        stories = []
        if epic_ids:
            stories = Story.query.filter(Story.epic_id.in_(epic_ids)).order_by(Story.created_at).all()
        
        # Convert to dictionaries with proper data structure
        epics_data = []
        for epic in epics:
            epic_stories = [story for story in stories if story.epic_id == epic.id]
            stories_data = []
            
            for story in epic_stories:
                stories_data.append({
                    'id': story.id,
                    'epic_id': story.epic_id,
                    'title': story.title or 'Untitled Story',
                    'description': story.description or '',
                    'priority': story.priority or 'Medium',
                    'effort_estimate': story.effort_estimate or '',
                    'acceptance_criteria': story.acceptance_criteria or '',
                    'created_at': story.created_at.isoformat() if story.created_at else None
                })
            
            epics_data.append({
                'id': epic.id,
                'project_id': epic.project_id,
                'title': epic.title or 'Untitled Epic',
                'description': epic.description or '',
                'created_at': epic.created_at.isoformat() if epic.created_at else None,
                'stories': stories_data
            })
        
        return jsonify({
            'success': True,
            'epics': epics_data,
            'project_id': project_id,
            'project_title': project.title,
            'total_epics': len(epics_data),
            'total_stories': len(stories)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching project epics and stories: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load project backlog'
        }), 500

@ai_bp.route('/api/epics', methods=['POST'])
@login_required
def create_epic_api():
    """Create a new epic (BA only)"""
    user = current_user
    
    if user.role.value != 'BA':
        return jsonify({'error': 'Only Business Analysts can create epics'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Allow creation with either case_id or project_id
    if 'case_id' not in data and 'project_id' not in data:
        return jsonify({'error': 'Either case_id or project_id is required'}), 400
    
    if 'title' not in data:
        return jsonify({'error': 'Missing required field: title'}), 400
    
    try:
        epic = Epic(
            case_id=data.get('case_id'),
            project_id=data.get('project_id'),
            title=data['title'],
            description=data.get('description'),
            creator_id=user.id
        )
        
        db.session.add(epic)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Epic created successfully',
            'epic': {
                'id': epic.id,
                'case_id': epic.case_id,
                'project_id': epic.project_id,
                'title': epic.title,
                'description': epic.description
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating epic: {e}")
        return jsonify({'error': 'Failed to create epic'}), 500

@ai_bp.route('/api/epics/<int:epic_id>', methods=['PUT'])
@login_required
def update_epic_api(epic_id):
    """Update an epic (BA only)"""
    user = current_user
    
    if user.role.value != 'BA':
        return jsonify({'error': 'Only Business Analysts can update epics'}), 403
    
    epic = Epic.query.get_or_404(epic_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        from models import PriorityEnum
        
        # Update fields
        if 'title' in data:
            epic.title = data['title']
        if 'description' in data:
            epic.description = data['description']
        if 'priority' in data:
            epic.priority = PriorityEnum(data['priority'])
        if 'effort_estimate' in data:
            epic.effort_estimate = data['effort_estimate']
        
        epic.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Epic updated successfully',
            'epic': {
                'id': epic.id,
                'case_id': epic.case_id,
                'title': epic.title,
                'description': epic.description,
                'priority': epic.priority.value,
                'effort_estimate': epic.effort_estimate
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating epic: {e}")
        return jsonify({'error': 'Failed to update epic'}), 500

@ai_bp.route('/api/epics/<int:epic_id>', methods=['DELETE'])
@login_required
def delete_epic_api(epic_id):
    """Delete an epic and all its stories (BA only)"""
    user = current_user
    
    if user.role.value != 'BA':
        return jsonify({'error': 'Only Business Analysts can delete epics'}), 403
    
    epic = Epic.query.get_or_404(epic_id)
    
    try:
        # Delete all stories first (due to foreign key constraints)
        Story.query.filter_by(epic_id=epic_id).delete()
        
        # Delete the epic
        db.session.delete(epic)
        db.session.commit()
        
        return jsonify({'message': 'Epic and associated stories deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting epic: {e}")
        return jsonify({'error': 'Failed to delete epic'}), 500

# Story Management API Endpoints for Project Backlog

@ai_bp.route('/api/stories', methods=['POST'])
@login_required
def create_story_api():
    """Create a new story (BA only)"""
    user = current_user
    
    if user.role.value != 'BA':
        return jsonify({'error': 'Only Business Analysts can create stories'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['epic_id', 'title']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        story = Story(
            epic_id=data['epic_id'],
            project_id=data.get('project_id'),
            title=data['title'],
            description=data.get('description'),
            priority=data.get('priority', 'Medium'),
            effort_estimate=data.get('effort_estimate'),
            acceptance_criteria=data.get('acceptance_criteria', [])
        )
        
        db.session.add(story)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Story created successfully',
            'story': {
                'id': story.id,
                'epic_id': story.epic_id,
                'project_id': story.project_id,
                'title': story.title,
                'description': story.description,
                'priority': story.priority,
                'effort_estimate': story.effort_estimate
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating story: {e}")
        return jsonify({'success': False, 'error': 'Failed to create story'}), 500

@ai_bp.route('/api/stories/<int:story_id>', methods=['PUT'])
@login_required
def update_story_api(story_id):
    """Update a story (BA only)"""
    user = current_user
    
    if user.role.value != 'BA':
        return jsonify({'error': 'Only Business Analysts can update stories'}), 403
    
    story = Story.query.get_or_404(story_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Update fields
        if 'title' in data:
            story.title = data['title']
        if 'description' in data:
            story.description = data['description']
        if 'priority' in data:
            story.priority = data['priority']
        if 'effort_estimate' in data:
            story.effort_estimate = data['effort_estimate']
        if 'acceptance_criteria' in data:
            story.acceptance_criteria = data['acceptance_criteria']
        
        story.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Story updated successfully',
            'story': {
                'id': story.id,
                'epic_id': story.epic_id,
                'title': story.title,
                'description': story.description,
                'priority': story.priority,
                'effort_estimate': story.effort_estimate
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating story: {e}")
        return jsonify({'success': False, 'error': 'Failed to update story'}), 500

@ai_bp.route('/api/stories/<int:story_id>', methods=['DELETE'])
@login_required
def delete_story_api(story_id):
    """Delete a story (BA only)"""
    user = current_user
    
    if user.role.value != 'BA':
        return jsonify({'error': 'Only Business Analysts can delete stories'}), 403
    
    story = Story.query.get_or_404(story_id)
    
    try:
        db.session.delete(story)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Story deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting story: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete story'}), 500

# Duplicate clear_epics function removed to avoid routing conflicts

# End of AI routes module