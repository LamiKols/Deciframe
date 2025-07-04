"""
Data Export & Retention Admin Routes
Provides admin interface for data management operations
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import current_user
from auth.session_auth import require_session_auth, require_role
from admin.data_management import DataManagementService
from models import DataRetentionPolicy, ExportJob, RetentionLog, StatusEnum, PriorityEnum
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
        from models import Problem, BusinessCase, Project
        
        stats = {
            'total_active': Problem.query.count() + BusinessCase.query.count() + Project.query.count(),
            'total_archived': 0,  # No archived data yet
            'total_exports': 0,   # No export tracking yet
            'storage_size': '2.5 GB'  # Placeholder
        }
        
        return render_template('admin/data_management/overview_simple.html', stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading data overview: {e}")
        # Provide fallback stats to prevent template errors
        stats = {
            'total_active': 0,
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
    from flask import Response
    
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
                               p.priority.value if p.priority else '', p.created_at])
        
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
                               c.roi, c.created_at])
        
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
                               p.budget, p.created_at])
        
        elif data_type == 'audit':
            from models import AuditLog
            writer.writerow(['ID', 'User', 'Action', 'Module', 'Target', 'Timestamp'])
            query = AuditLog.query
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            for a in query.all():
                writer.writerow([a.id, a.user.name if a.user else 'System', a.action, a.module, 
                               a.target, a.timestamp])
        
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{data_type}_export_{timestamp}.csv"
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error in direct CSV export: {e}")
        flash('Error generating CSV export', 'error')
        return redirect(url_for('data_management.export_data'))

@data_management_bp.route('/admin/data-management/retention', methods=['GET', 'POST'])
@require_session_auth
@admin_required
def data_retention_page():
    """Data Retention (Archive & Purge)"""
    if request.method == 'POST':
        try:
            table = request.form['table']         # 'problems','cases','projects'
            cutoff = datetime.fromisoformat(request.form['cutoff'])
            
            # Archive and delete data
            archive_sql = f"INSERT INTO archived_{table} SELECT * FROM {table} WHERE created_at < :cutoff"
            delete_sql = f"DELETE FROM {table} WHERE created_at < :cutoff"
            
            result = db.session.execute(db.text(archive_sql), {'cutoff': cutoff})
            deleted = db.session.execute(db.text(delete_sql), {'cutoff': cutoff})
            
            # Log the retention action
            from models import RetentionLog
            db.session.add(RetentionLog(
                table_name=table,
                cutoff_date=cutoff,
                archived_count=deleted.rowcount,
                created_by=current_user.id
            ))
            db.session.commit()
            
            flash(f"Archived & purged {deleted.rowcount} rows from {table}.", 'success')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in data retention: {e}")
            flash(f'Error in data retention: {str(e)}', 'error')
            
        return redirect(url_for('data_management.data_retention_page'))
    
    # Calculate retention data for display
    retention_data = calculate_retention_statistics()
    recent_archives = get_recent_archival_activity()
    
    return render_template('admin/data_management/retention.html', 
                         retention_data=retention_data,
                         recent_archives=recent_archives)

@data_management_bp.route('/admin/data-management/archive', methods=['GET', 'POST'])
@require_session_auth
@admin_required
def archive_data():
    """Manual data archiving interface"""
    if request.method == 'GET':
        policies = DataManagementService.get_retention_policies()
        return render_template('admin/data_management/archive.html', policies=policies)
    
    try:
        table_name = request.form.get('table_name')
        months_old = int(request.form.get('months_old', 24))
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=months_old * 30)
        
        # Archive data
        archived_count = DataManagementService.archive_old_data(
            table_name=table_name,
            cutoff_date=cutoff_date,
            user_id=current_user.id
        )
        
        flash(f'Successfully archived {archived_count} records from {table_name}', 'success')
        
    except Exception as e:
        logger.error(f"Error archiving data: {e}")
        flash(f'Error archiving data: {str(e)}', 'error')
    
    return redirect(url_for('data_management.archive_data'))


        
        flash(f'Export job started for {table_name} data', 'success')
        
    except Exception as e:
        logger.error(f"Error starting export: {e}")
        flash(f'Error starting export: {str(e)}', 'error')
    
    return redirect(url_for('data_management.export_data'))

@data_management_bp.route('/admin/data-management/export/download')
@require_session_auth
@admin_required
def download_export_direct():
    """Direct CSV download for immediate exports"""
    try:
        dtype = request.args.get('type')    # 'problems','cases','projects','audit'
        start = request.args.get('start')   # 'YYYY-MM-DD'
        end = request.args.get('end')
        
        # Map dtype to Model
        from models import Problem, BusinessCase, Project, AuditLog
        model_map = {
            'problems': Problem, 
            'cases': BusinessCase, 
            'projects': Project, 
            'audit': AuditLog
        }
        
        Model = model_map.get(dtype)
        if not Model:
            flash('Invalid data type.', 'error')
            return redirect(url_for('data_management.export_data'))

        q = Model.query
        if start:
            q = q.filter(Model.created_at >= datetime.fromisoformat(start))
        if end:
            q = q.filter(Model.created_at <= datetime.fromisoformat(end))

        filename = f"{dtype}_{start or 'begin'}_{end or 'now'}.csv"
        
        def generate():
            cols = [c.name for c in Model.__table__.columns]
            yield ','.join(cols) + '\n'
            for row in q.yield_per(100):
                vals = [str(getattr(row, c)) for c in cols]
                yield ','.join(f'"{v}"' for v in vals) + '\n'

        from flask import Response
        return Response(
            generate(), 
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename={filename}'}
        )
        
    except Exception as e:
        logger.error(f"Error generating direct export: {e}")
        flash('Error generating export file', 'error')
        return redirect(url_for('data_management.export_data'))

@data_management_bp.route('/admin/data-management/export/<int:job_id>/download')
@require_session_auth
@admin_required
def download_export(job_id):
    """Download completed export file"""
    try:
        export_job = ExportJob.query.get_or_404(job_id)
        
        # Check if user owns this export or is admin
        if export_job.user_id != current_user.id and current_user.role.value != 'Admin':
            flash('Unauthorized to download this export', 'error')
            return redirect(url_for('data_management.export_data'))
        
        if export_job.status != 'Complete' or not export_job.file_path:
            flash('Export file not available', 'error')
            return redirect(url_for('data_management.export_data'))
        
        if not os.path.exists(export_job.file_path):
            flash('Export file no longer exists', 'error')
            return redirect(url_for('data_management.export_data'))
        
        filename = os.path.basename(export_job.file_path)
        return send_file(export_job.file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Error downloading export: {e}")
        flash('Error downloading export file', 'error')
        return redirect(url_for('data_management.export_data'))

@data_management_bp.route('/admin/data-management/logs')
@require_session_auth
@admin_required
def retention_logs():
    """View retention logs"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    logs = RetentionLog.query.order_by(RetentionLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/data_management/logs.html', logs=logs)

