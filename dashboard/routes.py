"""
Executive Dashboard routes for DeciFrame
Provides analytics, metrics, and reporting for leadership
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, abort, send_file
from flask_login import login_required, current_user
from sqlalchemy import func, extract, and_
import io
import csv
from functools import wraps

from app import db
from models import (
    User, Department, Problem, BusinessCase, Project, ProjectMilestone,
    StatusEnum, RoleEnum, PriorityEnum, CaseTypeEnum
)


dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin/director/CEO roles"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 403
        if current_user.role not in [RoleEnum.Admin, RoleEnum.Director, RoleEnum.CEO]:
            return jsonify({"error": "Insufficient permissions"}), 403
        return f(*args, **kwargs)
    return decorated_function


@dashboard_bp.route('/dashboard-demo')
def dashboard_demo():
    """Demo version of executive dashboard - no auth required"""
    # Same logic as admin dashboard but without authentication
    problems_count = Problem.query.count()
    open_cases = BusinessCase.query.filter_by(status=StatusEnum.Open).count()
    active_projects = Project.query.filter(
        Project.status.in_([StatusEnum.Open, StatusEnum.InProgress])
    ).count()
    
    # Average case approval time
    resolved_cases = BusinessCase.query.filter_by(status=StatusEnum.Resolved).all()
    if resolved_cases:
        approval_times = []
        for case in resolved_cases:
            if case.updated_at and case.created_at:
                days = (case.updated_at - case.created_at).days
                approval_times.append(days)
        avg_case_approval_time = sum(approval_times) / len(approval_times) if approval_times else 0
    else:
        avg_case_approval_time = 0
    
    # Average ROI
    cases_with_roi = BusinessCase.query.filter(BusinessCase.roi != None).all()
    avg_roi = sum(case.roi for case in cases_with_roi) / len(cases_with_roi) if cases_with_roi else 0
    
    # Total investment and benefits
    total_investment = sum(case.cost_estimate for case in BusinessCase.query.all())
    total_benefits = sum(case.benefit_estimate for case in BusinessCase.query.all())
    
    # Project completion rate
    total_projects = Project.query.count()
    completed_projects = Project.query.filter_by(status=StatusEnum.Resolved).count()
    completion_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0
    
    metrics = {
        'problems_count': problems_count,
        'open_cases': open_cases,
        'active_projects': active_projects,
        'avg_case_approval_time': round(avg_case_approval_time, 1),
        'avg_roi': round(avg_roi, 1),
        'total_investment': total_investment,
        'total_benefits': total_benefits,
        'completion_rate': round(completion_rate, 1),
        'dept_problems': {}
    }
    
    return render_template('admin_dashboard_demo.html', metrics=metrics, datetime=datetime)


@dashboard_bp.route('/dashboard')
@admin_required  
def admin_dashboard():
    """Main executive dashboard with KPI cards and metrics"""
    
    # Core metrics
    problems_count = Problem.query.count()
    open_cases = BusinessCase.query.filter_by(status=StatusEnum.Open).count()
    active_projects = Project.query.filter(
        Project.status.in_([StatusEnum.Open, StatusEnum.InProgress])
    ).count()
    
    # Average case approval time (days from creation to resolution)
    resolved_cases = BusinessCase.query.filter_by(status=StatusEnum.Resolved).all()
    if resolved_cases:
        approval_times = []
        for case in resolved_cases:
            if case.updated_at and case.created_at:
                days = (case.updated_at - case.created_at).days
                approval_times.append(days)
        avg_case_approval_time = sum(approval_times) / len(approval_times) if approval_times else 0
    else:
        avg_case_approval_time = 0
    
    # Average ROI
    cases_with_roi = BusinessCase.query.filter(BusinessCase.roi.isnot(None)).all()
    avg_roi = sum(case.roi for case in cases_with_roi) / len(cases_with_roi) if cases_with_roi else 0
    
    # Total investment and benefits
    total_investment = sum(case.cost_estimate for case in BusinessCase.query.all())
    total_benefits = sum(case.benefit_estimate for case in BusinessCase.query.all())
    
    # Project completion rate
    total_projects = Project.query.count()
    completed_projects = Project.query.filter_by(status=StatusEnum.Resolved).count()
    completion_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0
    
    # Department breakdown
    dept_problems = db.session.query(
        func.coalesce(Problem.department_id, 0).label('dept_id'),
        func.count(Problem.id).label('count')
    ).group_by(Problem.department_id).all()
    
    metrics = {
        'problems_count': problems_count,
        'open_cases': open_cases,
        'active_projects': active_projects,
        'avg_case_approval_time': round(avg_case_approval_time, 1),
        'avg_roi': round(avg_roi, 1),
        'total_investment': total_investment,
        'total_benefits': total_benefits,
        'completion_rate': round(completion_rate, 1),
        'dept_problems': dict(dept_problems)
    }
    
    return render_template('admin_dashboard.html', metrics=metrics, datetime=datetime)


@dashboard_bp.route('/api/dashboard/problems-trend')
@admin_required
def problems_trend():
    """API endpoint for problem creation trends over last 90 days"""
    return _get_problems_trend()

@dashboard_bp.route('/api/dashboard/problems-trend-demo')
def problems_trend_demo():
    """Demo API endpoint for problem creation trends - no auth required"""
    return _get_problems_trend()

@dashboard_bp.route('/api/dashboard/case-conversion-demo')
def case_conversion_demo():
    """Demo API endpoint for case conversion - no auth required"""
    return _get_case_conversion()

@dashboard_bp.route('/api/dashboard/project-metrics-demo')
def project_metrics_demo():
    """Demo API endpoint for project metrics - no auth required"""
    return _get_project_metrics()

@dashboard_bp.route('/api/dashboard/status-breakdown-demo')
def status_breakdown_demo():
    """Demo API endpoint for status breakdown - no auth required"""
    return _get_status_breakdown()

@dashboard_bp.route('/api/dashboard/department-heatmap-demo')
def department_heatmap_demo():
    """Demo API endpoint for department heatmap - no auth required"""
    return _get_department_heatmap()

@dashboard_bp.route('/api/dashboard/time-to-value-demo')
def time_to_value_demo():
    """Demo API endpoint for time to value - no auth required"""
    return _get_time_to_value()

@dashboard_bp.route('/api/dashboard/risks-issues-demo')
def risks_issues_demo():
    """Demo API endpoint for risks and issues - no auth required"""
    return _get_risks_issues()

@dashboard_bp.route('/api/dashboard/milestone-burndown-demo')
def milestone_burndown_demo():
    """Demo API endpoint for milestone burndown - no auth required"""
    return _get_milestone_burndown()

@dashboard_bp.route('/api/dashboard/roi-waterfall-demo')
def roi_waterfall_demo():
    """Demo API endpoint for ROI waterfall - no auth required"""
    return _get_roi_waterfall()

@dashboard_bp.route('/api/dashboard/problem-clusters-demo')
def problem_clusters_demo():
    """Demo API endpoint for problem clusters - no auth required"""
    return _get_problem_clusters()

@dashboard_bp.route('/api/dashboard/resource-utilization-demo')
def resource_utilization_demo():
    """Demo API endpoint for resource utilization - no auth required"""
    return _get_resource_utilization()

def _get_problems_trend():
    """API endpoint for problem creation trends over last 90 days"""
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)
    
    # Base aggregation query with filters
    trends = db.session.query(
        func.date_trunc('week', Problem.created_at).label('week'),
        func.count(Problem.id).label('count')
    ).filter(
        Problem.created_at >= start_date
    )
    
    # Apply filters directly to aggregation query
    if 'departments' in request.args and request.args.get('departments'):
        dept_ids = [int(d) for d in request.args.get('departments').split(',') if d.strip().isdigit()]
        if dept_ids:
            trends = trends.filter(Problem.department_id.in_(dept_ids))
    
    if 'priority' in request.args and request.args.get('priority'):
        priorities = [p.strip() for p in request.args.get('priority').split(',') if p.strip()]
        valid_priorities = [p for p in priorities if hasattr(PriorityEnum, p)]
        if valid_priorities:
            priority_enums = [getattr(PriorityEnum, p) for p in valid_priorities]
            trends = trends.filter(Problem.priority.in_(priority_enums))
    
    if 'status' in request.args and request.args.get('status'):
        statuses = [s.strip() for s in request.args.get('status').split(',') if s.strip()]
        valid_statuses = [s for s in statuses if hasattr(StatusEnum, s)]
        if valid_statuses:
            status_enums = [getattr(StatusEnum, s) for s in valid_statuses]
            trends = trends.filter(Problem.status.in_(status_enums))
    
    trends = trends.group_by(func.date_trunc('week', Problem.created_at)).order_by('week').all()
    
    # Format for Chart.js (expected format: {labels: [], data: []})
    labels = []
    data = []
    for trend in trends:
        if trend.week:
            labels.append(trend.week.strftime('%Y-%m-%d'))
            data.append(trend.count)
    
    return jsonify({
        'labels': labels,
        'data': data
    })


@dashboard_bp.route('/api/dashboard/case-conversion')
@admin_required
def case_conversion():
    """API endpoint for Problem→BusinessCase conversion ratios by month"""
    return _get_case_conversion()

def _get_case_conversion():
    """API endpoint for Problem→BusinessCase conversion ratios by month"""
    
    # Get monthly data for the last 12 months
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)
    
    # Problems created by month
    problems_by_month = db.session.query(
        extract('year', Problem.created_at).label('year'),
        extract('month', Problem.created_at).label('month'),
        func.count(Problem.id).label('problem_count')
    ).filter(
        Problem.created_at >= start_date
    ).group_by(
        extract('year', Problem.created_at),
        extract('month', Problem.created_at)
    ).all()
    
    # Business cases created by month (reactive cases only)
    cases_by_month = db.session.query(
        extract('year', BusinessCase.created_at).label('year'),
        extract('month', BusinessCase.created_at).label('month'),
        func.count(BusinessCase.id).label('case_count')
    ).filter(
        and_(
            BusinessCase.created_at >= start_date,
            BusinessCase.problem_id.isnot(None)  # Only reactive cases
        )
    ).group_by(
        extract('year', BusinessCase.created_at),
        extract('month', BusinessCase.created_at)
    ).all()
    
    # Combine data
    conversion_data = {}
    
    for row in problems_by_month:
        key = f"{int(row.year)}-{int(row.month):02d}"
        conversion_data[key] = {'problems': row.problem_count, 'cases': 0}
    
    for row in cases_by_month:
        key = f"{int(row.year)}-{int(row.month):02d}"
        if key in conversion_data:
            conversion_data[key]['cases'] = row.case_count
        else:
            conversion_data[key] = {'problems': 0, 'cases': row.case_count}
    
    # Format for Chart.js (expected format: {labels: [], problems: [], cases: []})
    labels = []
    problems = []
    cases = []
    
    for month, data in sorted(conversion_data.items()):
        labels.append(month)
        problems.append(data['problems'])
        cases.append(data['cases'])
    
    return jsonify({
        'labels': labels,
        'problems': problems,
        'cases': cases
    })


@dashboard_bp.route('/api/dashboard/project-metrics')
@admin_required
def project_metrics():
    """API endpoint for project on-time vs delayed percentages"""
    return _get_project_metrics()

def _get_project_metrics():
    """API endpoint for project on-time vs delayed percentages"""
    
    # Get all projects with end dates
    projects = Project.query.filter(Project.end_date != None).all()
    
    if not projects:
        return jsonify({
            'on_time': 0,
            'delayed': 0,
            'in_progress': 0,
            'total': 0
        })
    
    today = datetime.now().date()
    on_time = 0
    delayed = 0
    in_progress = 0
    
    for project in projects:
        if project.status == StatusEnum.Resolved:
            # Check if completed before end date
            if project.updated_at and project.updated_at.date() <= project.end_date:
                on_time += 1
            else:
                delayed += 1
        elif project.status in [StatusEnum.Open, StatusEnum.InProgress]:
            if project.end_date < today:
                delayed += 1
            else:
                in_progress += 1
        else:
            # On hold or other status
            in_progress += 1
    
    total = len(projects)
    
    # Format for Chart.js doughnut chart (expected format: {labels: [], data: []})
    return jsonify({
        'labels': ['On Time', 'Delayed'],
        'data': [
            round((on_time / total * 100), 1) if total > 0 else 0,
            round((delayed / total * 100), 1) if total > 0 else 0
        ]
    })


@dashboard_bp.route('/api/dashboard/status-breakdown')
@admin_required
def status_breakdown():
    """API endpoint for status distribution across all entities"""
    return _get_status_breakdown()

def _get_status_breakdown():
    """API endpoint for status distribution across all entities"""
    
    # Apply filters if provided
    problem_query = Problem.query
    case_query = BusinessCase.query  
    project_query = Project.query
    
    if 'departments' in request.args:
        dept_ids = [int(d) for d in request.args.get('departments').split(',') if d.isdigit()]
        if dept_ids:
            problem_query = problem_query.filter(Problem.department_id.in_(dept_ids))
            project_query = project_query.filter(Project.department_id.in_(dept_ids))
    
    if 'status' in request.args:
        statuses = [s.strip() for s in request.args.get('status').split(',')]
        valid_statuses = [s for s in statuses if hasattr(StatusEnum, s)]
        if valid_statuses:
            status_enums = [getattr(StatusEnum, s) for s in valid_statuses]
            problem_query = problem_query.filter(Problem.status.in_(status_enums))
            case_query = case_query.filter(BusinessCase.status.in_(status_enums))
            project_query = project_query.filter(Project.status.in_(status_enums))
    
    # Get status breakdowns with filters applied
    problem_status = problem_query.with_entities(
        Problem.status, func.count(Problem.id).label('count')
    ).group_by(Problem.status).all()
    
    case_status = case_query.with_entities(
        BusinessCase.status, func.count(BusinessCase.id).label('count')
    ).group_by(BusinessCase.status).all()
    
    project_status = project_query.with_entities(
        Project.status, func.count(Project.id).label('count')
    ).group_by(Project.status).all()
    
    # Create status mapping for consistent ordering
    all_statuses = ['Open', 'InProgress', 'Resolved', 'OnHold']
    status_data = []
    
    for status_name in all_statuses:
        # Find counts for this status across all entity types
        prob_count = next((row.count for row in problem_status if row.status.value == status_name), 0)
        case_count = next((row.count for row in case_status if row.status.value == status_name), 0)
        proj_count = next((row.count for row in project_status if row.status.value == status_name), 0)
        
        # Only include status if it has data
        if prob_count > 0 or case_count > 0 or proj_count > 0:
            status_data.append({
                'status': status_name,
                'problems': prob_count,
                'cases': case_count,
                'projects': proj_count
            })
    
    return jsonify(status_data)




@dashboard_bp.route('/export/dashboard-csv')
@admin_required
def export_dashboard_csv():
    """Export dashboard metrics as CSV"""
    
    # Generate CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Metric', 'Value'])
    
    # Core metrics
    problems_count = Problem.query.count()
    open_cases = BusinessCase.query.filter_by(status=StatusEnum.Open).count()
    active_projects = Project.query.filter(
        Project.status.in_([StatusEnum.Open, StatusEnum.InProgress])
    ).count()
    
    writer.writerow(['Total Problems', problems_count])
    writer.writerow(['Open Business Cases', open_cases])
    writer.writerow(['Active Projects', active_projects])
    
    # Status breakdown
    writer.writerow(['', ''])  # Empty row
    writer.writerow(['Status Breakdown', ''])
    
    for status in StatusEnum:
        prob_count = Problem.query.filter_by(status=status).count()
        case_count = BusinessCase.query.filter_by(status=status).count()
        proj_count = Project.query.filter_by(status=status).count()
        
        writer.writerow([f'Problems - {status.value}', prob_count])
        writer.writerow([f'Cases - {status.value}', case_count])
        writer.writerow([f'Projects - {status.value}', proj_count])
    
    # Convert to bytes
    output.seek(0)
    csv_data = output.getvalue()
    output.close()
    
    # Create response
    csv_buffer = io.BytesIO()
    csv_buffer.write(csv_data.encode('utf-8'))
    csv_buffer.seek(0)
    
    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'dashboard-metrics-{datetime.now().strftime("%Y%m%d")}.csv'
    )


# Filter Helper Functions

def parse_filters():
    """Parse query parameters for filtering dashboard data"""
    filters = {}
    
    # Date range filters
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    
    if from_date:
        try:
            filters['from_date'] = datetime.strptime(from_date, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if to_date:
        try:
            filters['to_date'] = datetime.strptime(to_date, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Department filter (multi-select)
    departments = request.args.get('departments')
    if departments:
        try:
            filters['departments'] = [int(d) for d in departments.split(',') if d.strip()]
        except ValueError:
            pass
    
    # Case type filter
    case_type = request.args.get('case_type')
    if case_type and case_type in ['Reactive', 'Proactive']:
        filters['case_type'] = CaseTypeEnum(case_type)
    
    # Priority filter (multi-select)
    priority = request.args.get('priority')
    if priority:
        valid_priorities = []
        for p in priority.split(','):
            p = p.strip()
            if p in ['High', 'Medium', 'Low']:
                valid_priorities.append(PriorityEnum(p))
        if valid_priorities:
            filters['priority'] = valid_priorities
    
    # Manager filter
    manager = request.args.get('manager')
    if manager:
        try:
            filters['manager'] = int(manager)
        except ValueError:
            pass
    
    # Status filter (multi-select)
    status = request.args.get('status')
    if status:
        valid_statuses = []
        for s in status.split(','):
            s = s.strip()
            # Map display names to enum values
            if s == 'Open':
                valid_statuses.append(StatusEnum.Open)
            elif s == 'In Progress':
                valid_statuses.append(StatusEnum.InProgress)
            elif s == 'Resolved':
                valid_statuses.append(StatusEnum.Resolved)
            elif s == 'On Hold':
                valid_statuses.append(StatusEnum.OnHold)
        if valid_statuses:
            filters['status'] = valid_statuses
    
    return filters

def apply_problem_filters(query, filters):
    """Apply filters to problem query"""
    if 'from_date' in filters:
        query = query.filter(Problem.created_at >= filters['from_date'])
    if 'to_date' in filters:
        query = query.filter(Problem.created_at <= filters['to_date'])
    if 'departments' in filters:
        query = query.filter(Problem.department_id.in_(filters['departments']))
    if 'priority' in filters:
        query = query.filter(Problem.priority.in_(filters['priority']))
    if 'status' in filters:
        query = query.filter(Problem.status.in_(filters['status']))
    if 'manager' in filters:
        # Skip manager filtering for now - reports_to field not available
        pass
    return query

def apply_case_filters(query, filters):
    """Apply filters to business case query"""
    if 'from_date' in filters:
        query = query.filter(BusinessCase.created_at >= filters['from_date'])
    if 'to_date' in filters:
        query = query.filter(BusinessCase.created_at <= filters['to_date'])
    if 'case_type' in filters:
        query = query.filter(BusinessCase.case_type == filters['case_type'])
    if 'status' in filters:
        query = query.filter(BusinessCase.status.in_(filters['status']))
    if 'manager' in filters:
        # Skip manager filtering for now - reports_to field not available
        pass
    return query

def apply_project_filters(query, filters):
    """Apply filters to project query"""
    if 'from_date' in filters:
        query = query.filter(Project.created_at >= filters['from_date'])
    if 'to_date' in filters:
        query = query.filter(Project.created_at <= filters['to_date'])
    if 'departments' in filters:
        query = query.filter(Project.department_id.in_(filters['departments']))
    if 'priority' in filters:
        query = query.filter(Project.priority.in_(filters['priority']))
    if 'status' in filters:
        query = query.filter(Project.status.in_(filters['status']))
    if 'manager' in filters:
        query = query.filter(Project.project_manager_id == filters['manager'])
    return query

# Advanced Analytics Endpoints

@dashboard_bp.route('/api/dashboard/department-heatmap')
@admin_required
def department_heatmap():
    """Department heat-map showing problem/case volumes and ROI by department"""
    return _get_department_heatmap()

@dashboard_bp.route('/api/dashboard-demo/department-heatmap')
def department_heatmap_demo():
    """Demo department heat-map"""
    return _get_department_heatmap()

@dashboard_bp.route('/api/dashboard/time-to-value')
@admin_required
def time_to_value():
    """Time-to-value distribution showing case approval to project completion times"""
    return _get_time_to_value()

@dashboard_bp.route('/api/dashboard-demo/time-to-value')
def time_to_value_demo():
    """Demo time-to-value distribution"""
    return _get_time_to_value()

@dashboard_bp.route('/api/dashboard/risks-issues')
@admin_required
def risks_issues():
    """Risk and issue backlog by project"""
    return _get_risks_issues()

@dashboard_bp.route('/api/dashboard-demo/risks-issues')
def risks_issues_demo():
    """Demo risk and issue backlog"""
    return _get_risks_issues()

@dashboard_bp.route('/api/dashboard/milestone-burndown')
@admin_required
def milestone_burndown():
    """Milestone burn-down chart for active projects"""
    project_id = request.args.get('project_id')
    return _get_milestone_burndown(project_id)

@dashboard_bp.route('/api/dashboard-demo/milestone-burndown')
def milestone_burndown_demo():
    """Demo milestone burn-down"""
    project_id = request.args.get('project_id')
    return _get_milestone_burndown(project_id)

@dashboard_bp.route('/api/dashboard/roi-waterfall')
@admin_required
def roi_waterfall():
    """ROI waterfall chart showing cumulative ROI by case"""
    return _get_roi_waterfall()

@dashboard_bp.route('/api/dashboard-demo/roi-waterfall')
def roi_waterfall_demo():
    """Demo ROI waterfall"""
    return _get_roi_waterfall()

@dashboard_bp.route('/api/dashboard/problem-clusters')
@admin_required
def problem_clusters():
    """Top problem clusters with resolution times"""
    return _get_problem_clusters()

@dashboard_bp.route('/api/dashboard-demo/problem-clusters')
def problem_clusters_demo():
    """Demo problem clusters"""
    return _get_problem_clusters()

@dashboard_bp.route('/api/dashboard/resource-utilization')
@admin_required
def resource_utilization():
    """Resource utilization gauge for BAs/PMs"""
    return _get_resource_utilization()

@dashboard_bp.route('/api/dashboard-demo/resource-utilization')
def resource_utilization_demo():
    """Demo resource utilization"""
    return _get_resource_utilization()

def _get_department_heatmap():
    """Generate department heat-map data with filtering support"""
    filters = parse_filters()
    
    # Base query for problems
    problem_query = db.session.query(
        Department.name,
        func.count(Problem.id).label('problems')
    ).outerjoin(
        Problem, Problem.department_id == Department.id
    )
    problem_query = apply_problem_filters(problem_query, filters)
    problem_metrics = problem_query.group_by(Department.id, Department.name).all()
    
    # Base query for business cases  
    case_query = db.session.query(
        Department.name,
        func.count(BusinessCase.id).label('cases'),
        func.avg(BusinessCase.roi).label('avg_roi')
    ).outerjoin(
        Problem, Problem.department_id == Department.id
    ).outerjoin(
        BusinessCase, BusinessCase.problem_id == Problem.id
    )
    case_query = apply_case_filters(case_query, filters)
    case_metrics = case_query.group_by(Department.id, Department.name).all()
    
    # Base query for projects
    project_query = db.session.query(
        Department.name,
        func.count(Project.id).label('projects')
    ).outerjoin(
        Project, Project.department_id == Department.id
    )
    project_query = apply_project_filters(project_query, filters)
    project_metrics = project_query.group_by(Department.id, Department.name).all()
    
    # Combine metrics by department
    dept_data = {}
    
    # Add problem data
    for dept in problem_metrics:
        if dept.name not in dept_data:
            dept_data[dept.name] = {'problems': 0, 'cases': 0, 'projects': 0, 'avg_roi': 0}
        dept_data[dept.name]['problems'] = dept.problems or 0
    
    # Add case data
    for dept in case_metrics:
        if dept.name not in dept_data:
            dept_data[dept.name] = {'problems': 0, 'cases': 0, 'projects': 0, 'avg_roi': 0}
        dept_data[dept.name]['cases'] = dept.cases or 0
        dept_data[dept.name]['avg_roi'] = round(float(dept.avg_roi or 0), 1)
    
    # Add project data
    for dept in project_metrics:
        if dept.name not in dept_data:
            dept_data[dept.name] = {'problems': 0, 'cases': 0, 'projects': 0, 'avg_roi': 0}
        dept_data[dept.name]['projects'] = dept.projects or 0
    
    # Convert to list format
    heatmap_data = []
    for dept_name, metrics in dept_data.items():
        heatmap_data.append({
            'department': dept_name,
            'problems': metrics['problems'],
            'cases': metrics['cases'], 
            'projects': metrics['projects'],
            'avg_roi': metrics['avg_roi']
        })
    
    return jsonify(heatmap_data)

def _get_time_to_value():
    """Calculate time-to-value distribution"""
    time_data = db.session.query(
        BusinessCase.created_at,
        Project.start_date,
        Project.end_date,
        Project.status
    ).join(
        Project, Project.business_case_id == BusinessCase.id
    ).filter(
        Project.start_date != None
    ).all()
    
    approval_to_start = []
    start_to_completion = []
    
    for record in time_data:
        if record.start_date and record.created_at:
            approval_days = (record.start_date - record.created_at.date()).days
            if approval_days >= 0:
                approval_to_start.append(approval_days)
        
        if record.end_date and record.start_date and record.status == StatusEnum.Resolved:
            completion_days = (record.end_date - record.start_date).days
            if completion_days >= 0:
                start_to_completion.append(completion_days)
    
    # Create histogram buckets
    def create_buckets(data, bucket_size=7):
        if not data:
            return {'labels': [], 'data': []}
        
        max_days = max(data) if data else 0
        bucket_count = min((max_days // bucket_size) + 1, 10)
        buckets = [0] * bucket_count
        labels = []
        
        for i in range(bucket_count):
            start = i * bucket_size
            end = start + bucket_size - 1
            labels.append(f"{start}-{end}")
            
            for day in data:
                if start <= day <= end:
                    buckets[i] += 1
        
        return {'labels': labels, 'data': buckets}
    
    approval_buckets = create_buckets(approval_to_start)
    completion_buckets = create_buckets(start_to_completion)
    
    return jsonify({
        'approval_to_start': approval_buckets,
        'start_to_completion': completion_buckets
    })

def _get_risks_issues():
    """Get risk and issue backlog data"""
    projects = Project.query.all()
    risk_data = []
    
    for project in projects:
        milestone_count = ProjectMilestone.query.filter_by(project_id=project.id).count()
        overdue_milestones = ProjectMilestone.query.filter(
            ProjectMilestone.project_id == project.id,
            ProjectMilestone.due_date < datetime.now().date(),
            ProjectMilestone.completed == False
        ).count()
        
        risk_count = overdue_milestones + (1 if project.budget and project.budget > 50000 else 0)
        issue_count = overdue_milestones
        highest_severity = "High" if overdue_milestones > 2 else "Medium" if overdue_milestones > 0 else "Low"
        
        risk_data.append({
            'project_code': project.code or f"PRJ{project.id:04d}",
            'risk_count': risk_count,
            'issue_count': issue_count,
            'highest_severity': highest_severity
        })
    
    return jsonify(risk_data)

def _get_milestone_burndown(project_id=None):
    """Get milestone burn-down data"""
    if project_id:
        projects = [Project.query.get(project_id)] if Project.query.get(project_id) else []
    else:
        projects = Project.query.filter(
            Project.status.in_([StatusEnum.Open, StatusEnum.InProgress])
        ).limit(3).all()
    
    burndown_data = []
    
    for project in projects:
        milestones = ProjectMilestone.query.filter_by(project_id=project.id).order_by(ProjectMilestone.due_date).all()
        
        if milestones:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            timeline = []
            current_date = start_date
            total_milestones = len(milestones)
            
            while current_date <= end_date:
                days_elapsed = (current_date - start_date).days
                planned_completed = min(total_milestones, (days_elapsed / 30) * total_milestones)
                
                actual_completed = sum(1 for m in milestones 
                                     if m.completed and m.completion_date and m.completion_date <= current_date)
                
                timeline.append({
                    'date': current_date.isoformat(),
                    'planned': round(planned_completed, 1),
                    'actual': actual_completed
                })
                
                current_date += timedelta(days=2)
            
            burndown_data.append({
                'project': project.name,
                'timeline': timeline
            })
    
    return jsonify(burndown_data)

def _get_roi_waterfall():
    """Generate ROI waterfall chart data"""
    cases = BusinessCase.query.filter(
        BusinessCase.cost_estimate > 0,
        BusinessCase.benefit_estimate > 0
    ).order_by((BusinessCase.benefit_estimate - BusinessCase.cost_estimate).desc()).limit(10).all()
    
    waterfall_data = []
    for case in cases:
        net_benefit = case.benefit_estimate - case.cost_estimate
        waterfall_data.append({
            'case_code': case.code or f"C{case.id:04d}",
            'net_benefit': round(net_benefit, 0),
            'cost': case.cost_estimate,
            'benefit': case.benefit_estimate
        })
    
    return jsonify(waterfall_data)

def _get_problem_clusters():
    """Analyze problem clusters and resolution patterns"""
    recent_problems = Problem.query.filter(
        Problem.created_at >= datetime.now() - timedelta(days=30)
    ).all()
    
    clusters = {}
    business_terms = ['cost', 'efficiency', 'process', 'quality', 'customer', 'system', 'performance', 'security', 'workflow', 'data']
    
    for problem in recent_problems:
        text = f"{problem.title} {problem.description}".lower()
        found_terms = [term for term in business_terms if term in text]
        
        cluster_key = found_terms[0] if found_terms else 'general'
        
        if cluster_key not in clusters:
            clusters[cluster_key] = {
                'count': 0,
                'total_resolution_days': 0,
                'resolved_count': 0
            }
        
        clusters[cluster_key]['count'] += 1
        
        if problem.status == StatusEnum.Resolved:
            resolution_days = (datetime.now() - problem.created_at).days
            clusters[cluster_key]['total_resolution_days'] += resolution_days
            clusters[cluster_key]['resolved_count'] += 1
    
    cluster_data = []
    for cluster_name, data in sorted(clusters.items(), key=lambda x: x[1]['count'], reverse=True)[:5]:
        avg_resolution = (data['total_resolution_days'] / data['resolved_count']) if data['resolved_count'] > 0 else 0
        cluster_data.append({
            'cluster_label': cluster_name.title(),
            'count': data['count'],
            'avg_resolution_days': round(avg_resolution, 1)
        })
    
    return jsonify(cluster_data)

def _get_resource_utilization():
    """Calculate resource utilization for BAs/PMs"""
    ba_pm_users = User.query.filter(
        User.role.in_([RoleEnum.BA, RoleEnum.PM])
    ).all()
    
    total_capacity_hours = len(ba_pm_users) * 40 * 4  # 40 hours/week * 4 weeks
    
    active_projects = Project.query.filter(
        Project.status.in_([StatusEnum.Open, StatusEnum.InProgress])
    ).all()
    
    assigned_hours = len(active_projects) * 20  # 20 hours per active project
    
    utilization_pct = min(100, (assigned_hours / total_capacity_hours * 100)) if total_capacity_hours > 0 else 0
    
    return jsonify({
        'total_capacity_hours': total_capacity_hours,
        'assigned_hours': assigned_hours,
        'utilization_pct': round(utilization_pct, 1),
        'available_hours': total_capacity_hours - assigned_hours,
        'ba_pm_count': len(ba_pm_users)
    })


# Drill-Down API Endpoints

@dashboard_bp.route('/api/dashboard/drilldown')
@admin_required
def drilldown_data():
    """Generic drill-down endpoint for chart exploration"""
    return _get_drilldown_data()

@dashboard_bp.route('/api/dashboard-demo/drilldown')
def drilldown_data_demo():
    """Demo drill-down endpoint for chart exploration"""
    return _get_drilldown_data()

def _get_drilldown_data():
    """Get drill-down data based on chart type and context"""
    chart_type = request.args.get('chart')
    value = request.args.get('value')
    filters = parse_filters()
    
    if chart_type == 'deptHeatmap':
        return _drilldown_department(value, filters)
    elif chart_type == 'timeToValue':
        return _drilldown_time_range(value, filters)
    elif chart_type == 'riskIssue':
        return _drilldown_project(value, filters)
    elif chart_type == 'problemClusters':
        return _drilldown_problem_cluster(value, filters)
    elif chart_type == 'roiWaterfall':
        return _drilldown_business_case(value, filters)
    elif chart_type == 'milestones':
        return _drilldown_project_milestones(value, filters)
    else:
        return jsonify({'error': 'Unknown chart type'}), 400

def _drilldown_department(dept_name, filters):
    """Drill-down into department-specific data"""
    # Get department by name
    department = Department.query.filter_by(name=dept_name).first()
    if not department:
        return jsonify({'error': 'Department not found'}), 404
    
    # Problems in this department
    problem_query = Problem.query.filter_by(department_id=department.id)
    problem_query = apply_problem_filters(problem_query, filters)
    problems = problem_query.all()
    
    # Business cases linked to department problems
    case_query = BusinessCase.query.join(Problem).filter(Problem.department_id == department.id)
    case_query = apply_case_filters(case_query, filters)
    cases = case_query.all()
    
    # Projects in this department
    project_query = Project.query.filter_by(department_id=department.id)
    project_query = apply_project_filters(project_query, filters)
    projects = project_query.all()
    
    return jsonify({
        'department': dept_name,
        'problems': [{
            'id': p.id,
            'code': p.code or f'P{p.id:04d}',
            'title': p.title,
            'priority': p.priority.value,
            'status': p.status.value,
            'created_at': p.created_at.strftime('%Y-%m-%d'),
            'url': f'/problems/{p.id}'
        } for p in problems],
        'cases': [{
            'id': c.id,
            'code': c.code or f'C{c.id:04d}',
            'title': c.title,
            'cost_estimate': c.cost_estimate,
            'benefit_estimate': c.benefit_estimate,
            'roi': c.roi,
            'status': c.status.value,
            'url': f'/business/{c.id}'
        } for c in cases],
        'projects': [{
            'id': p.id,
            'code': p.code or f'PRJ{p.id:04d}',
            'name': p.name,
            'budget': p.budget,
            'status': p.status.value,
            'start_date': p.start_date.strftime('%Y-%m-%d') if p.start_date else None,
            'end_date': p.end_date.strftime('%Y-%m-%d') if p.end_date else None,
            'url': f'/projects/{p.id}'
        } for p in projects]
    })

def _drilldown_time_range(time_range, filters):
    """Drill-down into time-to-value range data"""
    # Parse time range (e.g., "7-14" days)
    try:
        start_days, end_days = map(int, time_range.split('-'))
    except:
        return jsonify({'error': 'Invalid time range format'}), 400
    
    # Find projects within this time range
    projects_in_range = []
    project_query = Project.query.join(BusinessCase)
    project_query = apply_project_filters(project_query, filters)
    
    for project in project_query.all():
        if project.start_date and project.business_case:
            approval_days = (project.start_date - project.business_case.created_at.date()).days
            if start_days <= approval_days <= end_days:
                projects_in_range.append({
                    'id': project.id,
                    'code': project.code or f'PRJ{project.id:04d}',
                    'name': project.name,
                    'approval_days': approval_days,
                    'start_date': project.start_date.strftime('%Y-%m-%d'),
                    'case_title': project.business_case.title,
                    'url': f'/projects/{project.id}'
                })
    
    return jsonify({
        'time_range': time_range,
        'projects': projects_in_range
    })

def _drilldown_project(project_code, filters):
    """Drill-down into project risks and issues"""
    project = Project.query.filter_by(code=project_code).first()
    if not project:
        # Try by ID format
        try:
            project_id = int(project_code.replace('PRJ', ''))
            project = Project.query.get(project_id)
        except:
            pass
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Get overdue milestones (treated as issues)
    overdue_milestones = ProjectMilestone.query.filter(
        ProjectMilestone.project_id == project.id,
        ProjectMilestone.due_date < datetime.now().date(),
        ProjectMilestone.completed == False
    ).all()
    
    # Simulate risks based on project characteristics
    risks = []
    if project.budget and project.budget > 50000:
        risks.append({
            'type': 'Budget',
            'description': 'High budget project requires additional oversight',
            'severity': 'Medium'
        })
    
    if len(overdue_milestones) > 2:
        risks.append({
            'type': 'Schedule',
            'description': 'Multiple overdue milestones indicate schedule risk',
            'severity': 'High'
        })
    
    return jsonify({
        'project': {
            'code': project.code or f'PRJ{project.id:04d}',
            'name': project.name,
            'status': project.status.value,
            'url': f'/projects/{project.id}'
        },
        'risks': risks,
        'issues': [{
            'id': m.id,
            'name': m.name,
            'due_date': m.due_date.strftime('%Y-%m-%d'),
            'days_overdue': (datetime.now().date() - m.due_date).days,
            'owner': m.owner.name if m.owner else 'Unassigned'
        } for m in overdue_milestones]
    })

def _drilldown_problem_cluster(cluster_label, filters):
    """Drill-down into problem cluster details"""
    # Find problems matching this cluster
    recent_problems = Problem.query.filter(
        Problem.created_at >= datetime.now() - timedelta(days=30)
    )
    recent_problems = apply_problem_filters(recent_problems, filters)
    
    cluster_problems = []
    for problem in recent_problems.all():
        text = f"{problem.title} {problem.description}".lower()
        if cluster_label.lower() in text:
            cluster_problems.append({
                'id': problem.id,
                'code': problem.code or f'P{problem.id:04d}',
                'title': problem.title,
                'priority': problem.priority.value,
                'status': problem.status.value,
                'created_at': problem.created_at.strftime('%Y-%m-%d'),
                'resolution_days': (datetime.now() - problem.created_at).days if problem.status == StatusEnum.Resolved else None,
                'url': f'/problems/{problem.id}'
            })
    
    return jsonify({
        'cluster': cluster_label,
        'problems': cluster_problems
    })

def _drilldown_business_case(case_code, filters):
    """Drill-down into business case details"""
    case = BusinessCase.query.filter_by(code=case_code).first()
    if not case:
        # Try by ID format
        try:
            case_id = int(case_code.replace('C', ''))
            case = BusinessCase.query.get(case_id)
        except:
            pass
    
    if not case:
        return jsonify({'error': 'Business case not found'}), 404
    
    # Get related projects
    projects = Project.query.filter_by(business_case_id=case.id).all()
    
    return jsonify({
        'case': {
            'id': case.id,
            'code': case.code or f'C{case.id:04d}',
            'title': case.title,
            'cost_estimate': case.cost_estimate,
            'benefit_estimate': case.benefit_estimate,
            'net_benefit': case.benefit_estimate - case.cost_estimate,
            'roi': case.roi,
            'status': case.status.value,
            'url': f'/business/{case.id}'
        },
        'projects': [{
            'id': p.id,
            'code': p.code or f'PRJ{p.id:04d}',
            'name': p.name,
            'status': p.status.value,
            'budget': p.budget,
            'url': f'/projects/{p.id}'
        } for p in projects]
    })

def _drilldown_project_milestones(project_code, filters):
    """Drill-down into project milestone details"""
    project = Project.query.filter_by(code=project_code).first()
    if not project:
        try:
            project_id = int(project_code.replace('PRJ', ''))
            project = Project.query.get(project_id)
        except:
            pass
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    milestones = ProjectMilestone.query.filter_by(project_id=project.id).order_by(ProjectMilestone.due_date).all()
    
    return jsonify({
        'project': {
            'code': project.code or f'PRJ{project.id:04d}',
            'name': project.name,
            'url': f'/projects/{project.id}'
        },
        'milestones': [{
            'id': m.id,
            'name': m.name,
            'due_date': m.due_date.strftime('%Y-%m-%d'),
            'completed': m.completed,
            'completion_date': m.completion_date.strftime('%Y-%m-%d') if m.completion_date else None,
            'owner': m.owner.name if m.owner else 'Unassigned',
            'status': 'Completed' if m.completed else ('Overdue' if m.due_date < datetime.now().date() else 'On Track')
        } for m in milestones]
    })


# Register blueprint with app
def register_dashboard_blueprint(app):
    """Register dashboard blueprint with the Flask app"""
    app.register_blueprint(dashboard_bp)