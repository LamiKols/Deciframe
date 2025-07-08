# DeciFrame Admin Center - Complete Help Articles

## Dashboard & Overview

### Admin Dashboard
**Getting Started with the Admin Dashboard**

The Admin Dashboard is your central command center for managing DeciFrame. Here you'll find:

- **System Statistics**: Real-time counts of users, departments, problems, and projects
- **Health Metrics**: System performance indicators and alerts
- **Quick Actions**: Fast access to all major admin functions
- **Pending Items**: Summary of items requiring your attention

Navigate to the dashboard by clicking "Admin Center" in the main navigation, then selecting "Dashboard".

### Quick Actions Panel
**Using Quick Actions for Efficient Administration**

The Quick Actions panel provides one-click access to:
- User management
- Data import/export
- Workflow configuration
- Organizational chart management
- System settings

Each button takes you directly to the relevant admin function, saving time on navigation.

## User Management

### User Creation & Editing
**Adding and Managing Users in DeciFrame**

To create a new user:
1. Navigate to Admin Center → Users
2. Click "Create New User"
3. Fill in required information:
   - Name and email address
   - Role assignment (Staff, Manager, BA, Director, CEO, PM, Admin)
   - Department placement
   - Contact information
4. Click "Save" to create the user

To edit existing users:
1. Find the user in the users list
2. Click "Edit" next to their name
3. Update information as needed
4. Save changes

### User Status Management
**Activating and Deactivating User Accounts**

Control user access by managing account status:

**To deactivate a user:**
1. Go to Admin Center → Users
2. Find the user in the list
3. Click the status toggle to deactivate
4. User will no longer be able to log in

**To reactivate a user:**
1. Follow the same steps
2. Toggle status back to active
3. User can log in again immediately

### Role Assignment
**Understanding and Assigning User Roles**

DeciFrame supports six user roles:

- **Staff**: Basic users who can submit problems and view assigned work
- **Manager**: Supervise teams and approve department-level decisions
- **BA (Business Analyst)**: Analyze problems and create business cases
- **Director**: Approve high-value business cases and strategic decisions
- **CEO**: Executive oversight and final approvals
- **PM (Project Manager)**: Manage projects and track deliverables
- **Admin**: Full system administration access

To change a user's role:
1. Edit the user profile
2. Select new role from dropdown
3. Save changes
4. Role takes effect immediately

### Department Assignment
**Linking Users to Organizational Units**

Proper department assignment ensures:
- Correct workflow routing
- Appropriate approval chains
- Accurate reporting and analytics

To assign departments:
1. Edit user profile
2. Select department from organizational structure
3. Choose primary department for the user
4. Save assignment

## Organizational Structure

### Department Management
**Creating and Managing Hierarchical Departments**

DeciFrame supports up to 5 levels of organizational hierarchy:

**Creating a new department:**
1. Go to Admin Center → Org Chart
2. Click "Create Org Unit"
3. Enter department information:
   - Department name
   - Description
   - Parent department (if applicable)
   - Manager assignment
4. Save the new department

**Managing existing departments:**
- Edit department details
- Move departments in hierarchy
- Assign managers
- Update descriptions and structure

### Organizational Chart
**Visualizing Your Company Structure**

The organizational chart provides:
- Interactive hierarchy visualization
- Drill-down capabilities
- Manager assignments
- Department relationships

Navigate using:
- Click to expand/collapse departments
- Hover for quick information
- Use search to find specific units

### Structure Import/Export
**Bulk Organizational Data Management**

**Importing organizational structure:**
1. Go to Admin Center → Data Import
2. Select "Organizational Structure"
3. Download the sample CSV template
4. Fill in your organization data
5. Upload and map columns
6. Review and confirm import

**Exporting structure:**
1. Go to Admin Center → Data Export
2. Select "Organizational Structure"
3. Choose format (CSV, PDF, Excel)
4. Download generated file

## System Configuration

### Organization Settings
**Configuring Company-Wide Preferences**

Access organization settings through Admin Center → Organization Settings:

**Currency Configuration:**
- Select primary currency (USD, EUR, GBP, etc.)
- Set currency symbol display preferences
- Configure regional formatting

**Date Format Settings:**
- US Format: MM/DD/YYYY
- EU Format: DD/MM/YYYY
- ISO Format: YYYY-MM-DD
- Long Format: Month DD, YYYY

