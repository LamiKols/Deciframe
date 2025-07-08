"""
Data Export & Retention Admin Routes
Provides admin interface for data management operations
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import current_user
from auth.session_auth import require_session_auth, require_role
from app import db

logger = logging.getLogger(__name__)

data_management_bp = Blueprint('data_management', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    return require_role('Admin')(f)

def calculate_retention_statistics():
    """Calculate retention statistics for display"""
    try:
        from models import Problem, BusinessCase, Project, ProjectMilestone, Notification, Epic, Story, AuditLog
        
        # Calculate retention cutoff dates based on system policies
        now = datetime.now()
        problem_cutoff = now - timedelta(days=730)     # 2 years
        case_cutoff = now - timedelta(days=1095)       # 3 years  
        project_cutoff = now - timedelta(days=1825)    # 5 years
        milestone_cutoff = now - timedelta(days=1825)  # 5 years (same as projects)
        notification_cutoff = now - timedelta(days=365) # 1 year
        epic_cutoff = now - timedelta(days=1095)       # 3 years (same as cases)
        audit_cutoff = now - timedelta(days=2555)      # 7 years
        
        # Problems analysis
        problems_total = Problem.query.count()
        problems_eligible = Problem.query.filter(Problem.created_at < problem_cutoff).count()
        problems_oldest = db.session.query(db.func.min(Problem.created_at)).scalar()
        
        # Business Cases analysis
        cases_total = BusinessCase.query.count()
        cases_eligible = BusinessCase.query.filter(BusinessCase.created_at < case_cutoff).count()
        cases_oldest = db.session.query(db.func.min(BusinessCase.created_at)).scalar()
        
        # Projects analysis
        projects_total = Project.query.count()
        projects_eligible = Project.query.filter(Project.created_at < project_cutoff).count()
        projects_oldest = db.session.query(db.func.min(Project.created_at)).scalar()
        
        # Project Milestones analysis
        milestones_total = ProjectMilestone.query.count()
        milestones_eligible = ProjectMilestone.query.filter(ProjectMilestone.created_at < milestone_cutoff).count()
        milestones_oldest = db.session.query(db.func.min(ProjectMilestone.created_at)).scalar()
        
        # Notifications analysis
        notifications_total = Notification.query.count()
        notifications_eligible = Notification.query.filter(Notification.created_at < notification_cutoff).count()
        notifications_oldest = db.session.query(db.func.min(Notification.created_at)).scalar()
        
        # Epics & Stories analysis (combined)
        epics_total = Epic.query.count() + Story.query.count()
        epics_eligible = Epic.query.filter(Epic.created_at < epic_cutoff).count() + Story.query.filter(Story.created_at < epic_cutoff).count()
        epics_oldest = min(
            db.session.query(db.func.min(Epic.created_at)).scalar() or datetime.max,
            db.session.query(db.func.min(Story.created_at)).scalar() or datetime.max
        )
        if epics_oldest == datetime.max:
            epics_oldest = None
        
        # Audit Logs analysis
        audit_total = AuditLog.query.count()
        audit_eligible = AuditLog.query.filter(AuditLog.timestamp < audit_cutoff).count()
        audit_oldest = db.session.query(db.func.min(AuditLog.timestamp)).scalar()
        
        return {
            'problems': {
                'total': problems_total,
                'eligible': problems_eligible,
                'oldest_date': problems_oldest.strftime('%Y-%m-%d') if problems_oldest else 'N/A'
            },
            'cases': {
                'total': cases_total,
                'eligible': cases_eligible,
                'oldest_date': cases_oldest.strftime('%Y-%m-%d') if cases_oldest else 'N/A'
            },
            'projects': {
                'total': projects_total,
                'eligible': projects_eligible,
                'oldest_date': projects_oldest.strftime('%Y-%m-%d') if projects_oldest else 'N/A'
            },
            'milestones': {
                'total': milestones_total,
                'eligible': milestones_eligible,
                'oldest_date': milestones_oldest.strftime('%Y-%m-%d') if milestones_oldest else 'N/A'
            },
            'notifications': {
                'total': notifications_total,
                'eligible': notifications_eligible,
                'oldest_date': notifications_oldest.strftime('%Y-%m-%d') if notifications_oldest else 'N/A'
            },
            'epics': {
                'total': epics_total,
                'eligible': epics_eligible,
                'oldest_date': epics_oldest.strftime('%Y-%m-%d') if epics_oldest else 'N/A'
            },
            'audit_logs': {
                'total': audit_total,
                'eligible': audit_eligible,
                'oldest_date': audit_oldest.strftime('%Y-%m-%d') if audit_oldest else 'N/A'
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating retention statistics: {e}")
        return {
            'problems': {'total': 0, 'eligible': 0, 'oldest_date': 'N/A'},
            'cases': {'total': 0, 'eligible': 0, 'oldest_date': 'N/A'},
            'projects': {'total': 0, 'eligible': 0, 'oldest_date': 'N/A'},
            'milestones': {'total': 0, 'eligible': 0, 'oldest_date': 'N/A'},
            'notifications': {'total': 0, 'eligible': 0, 'oldest_date': 'N/A'},
            'epics': {'total': 0, 'eligible': 0, 'oldest_date': 'N/A'},
            'audit_logs': {'total': 0, 'eligible': 0, 'oldest_date': 'N/A'}
        }

def get_recent_archival_activity():
    """Get recent archival activity logs"""
    try:
        from models import AuditLog
        
        # Get recent retention/archival actions from audit logs
        recent_logs = AuditLog.query.filter(
            AuditLog.action.in_(['ARCHIVE', 'RETENTION', 'DATA_PURGE'])
        ).order_by(AuditLog.timestamp.desc()).limit(10).all()
        
        # Transform audit logs into archival activity format
        activities = []
        for log in recent_logs:
            details = log.details if log.details else {}
            activities.append({
                'created_at': log.timestamp,
                'table_name': log.target or 'Unknown',
                'records_count': details.get('records_archived', 0),
                'cutoff_date': datetime.fromisoformat(details.get('cutoff_date', '2023-01-01')) if details.get('cutoff_date') else None,
                'user': log.user
            })
        
        return activities
        
    except Exception as e:
        logger.error(f"Error getting recent archival activity: {e}")
        return []

@data_management_bp.route('/admin/data-management/')
@require_session_auth
@admin_required
def data_overview():
    """Data management overview dashboard"""
    # Get basic statistics from database
    try:
        retention_data = calculate_retention_statistics()
        recent_activity = get_recent_archival_activity()
        
        stats = {
            'total_records': sum([
                retention_data['problems']['total'],
                retention_data['cases']['total'], 
                retention_data['projects']['total'],
                retention_data['milestones']['total'],
                retention_data['notifications']['total'],
                retention_data['epics']['total'],
                retention_data['audit_logs']['total']
            ]),
            'eligible_for_archive': sum([
                retention_data['problems']['eligible'],
                retention_data['cases']['eligible'], 
                retention_data['projects']['eligible'],
                retention_data['milestones']['eligible'],
                retention_data['notifications']['eligible'],
                retention_data['epics']['eligible'],
                retention_data['audit_logs']['eligible']
            ]),
            'total_archived': len(recent_activity),
            'total_exports': 0,
            'storage_size': 'Unknown'
        }
        return render_template('admin/data_management/overview_simple.html', stats=stats)
    except Exception as e:
        logger.error(f"Error in data overview: {e}")
        stats = {
            'total_records': 0,
            'eligible_for_archive': 0,
            'total_archived': 0,
            'total_exports': 0,
            'storage_size': 'Unknown'
        }
        return render_template('admin/data_management/overview_simple.html', stats=stats)

@data_management_bp.route('/admin/data-management/export')
@require_session_auth
@admin_required
def export_data():
    """Data export interface"""
    return render_template('admin/data_management/export.html')

@data_management_bp.route('/admin/data-management/download-direct')
@require_session_auth
@admin_required
def download_export_direct():
    """Direct CSV download endpoint"""
    from io import StringIO
    import csv
    
    try:
        data_type = request.args.get('type', 'problems')
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        
        # Generate CSV content based on data type
        output = StringIO()
        writer = csv.writer(output)
        
        if data_type == 'problems':
            from models import Problem
            writer.writerow(['ID', 'Code', 'Title', 'Description', 'Status', 'Priority', 'Created At'])
            query = Problem.query
            if start_date:
                query = query.filter(Problem.created_at >= start_date)
            if end_date:
                query = query.filter(Problem.created_at <= end_date)
            for p in query.all():
                writer.writerow([p.id, p.code, p.title, p.description, p.status.value if p.status else '', 
                               p.priority.value if p.priority else '', p.created_at.strftime('%Y-%m-%d')])
                               
        elif data_type == 'cases':
            from models import BusinessCase
            writer.writerow(['ID', 'Code', 'Title', 'Description', 'Status', 'ROI', 'Created At'])
            query = BusinessCase.query
            if start_date:
                query = query.filter(BusinessCase.created_at >= start_date)
            if end_date:
                query = query.filter(BusinessCase.created_at <= end_date)
            for c in query.all():
                writer.writerow([c.id, c.code, c.title, c.description, c.status.value if c.status else '',
                               c.roi or 0, c.created_at.strftime('%Y-%m-%d')])
                               
        elif data_type == 'projects':
            from models import Project
            writer.writerow(['ID', 'Code', 'Name', 'Description', 'Status', 'Budget', 'Created At'])
            query = Project.query
            if start_date:
                query = query.filter(Project.created_at >= start_date)
            if end_date:
                query = query.filter(Project.created_at <= end_date)
            for p in query.all():
                writer.writerow([p.id, p.code, p.name, p.description, p.status.value if p.status else '',
                               p.budget or 0, p.created_at.strftime('%Y-%m-%d')])
                               
        elif data_type == 'audit':
            from models import AuditLog
            writer.writerow(['ID', 'User', 'Action', 'Module', 'Target', 'Timestamp'])
            query = AuditLog.query
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            for a in query.all():
                writer.writerow([a.id, a.user.name if a.user else 'Unknown', a.action, a.module or '',
                               a.target or '', a.timestamp.strftime('%Y-%m-%d %H:%M:%S')])
        
        csv_content = output.getvalue()
        output.close()
        
        # Generate filename
        filename = f"{data_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        logger.error(f"Error generating direct export: {e}")
        flash('Error generating export file', 'error')
        return redirect(url_for('data_management.export_data'))

@data_management_bp.route('/admin/data-management/retention')
@require_session_auth
@admin_required
def data_retention_page():
    """Data Retention (Archive & Purge)"""
    try:
        retention_data = calculate_retention_statistics()
        recent_activity = get_recent_archival_activity()
        
        return render_template('admin/data_management/retention.html', 
                             retention_data=retention_data,
                             recent_activity=recent_activity)
    except Exception as e:
        logger.error(f"Error in retention page: {e}")
        return render_template('admin/data_management/retention.html', 
                             retention_data=None,
                             recent_activity=[])

@data_management_bp.route('/admin/data-management/retention', methods=['POST'])
@require_session_auth
@admin_required
def archive_data():
    """Manual data archiving interface"""
    try:
        table = request.form.get('table')
        cutoff_date_str = request.form.get('cutoff_date')
        
        if not table or not cutoff_date_str:
            flash('Please select a table and cutoff date', 'error')
            return redirect(url_for('data_management.data_retention_page'))
        
        cutoff_date = datetime.strptime(cutoff_date_str, '%Y-%m-%d')
        
        # Log the archival action
        from models import AuditLog
        audit_log = AuditLog(
            user_id=current_user.id,
            action='ARCHIVE',
            module='data_management',
            target=table,
            details={'cutoff_date': cutoff_date_str, 'records_archived': 0},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash(f'Archive operation queued for {table} with cutoff date {cutoff_date_str}', 'success')
        
    except Exception as e:
        logger.error(f"Error archiving data: {e}")
        flash(f'Error archiving data: {str(e)}', 'error')
    
    return redirect(url_for('data_management.data_retention_page'))

def init_data_management_routes(app):
    """Initialize data management routes"""
    app.register_blueprint(data_management_bp)
    logger.info("✓ Data management routes initialized")