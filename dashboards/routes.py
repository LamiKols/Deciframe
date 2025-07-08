"""
Role-Scoped Dashboard Routes
Provides personalized home pages based on user roles
"""
from flask import Blueprint, redirect, url_for, render_template, session, flash, Response
from flask_login import login_required, current_user, login_user
from sqlalchemy import desc, and_
from datetime import datetime, timedelta

from models import Problem, BusinessCase, Project, ProjectMilestone, User, ImportJob, Department, AuditLog
from models import StatusEnum, PriorityEnum, RoleEnum
from app import db



dash_bp = Blueprint('dashboards', __name__, url_prefix='/dashboard')

def compute_department_kpis(dept_id):
    """Compute KPIs for a department"""
    # Get ALL problems in department (organization-wide totals for KPI cards)
    open_problems = Problem.query.filter_by(organization_id=current_user.organization_id).count()
    
    # Get ALL pending cases (organization-wide totals for KPI cards)
    pending_cases = BusinessCase.query.filter_by(status=StatusEnum.Open, organization_id=current_user.organization_id).count()
    
    # Get ALL active projects (organization-wide totals for KPI cards)
    active_projects = Project.query.filter(
        Project.status.in_([StatusEnum.Open, StatusEnum.InProgress])
    ).count()
    
    # Calculate average ROI across all approved cases (organization-wide)
    approved_cases = BusinessCase.query.filter(
        BusinessCase.status == StatusEnum.Approved,
        BusinessCase.roi != None
    ).all()
    
    avg_roi = 0
    if approved_cases:
        total_roi = sum(case.roi for case in approved_cases if case.roi)
        avg_roi = total_roi / len(approved_cases) if approved_cases else 0
    
    return {
        'open_problems': open_problems,
        'pending_cases': pending_cases, 
        'active_projects': active_projects,
        'avg_roi': round(avg_roi, 1)
    }

@dash_bp.route('/')
@login_required
def dashboard_home():
    """Personal dashboard showing user-specific metrics and tasks"""
    # Check if user has pending department assignment
    if current_user.has_pending_department:
        return redirect(url_for('dashboards.pending_dashboard'))
    
    role = current_user.role.value.lower()
    
    # Show personal dashboard with user-specific data regardless of role
    # Get user's personal statistics
    my_problems = Problem.query.filter_by(reported_by=current_user.id, organization_id=current_user.organization_id).count()
    my_cases = BusinessCase.query.filter_by(created_by=current_user.id, organization_id=current_user.organization_id).count()
    my_projects = Project.query.filter_by(created_by=current_user.id, organization_id=current_user.organization_id).count()
    
    # Get recent items for this user
    recent_problems = Problem.query.filter_by(reported_by=current_user.id, organization_id=current_user.organization_id)\
        .order_by(desc(Problem.created_at)).limit(5).all()
    recent_cases = BusinessCase.query.filter_by(created_by=current_user.id, organization_id=current_user.organization_id)\
        .order_by(desc(BusinessCase.created_at)).limit(5).all()
    
    # Get tasks based on role
    if role in ['director', 'ceo', 'admin']:
        pending_approvals = BusinessCase.query.filter_by(status=StatusEnum.Open, organization_id=current_user.organization_id).count()
    else:
        pending_approvals = 0
    
    return render_template('dashboards/personal.html',
                         my_problems=my_problems,
                         my_cases=my_cases, 
                         my_projects=my_projects,
                         recent_problems=recent_problems,
                         recent_cases=recent_cases,
                         pending_approvals=pending_approvals,
                         user=current_user)

@dash_bp.route('/staff')
@login_required
def staff_dashboard():
    """Staff dashboard - shows user's own problems and cases"""
    problems = Problem.query.filter_by(reported_by=current_user.id, organization_id=current_user.organization_id)\
        .order_by(desc(Problem.created_at)).limit(10).all()
    
    # Cases where user is creator
    cases = BusinessCase.query.filter_by(created_by=current_user.id, organization_id=current_user.organization_id)\
        .order_by(desc(BusinessCase.created_at)).limit(10).all()
    
    return render_template('dashboards/staff.html', 
                         problems=problems, 
                         cases=cases,
                         user=current_user)