**Timezone Management:**
- Set organization timezone
- Configure automatic DST handling
- Adjust user display preferences

**Theme Settings:**
- Choose default theme (Light/Dark)
- Allow user theme overrides
- Configure color schemes

### Application Settings
**System-Wide Configuration Parameters**

Manage core application settings:

**Business Rules:**
- Full Case Threshold: Set dollar amount for detailed business cases
- Approval Timeouts: Configure automatic escalation timing
- Workflow Parameters: Customize business process behavior

**Security Settings:**
- Session timeout configuration
- Password requirements
- Authentication settings

### Feature Toggles
**Enabling and Disabling Application Features**

Control which features are available:

1. Access Admin Center → Settings → Features
2. Toggle features on/off:
   - AI-powered requirements generation
   - Predictive analytics
   - Advanced reporting
   - Integration capabilities
3. Changes take effect immediately

## Workflow Management

### Workflow Configuration
**Customizing Business Process Parameters**

Configure key workflow settings:

**Full Case Threshold:**
- Set dollar amount requiring detailed business cases
- Default: $25,000
- Affects problem-to-case conversion

**Assignment Timeouts:**
- BA Assignment: Time before escalation (default 72 hours)
- Director Approval: Time for executive decisions (default 72 hours)
- Customize based on organizational needs

**Notification Settings:**
- Email notification preferences
- SMS alert configuration
- Escalation notification rules

### Automated Triage Rules
**Creating and Managing Business Rule Automation**

Set up automated decision-making:

**Creating triage rules:**
1. Go to Admin Center → Triage Rules
2. Click "Create New Rule"
3. Define conditions:
   - Problem criteria
   - Value thresholds
   - Department routing
4. Set actions:
   - Auto-assignment
   - Escalation triggers
   - Notification sends
5. Test and activate rule

**Managing existing rules:**
- Edit rule conditions
- Test rule effectiveness
- Monitor rule performance
- Activate/deactivate as needed

### Workflow Templates
**Managing Pre-configured Business Processes**

DeciFrame includes 8 essential workflow templates:

1. **Problem-to-Business Case**: Problem identification through business case creation
2. **Business Case Review**: Multi-stage approval process
3. **Epic & Story Management**: AI-powered epic creation and story breakdown
4. **Project Conversion**: Business case to project transformation
5. **Project Tracking**: Milestone monitoring with ML predictions
6. **Solution Recommendation**: AI-powered solution engine
7. **Department Escalation**: Hierarchical routing and approvals
8. **Notification Management**: Automated notification system

All templates are automatically configured for your organization.

## Data Management & Analytics

### Data Import System
**Bulk Data Import with Mapping Interface**

Import large datasets efficiently:

**Starting an import:**
1. Go to Admin Center → Data Import
2. Select data type (Users, Departments, Problems, etc.)
3. Download appropriate CSV template
4. Prepare your data file
5. Upload file for processing

**Mapping columns:**
1. Review detected columns
2. Map your data to DeciFrame fields
3. Set required field mappings
4. Configure optional field assignments
5. Validate mapping configuration

**Processing import:**
1. Review import preview
2. Confirm data accuracy
3. Execute import process
4. Monitor progress in real-time
5. Review import results and errors

### Data Export System
**Comprehensive Export Capabilities**

Export data for analysis and backup:

**Available export types:**
- Organizational structure
- User lists and profiles
- Problems and business cases
- Projects and milestones
- System reports and analytics

**Export formats:**
- CSV: For spreadsheet analysis
- PDF: For formal reports
- Excel: For advanced data manipulation

**Creating exports:**
1. Go to Admin Center → Data Export
2. Select data type and format
3. Configure date ranges and filters
4. Generate and download export

### Audit Trail
**Complete System Activity Logging**

Monitor all system activity:

**Viewing audit logs:**
1. Go to Admin Center → Audit Logs
2. Filter by:
   - Date range
   - User actions
   - System events
   - Error conditions
3. Export logs for compliance

**Audit information includes:**
- User actions and timestamps
- System changes and modifications
- Login/logout events
- Data access and modifications
- Error conditions and resolutions

## Help Center Management

### Category Management
**Creating and Organizing Help Categories**

Organize help content effectively:

**Creating categories:**
1. Go to Admin Center → Help Center
2. Click "New Category"
3. Enter category information:
   - Category name
   - Description
   - Sort order
4. Save category

