"""
Workflow management routes
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, WorkflowTemplate, WorkflowLibrary, AuditLog, RoleEnum
import logging
from datetime import datetime

workflows_bp = Blueprint('workflows', __name__, url_prefix='/workflows')
logger = logging.getLogger(__name__)


def admin_required(f):
    """Decorator to require admin access"""
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.value not in ['Admin', 'Director', 'CEO']:
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@workflows_bp.route('/')
@login_required
@admin_required
def workflows_index():
    """Display workflows management dashboard"""
    try:
        templates = WorkflowTemplate.query.filter_by(
            organization_id=current_user.organization_id
        ).order_by(WorkflowTemplate.name).all()
        
        library_items = WorkflowLibrary.query.filter_by(
            organization_id=current_user.organization_id
        ).order_by(WorkflowLibrary.name).all()
        
        return render_template('workflows/index.html', 
                             templates=templates,
                             library_items=library_items)
    except Exception as e:
        logger.error(f"Error loading workflows: {e}")
        flash('Unable to load workflows', 'error')
        return redirect(url_for('index'))


@workflows_bp.route('/templates')
@login_required
@admin_required
def templates():
    """Display workflow templates"""
    try:
        templates = WorkflowTemplate.query.filter_by(
            organization_id=current_user.organization_id
        ).order_by(WorkflowTemplate.created_at.desc()).all()
        
        return render_template('workflows/templates.html', templates=templates)
    except Exception as e:
        logger.error(f"Error loading workflow templates: {e}")
        flash('Unable to load templates', 'error')
        return redirect(url_for('workflows.workflows_index'))


@workflows_bp.route('/templates/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_template():
    """Create new workflow template"""
    if request.method == 'GET':
        return render_template('workflows/create_template.html')
    
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        trigger_event = request.form.get('trigger_event', '').strip()
        conditions = request.form.get('conditions', '{}')
        actions = request.form.get('actions', '[]')
        
        # Validation
        if not name or not trigger_event:
            flash('Name and trigger event are required', 'error')
            return render_template('workflows/create_template.html')
        
        # Check for duplicate names
        existing = WorkflowTemplate.query.filter_by(
            name=name,
            organization_id=current_user.organization_id
        ).first()
        
        if existing:
            flash('Template name already exists', 'error')
            return render_template('workflows/create_template.html')
        
        # Create template
        template = WorkflowTemplate(
            name=name,
            description=description,
            trigger_event=trigger_event,
            conditions=conditions,
            actions=actions,
            created_by_id=current_user.id,
            organization_id=current_user.organization_id,
            is_active=True
        )
        
        db.session.add(template)
        db.session.commit()
        
        # Log the creation
        audit_log = AuditLog(
            user_id=current_user.id,
            action='CREATE_WORKFLOW_TEMPLATE',
            details=f'Created workflow template: {name}',
            ip_address=request.remote_addr,
            organization_id=current_user.organization_id
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('Workflow template created successfully', 'success')
        return redirect(url_for('workflows.templates'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating workflow template: {e}")
        flash('Failed to create template', 'error')
        return render_template('workflows/create_template.html')


@workflows_bp.route('/templates/<int:template_id>')
@login_required
@admin_required
def template_detail(template_id):
    """Display workflow template details"""
    try:
        template = WorkflowTemplate.query.filter_by(
            id=template_id,
            organization_id=current_user.organization_id
        ).first()
        
        if not template:
            flash('Template not found', 'error')
            return redirect(url_for('workflows.templates'))
        
        return render_template('workflows/template_detail.html', template=template)
        
    except Exception as e:
        logger.error(f"Error loading template detail: {e}")
        flash('Unable to load template details', 'error')
        return redirect(url_for('workflows.templates'))


@workflows_bp.route('/templates/<int:template_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_template(template_id):
    """Toggle workflow template active status"""
    try:
        template = WorkflowTemplate.query.filter_by(
            id=template_id,
            organization_id=current_user.organization_id
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        template.is_active = not template.is_active
        db.session.commit()
        
        # Log the action
        action = 'ACTIVATE' if template.is_active else 'DEACTIVATE'
        audit_log = AuditLog(
            user_id=current_user.id,
            action=f'{action}_WORKFLOW_TEMPLATE',
            details=f'{action.lower().capitalize()}d workflow template: {template.name}',
            ip_address=request.remote_addr,
            organization_id=current_user.organization_id
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_active': template.is_active,
            'message': f'Template {"activated" if template.is_active else "deactivated"}'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling template: {e}")
        return jsonify({'error': 'Failed to toggle template'}), 500


@workflows_bp.route('/library')
@login_required
@admin_required
def library():
    """Display workflow library"""
    try:
        library_items = WorkflowLibrary.query.filter_by(
            organization_id=current_user.organization_id
        ).order_by(WorkflowLibrary.name).all()
        
        return render_template('workflows/library.html', library_items=library_items)
        
    except Exception as e:
        logger.error(f"Error loading workflow library: {e}")
        flash('Unable to load workflow library', 'error')
        return redirect(url_for('workflows.workflows_index'))


@workflows_bp.route('/api/events')
@login_required
@admin_required
def api_events():
    """API endpoint for workflow events"""
    try:
        # Return available workflow events
        events = [
            'problem_created',
            'problem_updated',
            'business_case_submitted',
            'business_case_approved',
            'business_case_rejected',
            'project_created',
            'project_milestone_due',
            'project_completed',
            'user_assigned',
            'escalation_required'
        ]
        
        return jsonify({'events': events})
        
    except Exception as e:
        logger.error(f"Error loading workflow events: {e}")
        return jsonify({'error': 'Failed to load events'}), 500


@workflows_bp.route('/api/actions')
@login_required
@admin_required
def api_actions():
    """API endpoint for workflow actions"""
    try:
        # Return available workflow actions
        actions = [
            'send_notification',
            'notify_manager',
            'create_task',
            'escalate_to_manager',
            'auto_approve',
            'schedule_follow_up',
            'create_business_case',
            'assign_business_analyst',
            'log_action',
            'notify_stakeholders'
        ]
        
        return jsonify({'actions': actions})
        
    except Exception as e:
        logger.error(f"Error loading workflow actions: {e}")
        return jsonify({'error': 'Failed to load actions'}), 500