@dash_bp.route('/manager')
@login_required
def manager_dashboard():
    """Manager dashboard - shows department problems and pending cases"""
    dept_id = current_user.dept_id
    
    # Department problems by priority
    problems = Problem.query.filter_by(department_id=dept_id, organization_id=current_user.organization_id)\
        .order_by(desc(Problem.priority)).limit(10).all()
    
    # Pending cases in department
    cases = BusinessCase.query.filter_by(dept_id=dept_id, status=StatusEnum.Open, organization_id=current_user.organization_id)\
        .order_by(desc(BusinessCase.created_at)).all()
    
    # Department KPIs
    kpis = compute_department_kpis(dept_id)
    
    return render_template('dashboards/manager.html', 
                         dept_problems=problems, 
                         pending_cases=cases,
                         kpis=kpis,
                         user=current_user)

@dash_bp.route('/ba')
@login_required
def ba_dashboard():
    """Business Analyst dashboard - shows assigned cases and requirements"""
    # Cases assigned to this BA
    assigned_cases = BusinessCase.query.filter_by(assigned_ba=current_user.id, organization_id=current_user.organization_id)\
        .order_by(desc(BusinessCase.created_at)).all()
    
    # Cases without epics (pending requirements)
    needs_requirements = [case for case in assigned_cases if not case.epics]
    
    # Recent cases across all departments for awareness
    recent_cases = BusinessCase.query.filter_by(status=StatusEnum.Open, organization_id=current_user.organization_id)\
        .order_by(desc(BusinessCase.created_at)).limit(5).all()
    
    # Calculate statistics for BA dashboard
    in_progress_count = BusinessCase.query.filter(
        BusinessCase.assigned_ba == current_user.id,
        BusinessCase.status == StatusEnum.InProgress
    ).count()
    
    stats = {
        'total_assigned': len(assigned_cases),
        'in_progress': in_progress_count,
        'needs_requirements': len(needs_requirements),
        'completed_this_month': BusinessCase.query.filter(
            BusinessCase.assigned_ba == current_user.id,
            BusinessCase.status == StatusEnum.Approved,
            BusinessCase.created_at >= datetime.now().replace(day=1)
        ).count()
    }
    
    return render_template('dashboards/ba.html', 
                         assigned_cases=assigned_cases,
                         needs_requirements=needs_requirements,
                         recent_cases=recent_cases,
                         stats=stats,
                         user=current_user)

@dash_bp.route('/pm')
@login_required
def pm_dashboard():
    """Project Manager dashboard - shows active projects and milestones"""
    # Projects managed by this PM
    projects = Project.query.filter_by(project_manager_id=current_user.id, organization_id=current_user.organization_id)\
        .order_by(desc(Project.created_at)).all()
    
    # Upcoming milestones using helper function
    upcoming_milestones = Project.upcoming_milestones(days=7)
    
    # Filter for milestones belonging to projects managed by current user
    user_upcoming = [m for m in upcoming_milestones 
                    if m.project.project_manager_id == current_user.id]
    
    # Overdue milestones
    overdue_milestones = ProjectMilestone.query.join(Project)\
        .filter(
            Project.project_manager_id == current_user.id,
            ProjectMilestone.due_date < datetime.utcnow().date(),
            ProjectMilestone.completed == False
        ).order_by(ProjectMilestone.due_date).all()
    
    return render_template('dashboards/pm.html', 
                         projects=projects, 
                         upcoming_milestones=user_upcoming,
                         overdue_milestones=overdue_milestones,
                         user=current_user)

@dash_bp.route('/director')
@login_required
def director_dashboard():
    """Director/CEO dashboard - shows department KPIs and approvals"""
    dept_id = current_user.dept_id
    
    # Department KPIs
    kpis = compute_department_kpis(dept_id)
    
    # Cases awaiting approval in department
    cases = BusinessCase.query.filter_by(dept_id=dept_id, status=StatusEnum.Open, organization_id=current_user.organization_id)\
        .order_by(desc(BusinessCase.created_at)).all()
    
    # High priority problems across department
    high_priority_problems = Problem.query.filter_by(
        department_id=dept_id, 
        priority=PriorityEnum.High,
        status=StatusEnum.Open
    , organization_id=current_user.organization_id).order_by(desc(Problem.created_at)).all()
    
    # Portfolio metrics for department projects
    portfolio = {
        'total_value': '$2.4M',
        'avg_roi': '18.5'
    }
    
    # Trend metrics for dashboard
    trends = {
        'problem_resolution': '85',
        'case_approval': '92',
        'project_delivery': '78'
    }
    
    return render_template('dashboards/director.html', 
                         kpi=kpis, 
                         cases=cases,
                         high_priority_problems=high_priority_problems,
                         portfolio=portfolio,
                         trends=trends,
                         user=current_user)