**Managing categories:**
- Edit category details
- Reorder categories
- Delete empty categories
- Track article counts

### Article Management
**Creating and Managing Help Articles**

Build comprehensive documentation:

**Creating articles:**
1. Click "New Article" in Help Center
2. Select target category
3. Enter article details:
   - Title and description
   - Content (Markdown supported)
   - Role-based access controls
   - Sort order within category
4. Save and publish article

**Content features:**
- Markdown formatting support
- Code syntax highlighting
- Tables and lists
- Images and links
- Role-based visibility

**Managing articles:**
- Edit existing content
- Update role permissions
- Reorder within categories
- Track view statistics
- Archive outdated content

## Notification System

### Notification Templates
**Creating and Managing System Notifications**

Configure automated communications:

**Template types:**
- Email notifications
- In-app alerts
- SMS messages (if configured)
- System announcements

**Creating templates:**
1. Go to Admin Center → Notifications
2. Click "New Template"
3. Configure:
   - Template name and description
   - Message content with variables
   - Trigger conditions
   - Recipient rules
4. Test and activate template

### Email Integration
**Configuring Email Notification Settings**

Set up email communications:

**SMTP Configuration:**
- Email server settings
- Authentication credentials
- Security settings (TLS/SSL)
- Sender information

**Email Templates:**
- Customize email layouts
- Add company branding
- Configure signatures
- Set up automatic responses

### Notification Rules
**Setting Up Automated Notification Triggers**

Create intelligent notification automation:

**Rule configuration:**
1. Define trigger conditions
2. Set recipient criteria
3. Choose notification methods
4. Configure timing and frequency
5. Test rule effectiveness

**Common triggers:**
- Problem submissions
- Business case approvals
- Project milestone completions
- Escalation events
- System alerts

## Security & Compliance

### Role-Based Access Control
**Managing User Permissions by Role**

Implement granular security:

**Permission levels:**
- Read: View information
- Create: Add new items
- Update: Modify existing items
- Delete: Remove items
- Admin: Full administrative access

**Configuring permissions:**
1. Go to Admin Center → Roles
2. Select role to modify
3. Adjust permissions by module
4. Save configuration
5. Changes apply immediately

### Multi-Tenant Security
**Organization-Level Data Isolation**

Ensure complete data separation:

**Automatic isolation:**
- Users only see their organization's data
- Cross-organization access prevented
- Secure data boundaries maintained

**Security features:**
- Encrypted data transmission
- Secure session management
- Audit trail maintenance
- Compliance reporting

### Audit Logging
**Complete Activity Tracking and Compliance**

Maintain comprehensive audit trails:

**Logged activities:**
- User login/logout events
- Data access and modifications
- Administrative actions
- System configuration changes
- Error conditions and resolutions

**Compliance features:**
- Tamper-proof logging
- Long-term log retention
- Searchable audit history
- Export capabilities for audits

## Reports & Monitoring

### System Reports
**Generating Comprehensive System Reports**

Create detailed system analytics:

**Available reports:**
- User activity summaries
- System performance metrics
- Business process analytics
- Error and incident reports
- Compliance and audit reports

**Report features:**
- Customizable date ranges
- Multiple export formats
- Scheduled report generation
- Email delivery options
- Interactive charts and graphs

### Performance Metrics
**Monitoring System Performance and Usage**

Track system health and utilization:

**Key metrics:**
- Response time monitoring
- User engagement statistics
- System resource utilization
- Error rates and patterns
- Business process efficiency

**Monitoring tools:**
- Real-time dashboards
- Alert configuration
- Trend analysis
- Performance baselines
- Capacity planning

## System Maintenance

### Database Management
**System Backup and Maintenance Tools**

Ensure system reliability:

**Backup procedures:**
- Automated daily backups
- Manual backup creation
- Backup verification
- Restore procedures
- Disaster recovery planning

**Maintenance tasks:**
- Database optimization
- Index maintenance
- Performance tuning
- Storage management
- System updates

### Error Monitoring
**Tracking and Resolving System Errors**

Proactive error management:

**Error tracking:**
- Automatic error detection
- Error categorization
- Impact assessment
- Resolution tracking
- Prevention measures

**Resolution workflow:**
1. Error detection and alerting
2. Impact assessment
3. Root cause analysis
4. Resolution implementation
5. Prevention measures

This comprehensive help system covers all administrative functions in DeciFrame, providing step-by-step guidance for effective system management.