@data_management_bp.route('/admin/data-management/exports')
@require_session_auth
@admin_required
def export_jobs():
    """View all export jobs"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    jobs = ExportJob.query.order_by(ExportJob.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/data_management/export_jobs.html', jobs=jobs)

@data_management_bp.route('/admin/data-management/cleanup')
@require_session_auth
@admin_required
def cleanup_exports():
    """Clean up old export files"""
    try:
        days_old = int(request.args.get('days', 30))
        cleaned_count = DataManagementService.cleanup_old_exports(days_old)
        flash(f'Cleaned up {cleaned_count} old export files', 'success')
        
    except Exception as e:
        logger.error(f"Error cleaning up exports: {e}")
        flash('Error cleaning up old exports', 'error')
    
    return redirect(url_for('data_management.export_jobs'))

@data_management_bp.route('/admin/data-management/api/stats')
@require_session_auth
@admin_required
def api_stats():
    """API endpoint for real-time statistics"""
    try:
        stats = DataManagementService.get_table_statistics()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500

@data_management_bp.route('/admin/data-management/api/export-status/<int:job_id>')
@require_session_auth
@admin_required
def api_export_status(job_id):
    """API endpoint for export job status"""
    try:
        export_job = ExportJob.query.get_or_404(job_id)
        
        return jsonify({
            'id': export_job.id,
            'status': export_job.status,
            'row_count': export_job.row_count,
            'file_size': export_job.file_size,
            'error_message': export_job.error_message,
            'completed_at': export_job.completed_at.isoformat() if export_job.completed_at else None
        })
        
    except Exception as e:
        logger.error(f"Error getting export status: {e}")
        return jsonify({'error': 'Failed to get export status'}), 500

def init_data_management_routes(app):
    """Initialize data management routes"""
    app.register_blueprint(data_management_bp)
    logger.info("✓ Data management routes initialized")