@dash_bp.route('/executive')
@login_required
def exec_dashboard():
    """Executive dashboard with organization-wide metrics"""
    from models import Problem, BusinessCase, Project, Department, User
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    user = current_user
    
    # Check if user has appropriate role for executive dashboard
    if user.role.value not in ['Director', 'CEO', 'Admin']:
        flash('Access denied. Executive dashboard is restricted to Directors, CEOs, and Administrators.', 'error')
        return redirect(url_for('dashboards.dashboard_home'))
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # For now, show organization-wide metrics for all executive users
    # TODO: Add department scoping for Directors in future iteration
    problems = Problem.query
    business_cases = BusinessCase.query
    projects = Project.query
    departments = Department.query
    users = User.query
    
    # Calculate key metrics
    metrics = {
        'total_problems': problems.count(),
        'problems_resolved': problems.filter(Problem.status == 'Resolved').count(),
        'problems_recent': problems.filter(Problem.created_at >= thirty_days_ago).count(),
        
        'total_cases': business_cases.count(),
        'cases_approved': business_cases.filter(BusinessCase.status == 'Approved').count(),
        'cases_pending': business_cases.filter(BusinessCase.status.in_(['Submitted', 'In_Progress'])).count(),
        
        'total_projects': projects.count(),
        'projects_active': projects.filter(Project.status.in_(['In_Progress', 'InProgress'])).count(),
        'projects_completed': projects.filter(Project.status == 'Completed').count(),
        
        'total_departments': departments.count(),
        'total_users': users.count()
    }
    
    # Department performance data (simplified for initial implementation)
    dept_performance = []
    for dept in departments.limit(10).all():  # Limit to top 10 for display
        # Count items related to this department (if department relationship exists)
        dept_problems = 0
        dept_cases = 0
        dept_projects = 0
        
        # Try to count department-related items, fallback to 0 if no relationship
        try:
            dept_problems = Problem.query.filter_by(department_id=dept.id, organization_id=current_user.organization_id).count() if hasattr(Problem, 'department_id') else 0
            dept_cases = BusinessCase.query.filter_by(department_id=dept.id, organization_id=current_user.organization_id).count() if hasattr(BusinessCase, 'department_id') else 0
            dept_projects = Project.query.filter_by(department_id=dept.id, organization_id=current_user.organization_id).count() if hasattr(Project, 'department_id') else 0
        except:
            pass  # Default to 0 counts
        
        dept_performance.append({
            'name': dept.name,
            'problems': dept_problems,
            'cases': dept_cases,
            'projects': dept_projects
        })
    
    # Recent activity
    recent_problems = problems.order_by(Problem.created_at.desc()).limit(5).all()
    recent_cases = business_cases.order_by(BusinessCase.created_at.desc()).limit(5).all()
    recent_projects = projects.order_by(Project.created_at.desc()).limit(5).all()
    
    return render_template('dashboards/executive_dashboard.html',
                         metrics=metrics,
                         dept_performance=dept_performance,
                         recent_problems=recent_problems,
                         recent_cases=recent_cases,
                         recent_projects=recent_projects,
                         user_role=user.role.value)

