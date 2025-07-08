"""
Admin Routes for Report Management
Handles report template CRUD operations, preview, and manual execution
"""

import json
import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from app import db
from models import ReportTemplate, ReportRun, User, RoleEnum, ReportFrequencyEnum, ReportTypeEnum
from reports.service import ReportService
from reports.scheduler import report_scheduler

reports_bp = Blueprint('reports', __name__, url_prefix='/admin/reports')

def admin_required(f):
    """Decorator to require admin/director/CEO roles for report management"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function_reports(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        
        if current_user.role not in [RoleEnum.Admin, RoleEnum.Director, RoleEnum.CEO]:
            return jsonify({"error": "Admin access required"}), 403
        
        return f(*args, **kwargs)
    return decorated_function_reports

@reports_bp.route('/')
@login_required
@admin_required
def list_templates():
    """List all report templates"""
    templates = ReportTemplate.query.order_by(ReportTemplate.created_at.desc()).all()
    return render_template('admin/reports.html', templates=templates)

@reports_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_template():
    """Create a new report template"""
    if request.method == 'POST':
        try:
            # Parse form data
            name = request.form.get('name')
            description = request.form.get('description')
            frequency = request.form.get('frequency')
            template_type = request.form.get('template_type')
            mailing_list = request.form.get('mailing_list', '[]')
            filters = request.form.get('filters', '{}')
            
            # Validation
            if not name or not frequency or not template_type:
                flash('Name, frequency, and template type are required', 'error')
                return render_template('admin/report_form.html')
            
            # Create template
            template = ReportTemplate()
            template.name = name
            template.description = description
            template.frequency = ReportFrequencyEnum(frequency)
            template.template_type = ReportTypeEnum(template_type)
            template.mailing_list = mailing_list
            template.filters = filters
            template.created_by = current_user.id
            template.active = True
            
            db.session.add(template)
            db.session.commit()
            
            flash(f'Report template "{name}" created successfully', 'success')
            return redirect(url_for('reports.list_templates'))
            
        except Exception as e:
            logging.error(f"Error creating report template: {str(e)}")
            flash(f'Error creating template: {str(e)}', 'error')
            return render_template('admin/report_form.html')
    
    # GET request - show form
    users = User.query.all()
    return render_template('admin/report_form.html', users=users)

@reports_bp.route('/edit/<int:template_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_template(template_id):
    """Edit an existing report template"""
    template = ReportTemplate.query.filter_by(id=template_id, organization_id=current_user.organization_id).first_or_404()
    
    if request.method == 'POST':
        try:
            # Update template
            template.name = request.form.get('name')
            template.description = request.form.get('description')
            template.frequency = ReportFrequencyEnum(request.form.get('frequency'))
            template.template_type = ReportTypeEnum(request.form.get('template_type'))
            template.mailing_list = request.form.get('mailing_list', '[]')
            template.filters = request.form.get('filters', '{}')
            template.active = request.form.get('active') == 'on'
            
            db.session.commit()
            
            flash(f'Report template "{template.name}" updated successfully', 'success')
            return redirect(url_for('reports.list_templates'))
            
        except Exception as e:
            logging.error(f"Error updating report template: {str(e)}")
            flash(f'Error updating template: {str(e)}', 'error')
    
    users = User.query.all()
    return render_template('admin/report_form.html', template=template, users=users)

@reports_bp.route('/delete/<int:template_id>', methods=['POST'])
@login_required
@admin_required
def delete_template(template_id):
    """Delete a report template"""
    try:
        template = ReportTemplate.query.filter_by(id=template_id, organization_id=current_user.organization_id).first_or_404()
        name = template.name
        
        db.session.delete(template)
        db.session.commit()
        
        flash(f'Report template "{name}" deleted successfully', 'success')
        return jsonify({"success": True})
        
    except Exception as e:
        logging.error(f"Error deleting report template: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@reports_bp.route('/preview/<int:template_id>')
@login_required
@admin_required
def preview_template(template_id):
    """Preview a report template"""
    try:
        report_service = ReportService()
        html_content = report_service.preview_report(template_id)
        
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html'
        return response
        
    except Exception as e:
        logging.error(f"Error previewing report: {str(e)}")
        return f"<html><body><h1>Preview Error</h1><p>{str(e)}</p></body></html>"

@reports_bp.route('/run/<int:template_id>', methods=['POST'])
@login_required
@admin_required
def run_template(template_id):
    """Manually run a report template"""
    try:
        result = report_scheduler.run_report_now(template_id)
        
        if result['success']:
            flash(f'Report generated successfully. Emails sent: {result.get("emails_sent", 0)}', 'success')
        else:
            flash(f'Report generation failed: {result.get("error", "Unknown error")}', 'error')
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error running report: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@reports_bp.route('/runs')
@login_required
@admin_required
def list_runs():
    """List recent report runs"""
    runs = ReportRun.query.order_by(ReportRun.run_at.desc()).limit(50).all()
    return render_template('admin/report_runs.html', runs=runs)

@reports_bp.route('/runs/<int:run_id>')
@login_required
@admin_required
def run_details(run_id):
    """Show details of a specific report run"""
    run = ReportRun.query.filter_by(id=run_id, organization_id=current_user.organization_id).first_or_404()
    return render_template('admin/report_run_details.html', run=run)

@reports_bp.route('/api/templates')
@login_required
@admin_required
def api_templates():
    """API endpoint for report templates"""
    templates = ReportTemplate.query.filter_by(organization_id=current_user.organization_id).all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'description': t.description,
        'frequency': t.frequency.value,
        'template_type': t.template_type.value,
        'active': t.active,
        'last_run_at': t.last_run_at.isoformat() if t.last_run_at else None,
        'created_at': t.created_at.isoformat()
    } for t in templates])

@reports_bp.route('/api/runs')
@login_required
@admin_required
def api_runs():
    """API endpoint for report runs"""
    runs = ReportRun.query.order_by(ReportRun.run_at.desc()).limit(20).all()
    return jsonify([{
        'id': r.id,
        'template_name': r.template.name,
        'status': r.status,
        'emails_sent': r.emails_sent,
        'run_at': r.run_at.isoformat(),
        'completed_at': r.completed_at.isoformat() if r.completed_at else None,
        'error_message': r.error_message
    } for r in runs])

def register_reports_blueprint(app):
    """Register reports blueprint with the Flask app"""
    app.register_blueprint(reports_bp)
    logging.info("✓ Reports blueprint registered")