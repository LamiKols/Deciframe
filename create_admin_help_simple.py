#!/usr/bin/env python3
"""
Simple Admin Help Articles Creator
Directly creates help articles for admin functionalities
"""

import os
import sys
sys.path.append('/home/runner/workspace')

from app import create_app, db
from models import HelpCategory, HelpArticle, User, RoleEnum
from datetime import datetime

def create_admin_help():
    """Create admin help articles directly"""
    
    app = create_app()
    with app.app_context():
        # Get admin user
        admin_user = User.query.filter_by(role=RoleEnum.Admin).first()
        if not admin_user:
            print("❌ No admin user found")
            return False
            
        print(f"✅ Found admin user: {admin_user.email}")
        
        # Create new categories for admin help
        admin_categories = [
            {
                'name': 'User Management',
                'description': 'Creating, editing, and managing user accounts and roles',
                'sort_order': 10
            },
            {
                'name': 'System Configuration', 
                'description': 'Application settings and system configuration',
                'sort_order': 11
            },
            {
                'name': 'Workflow Management',
                'description': 'Business process configuration and automation',
                'sort_order': 12
            },
            {
                'name': 'Data Management',
                'description': 'Import, export, and data analytics tools',
                'sort_order': 13
            },
            {
                'name': 'Organizational Structure',
                'description': 'Department management and organizational hierarchy',
                'sort_order': 14
            }
        ]
        
        # Create categories
        categories = {}
        for cat_data in admin_categories:
            existing_cat = HelpCategory.query.filter_by(
                name=cat_data['name'],
                organization_id=admin_user.organization_id
            ).first()
            
            if not existing_cat:
                category = HelpCategory(
                    name=cat_data['name'],
                    description=cat_data['description'],
                    sort_order=cat_data['sort_order'],
                    organization_id=admin_user.organization_id,
                    created_by_id=admin_user.id,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.session.add(category)
                print(f"✅ Created category: {cat_data['name']}")
            else:
                category = existing_cat
                print(f"📋 Using existing category: {cat_data['name']}")
                
            categories[cat_data['name']] = category
        
        db.session.commit()
        
        # Create admin help articles
        admin_articles = [
            {
                'category': 'User Management',
                'title': 'Creating and Managing User Accounts',
                'content': '''# Creating and Managing User Accounts

This guide covers the complete process of user account management in DeciFrame.

## Creating New Users

### Step-by-Step Process
1. **Navigate to User Management**
   - Go to Admin Center → Users
   - Click "Create New User" button

2. **Complete User Information**
   - **Personal Details**: Full name, email address, phone number
   - **Role Assignment**: Select appropriate role from dropdown
   - **Department Placement**: Assign to organizational unit
   - **Access Configuration**: Set account status and permissions

3. **Save and Activate**
   - Review all information for accuracy
   - Click "Save" to create the user
   - System generates welcome email automatically

### Required Information
- Full name (display name for the system)
- Email address (must be unique and business email)
- Role assignment (determines access level and permissions)
- Department placement (links user to organizational structure)

## Managing Existing Users

### User Profile Updates
1. **Locate User**: Use search functionality or browse user list
2. **Edit Information**: Click "Edit" next to user name
3. **Update Fields**: Modify any field as needed
4. **Save Changes**: Changes take effect immediately

### Common Management Tasks
- **Role Changes**: Update user permissions and access levels
- **Department Transfers**: Move users between organizational units
- **Account Status**: Activate, deactivate, or manage user access
- **Contact Updates**: Maintain current user information

## Best Practices
- Regular review of user information accuracy
- Prompt updates for role changes and transfers
- Maintain current contact information
- Document significant changes in user notes
- Follow organizational security policies

Effective user management ensures proper access control and workflow routing throughout DeciFrame.''',
                'meta_description': 'Complete guide to creating, editing, and managing user accounts in DeciFrame',
                'sort_order': 1
            },
            {
                'category': 'User Management', 
                'title': 'Understanding User Roles and Permissions',
                'content': '''# Understanding User Roles and Permissions

DeciFrame uses a comprehensive role-based access control system with six distinct user roles.

## User Roles Overview

### Staff Role
- **Purpose**: Front-line employees who identify problems and track solutions
- **Permissions**: Submit problems, view assigned tasks, update personal items
- **Typical Users**: General employees, end users, individual contributors

### Manager Role
- **Purpose**: Team supervision and departmental decision-making
- **Permissions**: All Staff permissions plus team oversight and departmental approvals
- **Typical Users**: Team leads, department supervisors, middle management

### BA (Business Analyst) Role
- **Purpose**: Problem analysis and business case development
- **Permissions**: Problem investigation, business case creation, requirements gathering
- **Typical Users**: Business analysts, process improvement specialists

### Director Role
- **Purpose**: Strategic oversight and high-value decision approval
- **Permissions**: All BA permissions plus strategic approvals and executive reporting
- **Typical Users**: Department directors, senior managers, division heads

### CEO Role
- **Purpose**: Ultimate executive authority and organizational oversight
- **Permissions**: All Director permissions plus final approval authority
- **Typical Users**: C-level executives, company owners, board members

### PM (Project Manager) Role
- **Purpose**: Project execution and deliverable management
- **Permissions**: Project planning, milestone tracking, resource allocation
- **Typical Users**: Project managers, program coordinators, delivery managers

### Admin Role
- **Purpose**: Complete system administration and configuration
- **Permissions**: Full system access, user management, system configuration
- **Typical Users**: IT administrators, system managers, technical leads

## Role Assignment Guidelines
- Match role to actual job responsibilities
- Consider approval authority levels and financial limits
- Account for required data access and security clearance
- Plan for career progression and role advancement paths

## Security Best Practices
- Apply principle of least privilege
- Regular role reviews and audits
- Document role assignment rationale
- Implement proper change management procedures

Understanding these roles ensures proper access control and workflow efficiency throughout your organization.''',
                'meta_description': 'Comprehensive guide to DeciFrame user roles, permissions, and assignment best practices',
                'sort_order': 2
            },
            {
                'category': 'System Configuration',
                'title': 'Organization Settings and Preferences',
                'content': '''# Organization Settings and Preferences

Configure company-wide settings that affect how DeciFrame displays information and handles business processes.

## Accessing Organization Settings
Navigate to **Admin Center → Organization Settings** to access all configuration options.

## Currency Configuration

### Setting Primary Currency
1. **Select Currency**: Choose from supported international currencies
   - USD (US Dollar), EUR (Euro), GBP (British Pound)
   - CAD (Canadian Dollar), AUD (Australian Dollar)
   - And many more regional currencies

2. **Display Options**:
   - Symbol position (before or after amounts)
   - Decimal places (0, 2, or 3 decimal precision)
   - Thousands separator (comma, period, or space)
   - Negative format options

### Currency Impact
- Business case ROI calculations and budget displays
- Project cost tracking and financial reporting
- System-wide monetary displays and thresholds
- Automatic case upgrade financial limits

## Date Format Configuration

### Available Format Options

#### US Format (MM/DD/YYYY)
- Display: 12/25/2024
- Best for: American organizations
- Benefits: Familiar to US users

#### European Format (DD/MM/YYYY)
- Display: 25/12/2024  
- Best for: European and international organizations
- Benefits: International standard compatibility

#### ISO Format (YYYY-MM-DD)
- Display: 2024-12-25
- Best for: Technical organizations, data analysis
- Benefits: Sortable, unambiguous, international standard

#### Long Format (Month DD, YYYY)
- Display: December 25, 2024
- Best for: Formal documents, executive reports
- Benefits: Clear, readable, professional appearance

## Timezone Management
- Set organization primary timezone
- Enable automatic daylight saving time adjustment
- Allow user personal timezone preferences
- Ensure accurate timestamp recording and display

## Theme and Display Settings
- Light theme (traditional interface)
- Dark theme (modern, reduced eye strain)
- Auto theme (follows user system preferences)
- Organization default with user override options

## Best Practices
- Consult key stakeholders before making format changes
- Test thoroughly in all contexts before finalizing
- Document configuration decisions for future reference
- Communicate changes well in advance to users
- Consider needs of multi-regional organizations

Proper organization settings ensure consistent, professional system operation that meets your specific business requirements.''',
                'meta_description': 'Configure organization-wide settings including currency, date formats, timezones, and themes',
                'sort_order': 1
            },
            {
                'category': 'Workflow Management',
                'title': 'Business Process Configuration',
                'content': '''# Business Process Configuration

Configure automated business processes and workflow parameters to match your organization's operational requirements.

## Core Workflow Settings

### Full Case Threshold Configuration
The Full Case Threshold determines when problems require detailed business case development.

**Setting the Threshold**:
1. Navigate to Admin Center → Workflows → Configuration
2. Locate "Full Case Threshold" setting
3. Enter monetary amount (default: $25,000)
4. Save configuration

**Impact**:
- Above threshold: Requires detailed business case with ROI analysis
- Below threshold: Simplified light case process
- Automatic routing based on financial impact
- Different approval requirements by value

### Assignment Timeout Configuration

#### BA Assignment Timeout
- Controls automatic escalation when cases aren't assigned
- Default: 72 hours before escalation
- Escalates to Manager or Director level
- Configurable notification schedule

#### Director Approval Timeout
- Manages escalation for pending executive approvals
- Default: 72 hours for director decisions
- Escalates to CEO or Board level
- Optional auto-approval for certain criteria

### Notification Workflow Settings
- Email notification configuration and templates
- SMS integration for critical alerts
- Frequency controls to prevent spam
- Role-based notification routing

## Advanced Workflow Features

### Conditional Routing
Set up intelligent workflow routing based on:
- Problem financial impact and value
- Originating department and team
- Problem category and classification
- Submitter role and authority level

### Escalation Management
Configure multi-level escalation:
- Time-based automatic escalation
- Value-based escalation triggers
- Resource availability escalation
- Manual escalation override options

## Workflow Monitoring
- Processing time metrics and analysis
- Bottleneck identification and resolution
- Success rate tracking and optimization
- User and team performance metrics

## Best Practices
- Start with conservative timeouts, adjust based on experience
- Monitor performance metrics before making changes
- Involve process users in configuration decisions
- Document configuration rationale and changes
- Test changes in non-production environment first
- Maintain audit trails for compliance requirements

Proper workflow configuration ensures efficient business process automation while maintaining necessary controls and oversight.''',
                'meta_description': 'Configure business process workflows, thresholds, and automation in DeciFrame',
                'sort_order': 1
            },
            {
                'category': 'Data Management',
                'title': 'Bulk Data Import and Export System',
                'content': '''# Bulk Data Import and Export System

Efficiently manage large datasets using DeciFrame's comprehensive import and export capabilities.

## Data Import System

### Supported Import Types
- **User Accounts**: Complete user information and role assignments
- **Organizational Structure**: Departments and hierarchical relationships
- **Historical Problems**: Past problem records and resolutions
- **Project Data**: Project information and milestone tracking
- **Business Cases**: Existing business case information

### Import Process
1. **Preparation**: Download CSV template for data type
2. **Data Preparation**: Format data according to template requirements
3. **File Upload**: Upload prepared CSV file to system
4. **Column Mapping**: Map your data columns to DeciFrame fields
5. **Validation**: System validates data quality and relationships
6. **Execution**: Process import with real-time progress tracking
7. **Review**: Examine results and resolve any errors

### Import Best Practices
- **Data Quality**: Ensure clean, consistent source data
- **Template Usage**: Always use provided CSV templates
- **Validation**: Verify required fields and data formats
- **Testing**: Test with small datasets before large imports
- **Backup**: Create system backup before major imports
- **Timing**: Schedule large imports during off-peak hours

## Data Export System

### Available Export Types
- **Organizational Data**: Structure, users, and relationships
- **Business Process Data**: Problems, cases, and projects
- **Analytics Reports**: Usage statistics and performance metrics
- **Audit Trails**: Complete system activity logs
- **Custom Reports**: Filtered data based on specific criteria

### Export Formats
- **CSV**: For data analysis and spreadsheet import
- **PDF**: For formal reports and documentation
- **Excel**: For advanced analysis with multiple worksheets
- **JSON**: For system integration and API consumption

### Export Configuration
- **Date Range Filtering**: Specific time periods
- **Content Filtering**: Department, role, or status-based
- **Privacy Controls**: Respect data privacy and permissions
- **Format Options**: Customize output format and structure

## Advanced Features

### Scheduled Operations
- **Automated Imports**: Regular data synchronization
- **Scheduled Exports**: Recurring report generation
- **Monitoring**: Track scheduled operation success
- **Notifications**: Alerts for operation completion or failure

### Data Quality Management
- **Validation Rules**: Enforce data integrity during import
- **Duplicate Detection**: Identify and handle duplicate records
- **Error Reporting**: Detailed error analysis and resolution
- **Data Cleansing**: Automatic data format standardization

## Security and Compliance
- **Access Control**: Limit import/export permissions
- **Audit Logging**: Track all data operations
- **Data Privacy**: Protect sensitive information
- **Compliance Reporting**: Support regulatory requirements

The comprehensive data management system provides powerful tools for efficient data migration, backup, analysis, and compliance reporting while maintaining security and performance standards.''',
                'meta_description': 'Guide to bulk data import, export, and management capabilities in DeciFrame',
                'sort_order': 1
            }
        ]
        
        # Create articles
        created_count = 0
        for article_data in admin_articles:
            category = categories.get(article_data['category'])
            if not category:
                print(f"⚠️ Category not found: {article_data['category']}")
                continue
                
            # Check if article exists
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
                    role_restrictions=['Admin'],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                # Generate slug
                slug_base = article_data['title'].lower().replace(' ', '-').replace('&', 'and')
                # Remove special characters
                import re
                slug = re.sub(r'[^a-z0-9\-]', '', slug_base)
                article.slug = slug
                
                db.session.add(article)
                created_count += 1
                print(f"✅ Created article: {article_data['title']}")
            else:
                print(f"📄 Article exists: {article_data['title']}")
        
        try:
            db.session.commit()
            print(f"\n🎉 Successfully created {created_count} new admin help articles")
            
            # Show final counts
            total_categories = HelpCategory.query.filter_by(organization_id=admin_user.organization_id).count()
            total_articles = HelpArticle.query.filter_by(organization_id=admin_user.organization_id).count()
            
            print(f"📊 Total categories: {total_categories}")
            print(f"📚 Total articles: {total_articles}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating help articles: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = create_admin_help()
    sys.exit(0 if success else 1)