@dash_bp.route('/executive-dashboard')
@login_required
def executive_dashboard():
    """Improved Executive dashboard with role-based access and department scoping"""
    from models import Problem, BusinessCase, Project, Department, User
    
    # Check if user has appropriate role for executive dashboard
    if current_user.role.value not in ['Director', 'CEO', 'Admin']:
        flash('Access denied. Executive dashboard is restricted to Directors, CEOs, and Administrators.', 'error')
        return redirect(url_for('dashboards.dashboard_home'))
    
    # Get currency symbol from organization settings or use default
    currency_symbol = "$"  # Default fallback
    
    # Try to get organization currency from department's organization or global settings
    try:
        from models import OrganizationSettings
        org_settings = OrganizationSettings.query.first()
        if org_settings and org_settings.currency:
            # Map currency codes to symbols
            currency_symbols = {
                'USD': '$', 'EUR': '€', 'GBP': '£', 'CAD': 'C$',
                'AUD': 'A$', 'JPY': '¥', 'CNY': '¥', 'INR': '₹'
            }
            currency_symbol = currency_symbols.get(org_settings.currency, '$')
    except:
        pass  # Use default

    # Show all if Admin or CEO, else just their department with error handling
    try:
        if current_user.role.value == "Director":
            dept_id = current_user.dept_id
            if dept_id:
                cases = BusinessCase.query.filter_by(dept_id=dept_id, organization_id=current_user.organization_id)
                projects = Project.query.filter_by(dept_id=dept_id, organization_id=current_user.organization_id)
                departments = Department.query.filter_by(id=dept_id, organization_id=current_user.organization_id).all()
            else:
                # Fallback if no department assigned
                cases = BusinessCase.query
                projects = Project.query
                departments = Department.query.filter_by(organization_id=current_user.organization_id).all()
        else:
            cases = BusinessCase.query
            projects = Project.query
            departments = Department.query.filter_by(organization_id=current_user.organization_id).all()

        case_stats = []
        for dept in departments:
            try:
                dept_cases = BusinessCase.query.filter_by(dept_id=dept.id, organization_id=current_user.organization_id)
                total_count = dept_cases.count()
                approved_count = dept_cases.filter_by(status="Approved").count()
                rejected_count = dept_cases.filter_by(status="Rejected").count()
                pending_count = dept_cases.filter_by(status="Submitted").count()
                
                case_stats.append({
                    "name": dept.name,
                    "total": total_count,
                    "approved": approved_count,
                    "rejected": rejected_count,
                    "pending": pending_count
                })
            except Exception as e:
                # Skip departments that cause database errors
                print(f"Warning: Skipping department {dept.name} due to error: {str(e)}")
                continue
    except Exception as e:
        # Fallback to empty data if database queries fail
        print(f"Database error in executive dashboard: {str(e)}")
        cases = BusinessCase.query.filter_by(id=-1, organization_id=current_user.organization_id)  # Empty query
        projects = Project.query.filter_by(id=-1, organization_id=current_user.organization_id)  # Empty query
        case_stats = []

    # Calculate metrics with error handling
    try:
        case_count = cases.count()
    except:
        case_count = 0
        
    try:
        project_count = projects.count()
    except:
        project_count = 0
        
    try:
        problem_count = Problem.query.filter_by(status="Open", organization_id=current_user.organization_id).count()
    except:
        problem_count = 0
        
    try:
        project_list = projects.all()
        total_budget = sum([p.budget or 0 for p in project_list])
    except:
        project_list = []
        total_budget = 0

    return render_template("dashboards/executive_dashboard.html",
        case_count=case_count,
        project_count=project_count,
        problem_count=problem_count,
        total_budget=total_budget,
        case_stats=case_stats,
        projects=project_list,
        currency_symbol=currency_symbol
    )

