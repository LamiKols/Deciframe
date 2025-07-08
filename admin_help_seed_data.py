#!/usr/bin/env python3
"""
Admin Help Articles Seed Data Generator
Creates comprehensive help articles for all admin functionalities
"""

from app import create_app, db
from models import HelpCategory, HelpArticle, User, RoleEnum
from flask_login import login_user
from datetime import datetime
import sys

def create_admin_help_articles():
    """Create comprehensive admin help articles"""
    
    app = create_app()
    with app.app_context():
        # Find admin user for article creation
        admin_user = User.query.filter_by(role=RoleEnum.Admin).first()
        if not admin_user:
            print("❌ No admin user found. Please create an admin user first.")
            return False
            
        print(f"✅ Using admin user: {admin_user.email}")
        
        # Create or get admin categories
        categories_data = [
            {
                'name': 'Admin Dashboard',
                'description': 'Dashboard overview and navigation guides',
                'sort_order': 1
            },
            {
                'name': 'User Management', 
                'description': 'Creating, editing, and managing user accounts',
                'sort_order': 2
            },
            {
                'name': 'Organizational Structure',
                'description': 'Department management and organizational hierarchy',
                'sort_order': 3
            },
            {
                'name': 'System Configuration',
                'description': 'Application settings and system configuration',
                'sort_order': 4
            },
            {
                'name': 'Workflow Management',
                'description': 'Business process configuration and automation',
                'sort_order': 5
            },
            {
                'name': 'Data Management',
                'description': 'Import, export, and data analytics tools',
                'sort_order': 6
            },
            {
                'name': 'Help Center Management',
                'description': 'Managing knowledge base content and categories',
                'sort_order': 7
            },
            {
                'name': 'Security & Compliance',
                'description': 'Security settings and compliance tools',
                'sort_order': 8
            },
            {
                'name': 'Reports & Monitoring',
                'description': 'System reports and performance monitoring',
                'sort_order': 9
            }
        ]
        
        # Create categories
        categories = {}
        for cat_data in categories_data:
            category = HelpCategory.query.filter_by(
                name=cat_data['name'],
                organization_id=admin_user.organization_id
            ).first()
            
            if not category:
                category = HelpCategory(
                    name=cat_data['name'],
                    description=cat_data['description'],
                    sort_order=cat_data['sort_order'],
                    organization_id=admin_user.organization_id,
                    created_by_id=admin_user.id
                )
                db.session.add(category)
                print(f"✅ Created category: {cat_data['name']}")
            else:
                print(f"📋 Category exists: {cat_data['name']}")
                
            categories[cat_data['name']] = category
        
        db.session.commit()
        
        # Define comprehensive help articles
        articles_data = [
            # Admin Dashboard Articles
            {
                'category': 'Admin Dashboard',
                'title': 'Getting Started with the Admin Dashboard',
                'content': '''# Getting Started with the Admin Dashboard

The Admin Dashboard is your central command center for managing DeciFrame. Here you'll find everything you need to effectively administer your organization's workflow management system.

## Key Dashboard Features

### System Statistics
Monitor your organization's key metrics at a glance:
- **Total Users**: Current active user count across all roles
- **Departments**: Number of organizational units in your structure  
- **Active Problems**: Current problems awaiting resolution
- **Projects**: Active projects and their status
- **Business Cases**: Cases in various approval stages

### Health Metrics
Track system performance with real-time indicators:
- **Application Status**: Overall system health
- **Database Performance**: Query response times and connectivity
- **Service Availability**: Critical service status
- **Error Rates**: System error monitoring and alerts

### Quick Actions Panel
Access frequently used admin functions directly:
- **User Management**: Create and manage user accounts
- **Data Import**: Bulk data upload and processing
- **Workflow Configuration**: Business process setup
- **Organizational Chart**: Visual structure management
- **System Settings**: Application configuration

## Navigation Tips

1. **Bookmark the Dashboard**: Set as your homepage for quick access
2. **Use Quick Actions**: Faster than navigating through menus
3. **Monitor Alerts**: Check regularly for system notifications
4. **Review Statistics**: Daily monitoring helps identify trends

## Getting Help

- Click the Help icon (❓) for context-sensitive assistance
- Visit the Help Center for detailed documentation
- Contact system administrators for technical support

The dashboard updates in real-time, providing current information for informed decision-making.''',
                'meta_description': 'Learn how to navigate and use the DeciFrame Admin Dashboard effectively for system management',
                'sort_order': 1,
                'role_restrictions': ['Admin']
            },
            {
                'category': 'Admin Dashboard',
                'title': 'Using Quick Actions for Maximum Efficiency',
                'content': '''# Using Quick Actions for Maximum Efficiency

The Quick Actions panel streamlines admin workflows by providing direct access to essential functions without menu navigation.

## Available Quick Actions

### User Management Actions
- **Users Button**: Direct access to user list with search and filtering
- **Create User**: Skip to user creation form immediately  
- **Role Management**: Quick access to role assignment interface
- **Department Assignment**: Fast organizational structure updates

### Data Operation Actions
- **Import Data**: Launch bulk import wizard
  - Supports CSV file uploads
  - Automatic column mapping
  - Progress tracking and error reporting
- **Export Data**: Generate system reports
  - Multiple format options (CSV, PDF, Excel)
  - Custom date ranges and filters
  - Scheduled export capabilities

### System Configuration Actions
- **Workflows**: Configure business process automation
  - Triage rule management
  - Approval workflow setup
  - Notification configuration
- **Settings**: System-wide preferences
  - Organization settings
  - Currency and date formats
  - Theme and display options
- **Help Center**: Knowledge base management
  - Article creation and editing
  - Category organization
  - Content publishing controls

## Efficiency Tips

### Keyboard Shortcuts
- **Alt + U**: Quick user management
- **Alt + I**: Import data wizard
- **Alt + W**: Workflow configuration
- **Alt + S**: System settings
- **Alt + H**: Help center management

### Workflow Optimization
1. **Bookmark Frequent Actions**: Use browser bookmarks for daily tasks
2. **Batch Operations**: Group similar tasks for efficiency
3. **Monitor Progress**: Use real-time indicators during long operations
4. **Context Switching**: Quick Actions maintain your place in workflows

### Best Practices
- **Regular Monitoring**: Check system status daily
- **Proactive Management**: Address alerts promptly
- **Documentation**: Keep notes on configuration changes
- **User Training**: Share efficiency tips with other administrators

Quick Actions save significant time and reduce navigation complexity for routine administrative tasks.''',
                'meta_description': 'Master the Quick Actions panel for efficient DeciFrame system administration',
                'sort_order': 2,
                'role_restrictions': ['Admin']
            },
            
            # User Management Articles
            {
                'category': 'User Management',
                'title': 'Creating and Managing User Accounts',
                'content': '''# Creating and Managing User Accounts

Effective user management ensures proper access control and workflow routing throughout DeciFrame.

## Creating New Users

### Step-by-Step User Creation
1. **Navigate to User Management**
   - Go to Admin Center → Users
   - Click "Create New User" button
   
2. **Complete User Information**
   - **Personal Details**:
     - Full name (required)
     - Email address (must be unique and business email)
     - Phone number (optional but recommended)
     - Employee ID (if applicable)
   
   - **Role Assignment**:
     - Select appropriate role from dropdown
     - Consider user's job responsibilities
     - Plan for potential role progression
   
   - **Department Placement**:
     - Choose from organizational structure
     - Ensures proper workflow routing
     - Enables correct approval chains
   
   - **Access Configuration**:
     - Set account status (Active/Inactive)
     - Configure notification preferences
     - Set password requirements

3. **Validation and Creation**
   - Review all information for accuracy
   - Click "Save" to create the user
   - System generates welcome email automatically

### Required vs Optional Fields
**Required Information:**
- Full name
- Email address  
- Role assignment
- Department placement

**Optional but Recommended:**
- Phone number for notifications
- Employee ID for integration
- Profile photo for identification
- Additional contact information

## Managing Existing Users

### User Profile Updates
1. **Locate User**
   - Use search functionality for large user lists
   - Filter by role, department, or status
   - Sort by name, email, or creation date

2. **Edit User Information**
   - Click "Edit" next to user name
   - Update any field as needed
   - Changes take effect immediately upon saving

### Common Management Tasks

#### Role Changes
- **Process**: Edit user → Change role → Save
- **Impact**: Immediate permission changes
- **Considerations**: Workflow disruption, training needs

#### Department Transfers
- **Process**: Edit user → Select new department → Update
- **Effects**: Changes approval routing and reporting
- **Follow-up**: Update any department-specific assignments

#### Account Status Management
- **Deactivation**: Removes system access while preserving data
- **Reactivation**: Restores full access with previous settings
- **Deletion**: Permanent removal (use with caution)

## Best Practices

### User Creation Guidelines
- **Consistent Naming**: Use standard name formats
- **Email Validation**: Verify business email addresses
- **Role Planning**: Consider growth and succession planning
- **Documentation**: Maintain user creation logs

### Ongoing Management
- **Regular Reviews**: Quarterly user access audits
- **Prompt Updates**: Process role changes immediately
- **Security Monitoring**: Track login patterns and access
- **Training Coordination**: Ensure users understand their roles

### Data Privacy Considerations
- **Information Protection**: Secure personal data handling
- **Access Logging**: Track who modifies user accounts
- **Compliance**: Follow organizational privacy policies
- **Retention**: Establish data retention guidelines

Proper user management ensures system security, workflow efficiency, and regulatory compliance.''',
                'meta_description': 'Complete guide to creating, editing, and managing user accounts in DeciFrame',
                'sort_order': 1,
                'role_restrictions': ['Admin']
            },
            {
                'category': 'User Management',
                'title': 'Understanding User Roles and Permissions',
                'content': '''# Understanding User Roles and Permissions

DeciFrame implements a comprehensive role-based access control system with six distinct user roles, each designed for specific organizational functions.

## Complete Role Breakdown

### Staff Role
**Purpose**: Front-line employees who identify problems and track solutions

**Core Permissions**:
- Submit new problems and requests
- View assigned tasks and projects
- Update personal work items
- Access basic reporting features
- Participate in workflow processes

**Typical Users**: General employees, end users, individual contributors

**Workflow Participation**:
- Problem submission and tracking
- Task completion and updates
- Basic project participation
- Personal dashboard access

### Manager Role  
**Purpose**: Team supervision and departmental decision-making

**Core Permissions**:
- All Staff permissions
- Team oversight and coordination
- Departmental approval authority
- Team member task assignment
- Departmental reporting access

**Typical Users**: Team leads, department supervisors, middle management

**Additional Capabilities**:
- Approve departmental requests
- Assign work to team members
- Access team performance metrics
- Manage departmental workflows

### BA (Business Analyst) Role
**Purpose**: Problem analysis and business case development

**Core Permissions**:
- Problem investigation and analysis
- Business case creation and management
- Requirements gathering and documentation
- Solution recommendation development
- Cross-departmental collaboration

**Typical Users**: Business analysts, process improvement specialists, solution architects

**Specialized Functions**:
- Detailed problem analysis
- ROI calculations and business case development
- Stakeholder requirement gathering
- Solution evaluation and recommendation

### Director Role
**Purpose**: Strategic oversight and high-value decision approval

**Core Permissions**:
- All BA permissions
- Strategic business case approval
- High-value project authorization
- Cross-departmental coordination
- Executive reporting access

**Typical Users**: Department directors, senior managers, division heads

**Executive Functions**:
- Approve business cases over threshold amounts
- Strategic project portfolio oversight
- Resource allocation decisions
- Executive dashboard access

### CEO Role
**Purpose**: Ultimate executive authority and organizational oversight

**Core Permissions**:
- All Director permissions
- Final approval authority
- Organization-wide visibility
- Strategic planning access
- Complete reporting suite

**Typical Users**: C-level executives, company owners, board members

**Top-Level Capabilities**:
- Final approval on major initiatives
- Complete organizational visibility
- Strategic planning and direction
- Ultimate escalation authority

### PM (Project Manager) Role
**Purpose**: Project execution and deliverable management

**Core Permissions**:
- Project planning and coordination
- Milestone tracking and management
- Resource allocation and scheduling
- Project reporting and analytics
- Team coordination across departments

**Typical Users**: Project managers, program coordinators, delivery managers

**Project-Specific Functions**:
- Create and manage project plans
- Track deliverables and milestones
- Coordinate cross-functional teams
- Monitor project performance metrics

### Admin Role
**Purpose**: Complete system administration and configuration

**Core Permissions**:
- Full system access and control
- User account management
- System configuration and settings
- Security and compliance management
- Technical administration

**Typical Users**: IT administrators, system managers, technical leads

**Administrative Functions**:
- User creation and role assignment
- System configuration and maintenance
- Security policy implementation
- Data management and backup
- Technical troubleshooting and support

## Role Assignment Best Practices

### Selection Criteria
1. **Job Responsibilities**: Match role to actual duties
2. **Approval Authority**: Consider financial and operational limits
3. **Data Access Needs**: Evaluate required information access
4. **Career Progression**: Plan for role advancement paths

### Implementation Guidelines
- **Start Conservatively**: Begin with minimal required permissions
- **Regular Reviews**: Quarterly role assessment and adjustment
- **Documentation**: Maintain role assignment rationale
- **Training**: Ensure users understand their role capabilities

### Security Considerations
- **Principle of Least Privilege**: Grant minimum necessary access
- **Separation of Duties**: Avoid conflicting role combinations
- **Regular Audits**: Monitor role usage and effectiveness
- **Change Management**: Document all role modifications

Understanding these roles ensures proper access control and workflow efficiency throughout your organization.''',
                'meta_description': 'Comprehensive guide to DeciFrame user roles, permissions, and role assignment best practices',
                'sort_order': 2,
                'role_restrictions': ['Admin']
            },
            
            # System Configuration Articles
            {
                'category': 'System Configuration',
                'title': 'Organization Settings and Preferences',
                'content': '''# Organization Settings and Preferences

Configure company-wide settings that affect how DeciFrame displays information and handles business processes across your organization.

## Accessing Organization Settings

Navigate to **Admin Center → Organization Settings** to access all configuration options.

## Currency Configuration

### Setting Primary Currency
1. **Select Currency**: Choose from supported currencies
   - USD (US Dollar)
   - EUR (Euro)
   - GBP (British Pound)
   - CAD (Canadian Dollar)
   - AUD (Australian Dollar)
   - And many more...

2. **Currency Display Options**:
   - **Symbol Position**: Before or after amounts
   - **Decimal Places**: 0, 2, or 3 decimal precision
   - **Thousands Separator**: Comma, period, or space
   - **Negative Format**: Parentheses, minus sign, or color coding

3. **Regional Formatting**:
   - Automatic formatting based on currency selection
   - Custom format override options
   - Consistent display across all modules

### Impact of Currency Settings
- **Business Cases**: ROI calculations and budget displays
- **Project Budgets**: Cost tracking and reporting
- **Financial Reports**: All monetary displays
- **Threshold Settings**: Automatic case upgrade limits

## Date Format Configuration

### Available Format Options

#### US Format (MM/DD/YYYY)
- **Display**: 12/25/2024
- **Use Case**: American organizations
- **Benefits**: Familiar to US users

#### European Format (DD/MM/YYYY)  
- **Display**: 25/12/2024
- **Use Case**: European and international organizations
- **Benefits**: International standard compatibility

#### ISO Format (YYYY-MM-DD)
- **Display**: 2024-12-25
- **Use Case**: Technical organizations, data analysis
- **Benefits**: Sortable, unambiguous, international standard

#### Long Format (Month DD, YYYY)
- **Display**: December 25, 2024
- **Use Case**: Formal documents, executive reports
- **Benefits**: Clear, readable, professional appearance

### Date Format Impact
- **System-Wide Application**: All dates display in selected format
- **Reports and Exports**: Consistent formatting across outputs
- **User Interface**: Dashboard, lists, and detail views
- **Email Notifications**: Automated communications

## Timezone Management

### Setting Organization Timezone
1. **Primary Timezone**: Select your organization's main timezone
2. **Automatic DST**: Enable automatic daylight saving time adjustment
3. **User Overrides**: Allow users to set personal timezone preferences

### Timezone Features
- **Automatic Conversion**: System timestamps adjust to user preferences
- **Meeting Scheduling**: Proper timezone handling for cross-location teams
- **Report Generation**: Consistent time references
- **Audit Logging**: Accurate timestamp recording

## Theme and Display Settings

### Theme Options
- **Light Theme**: Traditional white background interface
- **Dark Theme**: Modern dark interface for reduced eye strain
- **Auto Theme**: Follows user system preferences
- **Organization Default**: Set company-wide default theme

### Display Preferences
- **User Theme Override**: Allow personal theme selection
- **Branding Integration**: Custom colors and logo options
- **Interface Density**: Compact vs. comfortable spacing
- **Navigation Style**: Menu layout and organization

## Advanced Configuration

### Business Rules Integration
- **Full Case Threshold**: Monetary amount triggering detailed business cases
- **Approval Workflows**: Currency-aware approval routing
- **Reporting Periods**: Date format affects period calculations
- **Data Export**: Format settings apply to exported data

### System Performance
- **Caching**: Settings cached for performance
- **Real-time Updates**: Changes apply immediately
- **Backup**: Settings included in system backups
- **Audit Trail**: All changes logged for compliance

## Best Practices

### Initial Setup
1. **Consult Stakeholders**: Involve key users in format decisions
2. **Consider Integration**: Match existing system formats where possible
3. **Test Thoroughly**: Verify formats in all contexts before finalizing
4. **Document Decisions**: Record rationale for future reference

### Ongoing Management
- **Regular Review**: Quarterly assessment of setting effectiveness
- **User Feedback**: Monitor user satisfaction with format choices
- **Change Management**: Communicate format changes well in advance
- **Training**: Ensure all users understand format implications

### Global Organizations
- **Multi-Region Support**: Consider needs of different locations
- **Standardization**: Balance consistency with local preferences
- **Compliance**: Ensure formats meet regulatory requirements
- **Communication**: Clear guidelines for multi-format environments

Proper organization settings ensure consistent, professional system operation that meets your organization's specific needs and preferences.''',
                'meta_description': 'Configure organization-wide settings including currency, date formats, timezones, and themes',
                'sort_order': 1,
                'role_restrictions': ['Admin']
            }
        ]
        
        # Create articles
        created_count = 0
        for article_data in articles_data:
            category = categories[article_data['category']]
            
            # Check if article already exists
            existing_article = HelpArticle.query.filter_by(
                title=article_data['title'],
                category_id=category.id,
                organization_id=admin_user.organization_id
            ).first()
            
            if not existing_article:
                article = HelpArticle(
                    title=article_data['title'],
                    content=article_data['content'],
                    meta_description=article_data['meta_description'],
                    category_id=category.id,
                    organization_id=admin_user.organization_id,
                    created_by_id=admin_user.id,
                    sort_order=article_data['sort_order'],
                    is_published=True,
                    role_restrictions=article_data.get('role_restrictions', [])
                )
                db.session.add(article)
                created_count += 1
                print(f"✅ Created article: {article_data['title']}")
            else:
                print(f"📄 Article exists: {article_data['title']}")
        
        try:
            db.session.commit()
            print(f"\n🎉 Successfully created {created_count} new help articles")
            print(f"📊 Total categories: {len(categories)}")
            print(f"📚 Total articles processed: {len(articles_data)}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating help articles: {str(e)}")
            return False

if __name__ == '__main__':
    success = create_admin_help_articles()
    sys.exit(0 if success else 1)