# DeciFrame - Comprehensive Problem & Business Case Management System

## Overview
DeciFrame is a modular Flask application designed for comprehensive problem and business case management. It features advanced authentication, organizational tracking, project management, and workflow automation. The system provides a clear distinction between technology projects requiring detailed specifications and process projects needing workflow definitions, aligning with real-world project management practices. The ambition is to provide a professional brand foundation for the enterprise market, ensuring market differentiation and consistent user experience across all modules.

## User Preferences
- **Interface Style**: Bootstrap dark theme preferred
- **Code Standards**: Clean, modular Flask applications
- **Testing Approach**: Comprehensive test coverage with real data validation
- **Documentation**: Detailed inline comments and architectural documentation

## System Architecture
DeciFrame employs a modular Flask backend with SQLAlchemy ORM and a PostgreSQL database. Authentication is handled via a JWT stateless system, transitioning towards session-based Flask-Login for enhanced security. The frontend utilizes Bootstrap's dark theme for responsive design. Security is enforced with WTForms validation and Flask-CSRF protection.

**Core Modules:**
-   **Auth**: User authentication and profile management, including multi-tenant organization registration with business email domain validation.
-   **Department**: Hierarchical management up to 5 levels with a unified Department model (eliminating the dual hierarchy system). Directors have department-scoped admin access.
-   **Problems**: Problem reporting and tracking with auto-generated codes (P0001, etc.) and AI-powered issue classification (SYSTEM, PROCESS, OTHER).
-   **Business**: Progressive business case elaboration (Light/Full depths) with auto-generated codes (C0001, etc.), ROI calculations, and a comprehensive approval workflow that can convert business cases into projects.
-   **Projects**: Project management with milestone tracking, auto-generated codes (PRJ0001, etc.), and a backlog view for epics and stories.
-   **Notifications**: Workflow automation and notification system with in-app notifications and SendGrid email integration, offering configurable templates and frequency.
-   **Admin**: Comprehensive dashboard with user management, role permissions, system settings, audit logs, and data management (import/export).
-   **Help**: Contextual help system with a floating widget, public help center, and AI-powered chat assistant.

**Key Technical Implementations & Design Decisions:**
-   **Database Models**: User (role-based), Department (hierarchical), Problem, BusinessCase, Project, ProjectMilestone, NotificationTemplate, Notification, Epic, Story, Solution, AuditLog, ImportJob, OrgUnit, EpicSyncLog, ReportTemplate, ReportRun, PredictionFeedback, AIThresholdSettings. All core business models include `organization_id` for multi-tenant data isolation.
-   **UI/UX**: Standardized button styling, form fields, container dimensions (3px dark blue borders), and consistent dropdown menus. Sticky footer and full-width admin layouts. Professional branding with SVG assets and a welcome onboarding system for new users.
-   **AI Integration**: OpenAI GPT-4o for AI-powered problem classification, solution recommendations, requirements generation (epics and user stories), and review insights with confidence scoring.
-   **Workflow Automation**: Event-driven workflow processor with 26+ pre-defined templates, conditional logic, and action handlers. Asynchronous event queue for background processing.
-   **Reporting & Analytics**: Executive dashboard with 7+ advanced charts (e.g., Department Heat-Map, Time-to-Value), multi-dimensional filtering, drill-down capabilities, and automated PDF export via SendGrid. ML-powered predictive analytics for project success, cycle time, and anomaly detection with automated retraining.
-   **Search**: PostgreSQL full-text search (`tsvector`) with GIN indexes for fast, relevant results across problems, business cases, and projects.
-   **Globalization**: Complete organization-level preference system for currency, date format, and timezone, dynamically applied across the application.
-   **Security**: Strict multi-tenant data isolation, role-based access control (RBAC), CSRF protection, password hashing, and comprehensive audit logging. Session-based authentication is preferred over JWT.

## External Dependencies
-   **Flask**: Web framework
-   **SQLAlchemy**: ORM for database interaction
-   **PostgreSQL**: Primary database
-   **SendGrid**: Email notifications
-   **Authlib**: OAuth/OIDC authentication
-   **OpenAI**: AI-powered features (GPT-4o)
-   **Bootstrap**: Frontend framework (Bootstrap 5)
-   **Chart.js**: Data visualization
-   **WeasyPrint**: PDF generation
-   **psutil**: System monitoring
-   **APScheduler**: Task scheduling (e.g., for ML retraining, automated reports)
-   **scikit-learn**: Machine learning models (RandomForestClassifier, LinearRegression, IsolationForest)
-   **joblib**: ML model persistence
-   **pandas**: CSV/Excel file processing (for bulk import/export)
-   **openpyxl**: Excel file format support
-   **pytz**: Timezone handling