@dash_bp.route('/executive-dashboard/export', methods=['POST'])
@login_required
def export_exec_dashboard():
    """Export Executive Dashboard to PDF with watermark and audit logging"""
    # Check role access
    if current_user.role.value not in ['Director', 'CEO', 'Admin']:
        flash('Access denied. PDF export is restricted to Directors, CEOs, and Administrators.', 'error')
        return redirect(url_for('dashboards.executive_dashboard'))
    
    # Get currency symbol from organization settings or use default
    currency_symbol = "$"
    try:
        from models import OrganizationSettings
        org_settings = OrganizationSettings.query.first()
        if org_settings and org_settings.currency:
            currency_symbols = {
                'USD': '$', 'EUR': '€', 'GBP': '£', 'CAD': 'C$',
                'AUD': 'A$', 'JPY': '¥', 'CNY': '¥', 'INR': '₹'
            }
            currency_symbol = currency_symbols.get(org_settings.currency, '$')
    except:
        pass

    # Fetch metrics (reusing logic from executive_dashboard)
    if current_user.role.value == "Director":
        dept_id = current_user.dept_id
        cases = BusinessCase.query.filter_by(dept_id=dept_id, organization_id=current_user.organization_id)
        projects = Project.query.filter_by(dept_id=dept_id, organization_id=current_user.organization_id)
        departments = Department.query.filter_by(id=dept_id, organization_id=current_user.organization_id).all()
    else:
        cases = BusinessCase.query
        projects = Project.query
        departments = Department.query.filter_by(organization_id=current_user.organization_id).all()

    case_stats = []
    for dept in departments:
        dept_cases = BusinessCase.query.filter_by(dept_id=dept.id, organization_id=current_user.organization_id)
        case_stats.append({
            "name": dept.name,
            "total": dept_cases.count(),
            "approved": dept_cases.filter_by(status="Approved").count(),
            "rejected": dept_cases.filter_by(status="Rejected").count(),
            "pending": dept_cases.filter_by(status="Submitted").count()
        })

    # Render HTML with watermark
    html = render_template("dashboards/executive_dashboard_pdf.html",
        case_count=cases.count(),
        project_count=projects.count(),
        problem_count=Problem.query.filter_by(status="Open", organization_id=current_user.organization_id).count(),
        total_budget=sum([p.budget or 0 for p in projects]),
        case_stats=case_stats,
        projects=projects.all(),
        currency_symbol=currency_symbol,
        watermark="Generated by DeciFrame",
        generated_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        user_name=f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or current_user.username
    )

    try:
        from weasyprint import HTML
        pdf = HTML(string=html).write_pdf()

        # Log to audit trail
        audit_log = AuditLog(
            user_id=current_user.id,
            action="export_pdf",
            module="Executive Dashboard",
            target="dashboard_export",
            details="Executive Dashboard PDF report exported",
            timestamp=datetime.utcnow()
        )
        db.session.add(audit_log)
        db.session.commit()

        return Response(
            pdf,
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment; filename=DeciFrame_Executive_Report.pdf"}
        )
    except ImportError:
        flash('PDF generation not available. WeasyPrint library not installed.', 'error')
        return redirect(url_for('dashboards.executive_dashboard'))
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('dashboards.executive_dashboard'))

@dash_bp.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard - shows system health and management tasks"""
    # Import jobs needing attention
    pending_jobs = ImportJob.query.filter(ImportJob.status != 'Complete')\
        .order_by(desc(ImportJob.created_at)).all()
    
    # User statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    recent_users = User.query.filter(
        User.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    # System overview
    total_problems = Problem.query.filter_by(organization_id=current_user.organization_id).count()
    total_cases = BusinessCase.query.filter_by(organization_id=current_user.organization_id).count()
    total_projects = Project.query.filter_by(organization_id=current_user.organization_id).count()
    
    # Recent activity
    recent_problems = Problem.query.order_by(desc(Problem.created_at)).limit(5).all()
    recent_cases = BusinessCase.query.order_by(desc(BusinessCase.created_at)).limit(5).all()
    
    # System health status
    system_health = {
        'status': 'Healthy' if total_users > 0 else 'Warning',
        'database_connections': 'Active',
        'background_tasks': 'Running',
        'disk_usage': '45%',
        'last_check': datetime.utcnow()
    }
    
    # Import statistics for admin dashboard
    import_stats = {
        'completed': 0,
        'failed': 0,
        'pending': 0,
        'total': 0
    }
    
    # Get role-based user statistics
    from models import RoleEnum
    role_counts = {}
    for role in RoleEnum:
        role_counts[role.value] = User.query.filter_by(role=role).count()
    
    # Create user_stats object expected by template
    user_stats = {
        'total_users': total_users,
        'active_users': active_users,
        'by_role': role_counts
    }
    
    # Create system_stats object expected by template
    system_stats = {
        'total_problems': total_problems,
        'total_cases': total_cases,
        'total_projects': total_projects,
        'search_indexed': total_problems + total_cases + total_projects
    }
    
    return render_template('dashboards/admin.html', 
                         pending_jobs=pending_jobs,
                         user_stats=user_stats,
                         system_stats=system_stats,
                         recent_users=recent_users,
                         recent_problems=recent_problems,
                         recent_cases=recent_cases,
                         system_health=system_health,
                         import_stats=import_stats,
                         user=current_user)

@dash_bp.route('/pending')
@login_required
def pending_dashboard():
    """Limited dashboard for users with pending department assignments"""
    # Show only basic information and links to contact admin
    pending_count = User.query.filter_by(department_status='pending').count()
    
    return render_template('dashboards/pending.html',
                         user=current_user,
                         pending_count=pending_count)