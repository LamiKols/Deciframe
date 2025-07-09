"""
Contextual Help Placement Strategy for DeciFrame
Defines where help icons should appear and why
"""

# Contextual Help Placement Rules
CONTEXTUAL_HELP_AREAS = {
    'admin_dashboard': {
        'priority': 'high',
        'placements': [
            {
                'element': 'dashboard_title',
                'help_url': '/help?module=Admin&section=overview',
                'tooltip': 'Help with admin dashboard overview',
                'icon_size': '0.8em',
                'reason': 'Entry point - users need orientation'
            },
            {
                'element': 'user_management_card',
                'help_url': '/help?module=Admin&section=users',
                'tooltip': 'Help with user management',
                'icon_size': '0.75em',
                'reason': 'Complex feature requiring role understanding'
            },
            {
                'element': 'department_management_card',
                'help_url': '/help?module=Admin&section=departments',
                'tooltip': 'Help with department management',
                'icon_size': '0.75em',
                'reason': 'Hierarchical structure can be confusing'
            },
            {
                'element': 'business_cases_card',
                'help_url': '/help?module=Business&section=cases',
                'tooltip': 'Help with business case management',
                'icon_size': '0.75em',
                'reason': 'Core business feature with workflow complexity'
            },
            {
                'element': 'projects_card',
                'help_url': '/help?module=Projects&section=management',
                'tooltip': 'Help with project management',
                'icon_size': '0.75em',
                'reason': 'Project lifecycle management guidance needed'
            },
            {
                'element': 'triage_rules_card',
                'help_url': '/help?module=Admin&section=triage',
                'tooltip': 'Help with triage configuration',
                'icon_size': '0.75em',
                'reason': 'Automation rules require technical understanding'
            },
            {
                'element': 'quick_actions_section',
                'help_url': '/help?module=Admin&section=quick-actions',
                'tooltip': 'Help with admin quick actions',
                'icon_size': '0.8em',
                'reason': 'Feature discovery for admin shortcuts'
            }
        ]
    },
    'user_management': {
        'priority': 'high',
        'placements': [
            {
                'element': 'user_creation_form',
                'help_url': '/help?module=Admin&section=user-creation',
                'tooltip': 'Help with creating new users',
                'reason': 'Role assignment and permissions are complex'
            },
            {
                'element': 'role_assignment',
                'help_url': '/help?module=Admin&section=roles',
                'tooltip': 'Help with user roles and permissions',
                'reason': 'Role hierarchy and permissions matrix'
            }
        ]
    },
    'business_cases': {
        'priority': 'medium',
        'placements': [
            {
                'element': 'case_creation_form',
                'help_url': '/help?module=Business&section=creation',
                'tooltip': 'Help with creating business cases',
                'reason': 'ROI calculations and approval workflows'
            },
            {
                'element': 'epic_management',
                'help_url': '/help?module=Business&section=epics',
                'tooltip': 'Help with epic and story management',
                'reason': 'AI-powered requirements generation'
            }
        ]
    },
    'projects': {
        'priority': 'medium',
        'placements': [
            {
                'element': 'milestone_tracking',
                'help_url': '/help?module=Projects&section=milestones',
                'tooltip': 'Help with milestone management',
                'reason': 'Project tracking and reporting features'
            }
        ]
    }
}

# Help Content Mapping
HELP_CONTENT_STRUCTURE = {
    'Admin': {
        'overview': 'Admin Dashboard Overview and Navigation',
        'users': 'User Management and Role Assignment',
        'departments': 'Department Hierarchy and Organization',
        'triage': 'Automated Triage Rules Configuration',
        'quick-actions': 'Admin Quick Actions and Shortcuts',
        'workflows': 'Workflow Template Management',
        'settings': 'Organization Settings and Preferences'
    },
    'Business': {
        'cases': 'Business Case Management Overview',
        'creation': 'Creating and Submitting Business Cases',
        'epics': 'Epic and User Story Management',
        'approval': 'Business Case Approval Workflow'
    },
    'Projects': {
        'management': 'Project Management Overview',
        'milestones': 'Milestone Tracking and Reporting',
        'conversion': 'Converting Business Cases to Projects'
    },
    'Problems': {
        'management': 'Problem Tracking and Resolution',
        'reporting': 'Problem Submission and Classification'
    }
}

def should_show_help_icon(page_type, element_type, user_role):
    """
    Determine if a help icon should be shown based on context
    
    Args:
        page_type: Type of page (admin_dashboard, user_management, etc.)
        element_type: Specific element (user_card, department_card, etc.)
        user_role: Current user's role
    
    Returns:
        dict: Help configuration or None
    """
    if page_type not in CONTEXTUAL_HELP_AREAS:
        return None
    
    page_config = CONTEXTUAL_HELP_AREAS[page_type]
    
    # Find matching element configuration
    for placement in page_config['placements']:
        if placement['element'] == element_type:
            return placement
    
    return None

def get_help_url(module, section):
    """Generate help URL for given module and section"""
    return f"/help?module={module}&section={section}"

def get_contextual_help_config():
    """Return complete contextual help configuration"""
    return {
        'areas': CONTEXTUAL_HELP_AREAS,
        'content': HELP_CONTENT_STRUCTURE
    }