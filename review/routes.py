"""
Routes for Epic Collaborative Review System
"""
from datetime import datetime
from flask import request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_

from . import review_bp
from models import db, Epic, EpicComment, User, BusinessCase, BusinessCaseComment, Notification, StatusEnum, Project, ProjectComment, NotificationEventEnum
from auth.session_auth import require_role
from utils.ai_helpers import generate_epic_insights, generate_business_case_insights, generate_project_insights
from utils.ai_review_insights import get_ai_review_insights, get_confidence_badge_class, get_confidence_label


def notify_reviewers_project_submitted(project):
    """Create notifications for reviewers when a project is submitted"""
    # Find all users with reviewing roles (Manager, Director, CEO, PM)
    reviewers = User.query.filter(User.role.in_(['Manager', 'Director', 'CEO', 'PM'])).all()
    
    for reviewer in reviewers:
        notification = Notification(
            user_id=reviewer.id,
            message=f"New Project submitted for review: {project.name}",
            link=url_for('review.project_detail', project_id=project.id),
            event_type=NotificationEventEnum.PROJECT_CREATED,
            read_flag=False
        )
        db.session.add(notification)
    
    db.session.commit()


@review_bp.route('/epics')
@login_required
@require_role('Manager', 'Director', 'CEO', 'BA')
def review_epics():
    """Display list of epics pending review"""
    # Only show submitted epics for review
    epics = Epic.query.filter_by(status='Submitted').order_by(Epic.submitted_at.desc()).all()
    
    return render_template('review/epics.html', epics=epics)


@review_bp.route('/epic/<int:epic_id>')
@login_required  
@require_role('Manager', 'Director', 'CEO', 'BA')
def epic_detail(epic_id):
    """Show detailed view of an epic for review"""
    epic = Epic.query.get_or_404(epic_id)
    
    # Get all comments for this epic, ordered by creation time
    comments = EpicComment.query.filter_by(epic_id=epic_id).order_by(EpicComment.created_at.asc()).all()
    
    # Generate AI reviewer insights (existing system)
    ai_insights = generate_epic_insights(epic)
    
    # Generate enhanced AI review insights with confidence scoring
    enhanced_ai_insights = get_ai_review_insights(
        content_type="epic",
        title=epic.title,
        description=epic.description or "No description provided",
        additional_context=f"Status: {epic.status}, Business Case: {epic.case_id if epic.case_id else 'No linked case'}"
    )
    
    return render_template('review/epic_detail.html', 
                         epic=epic, 
                         comments=comments, 
                         ai_insights=ai_insights,
                         enhanced_ai_insights=enhanced_ai_insights,
                         get_confidence_badge_class=get_confidence_badge_class,
                         get_confidence_label=get_confidence_label)


@review_bp.route('/epic/<int:epic_id>/action', methods=['POST'])
@login_required
@require_role('Manager', 'Director', 'CEO', 'BA')
def handle_epic_action(epic_id):
    """Handle epic approval or rejection actions"""
    epic = Epic.query.get_or_404(epic_id)
    
    comment_text = request.form.get('comment', '').strip()
    action = request.form.get('action')
    
    # Add comment if provided
    if comment_text:
        comment = EpicComment(
            epic_id=epic.id,
            author_id=current_user.id,
            content=comment_text,
            created_at=datetime.utcnow()
        )
        db.session.add(comment)
    
    # Handle action
    if action == 'approve':
        epic.status = 'Approved'
        epic.approved_by = current_user.id
        epic.approved_at = datetime.utcnow()
        flash_message = f'Epic "{epic.title}" has been approved.'
        notification_message = f'Your epic "{epic.title}" has been approved by {current_user.name}.'
        
    elif action == 'reject':
        epic.status = 'Rejected'
        epic.approved_by = current_user.id
        epic.approved_at = datetime.utcnow()
        flash_message = f'Epic "{epic.title}" has been rejected.'
        notification_message = f'Your epic "{epic.title}" has been rejected by {current_user.name}.'
        
    elif action == 'send_back':
        epic.status = 'Draft'
        epic.submitted_by = None
        epic.submitted_at = None
        epic.approved_by = None
        epic.approved_at = None
        flash_message = f'Epic "{epic.title}" has been sent back to draft status.'
        notification_message = f'Your epic "{epic.title}" has been sent back to draft by {current_user.name}.'
        
    elif action == 'request_changes':
        epic.status = 'Changes Requested'
        flash_message = f'Changes have been requested for epic "{epic.title}".'
        notification_message = f'Changes have been requested for your epic "{epic.title}" by {current_user.name}.'
    
    else:
        flash('Invalid action specified.', 'error')
        return redirect(url_for('review.epic_detail', epic_id=epic_id))
    
    # Create notification for epic creator
    if epic.creator_id != current_user.id:
        notification = Notification(
            user_id=epic.creator_id,
            type='epic_review',
            title='Epic Review Update',
            message=notification_message,
            created_at=datetime.utcnow(),
            is_read=False
        )
        db.session.add(notification)
    
    db.session.commit()
    flash(flash_message, 'success')
    
    return redirect(url_for('review.review_epics'))


@review_bp.route('/epic/<int:epic_id>/comment', methods=['POST'])
@login_required
@require_role('Manager', 'Director', 'CEO', 'BA', 'Staff', 'PM')
def add_comment(epic_id):
    """Add a comment to an epic"""
    epic = Epic.query.get_or_404(epic_id)
    
    comment_text = request.form.get('comment', '').strip()
    if not comment_text:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('review.epic_detail', epic_id=epic_id))
    
    comment = EpicComment(
        epic_id=epic.id,
        author_id=current_user.id,
        content=comment_text,
        created_at=datetime.utcnow()
    )
    
    db.session.add(comment)
    
    # Create notification for epic creator if they're not the commenter
    if epic.creator_id != current_user.id:
        notification = Notification(
            user_id=epic.creator_id,
            type='epic_comment',
            title='New Epic Comment',
            message=f'{current_user.name} commented on your epic "{epic.title}".',
            created_at=datetime.utcnow(),
            is_read=False
        )
        db.session.add(notification)
    
    db.session.commit()
    flash('Comment added successfully.', 'success')
    
    return redirect(url_for('review.epic_detail', epic_id=epic_id))


@review_bp.route('/my-submissions')
@login_required
def my_submissions():
    """Show user's submitted epics and their review status"""
    epics = Epic.query.filter_by(creator_id=current_user.id).filter(
        Epic.status.in_(['Submitted', 'Approved', 'Rejected', 'Changes Requested'])
    ).order_by(Epic.submitted_at.desc()).all()
    
    return render_template('review/my_submissions.html', epics=epics)


@review_bp.route('/submit-epic/<int:epic_id>', methods=['POST'])
@login_required
def submit_epic(epic_id):
    """Submit an epic for review"""
    epic = Epic.query.get_or_404(epic_id)
    
    # Check if user owns the epic or has permission
    if epic.creator_id != current_user.id and current_user.role.value not in ['Admin', 'Manager', 'Director', 'CEO']:
        flash('You do not have permission to submit this epic.', 'error')
        return redirect(url_for('business.case_detail', case_id=epic.case_id))
    
    # Only allow submission if epic is in Draft or Changes Requested status
    if epic.status not in ['Draft', 'Changes Requested']:
        flash(f'Epic cannot be submitted. Current status: {epic.status}', 'error')
        return redirect(url_for('business.case_detail', case_id=epic.case_id))
    
    epic.status = 'Submitted'
    epic.submitted_by = current_user.id
    epic.submitted_at = datetime.utcnow()
    
    db.session.commit()
    flash(f'Epic "{epic.title}" has been submitted for review.', 'success')
    
    return redirect(url_for('business.case_detail', case_id=epic.case_id))


@review_bp.route('/api/epic-stats')
@login_required
@require_role('Manager', 'Director', 'CEO', 'BA')
def epic_review_stats():
    """API endpoint for epic review statistics"""
    stats = {
        'pending_review': Epic.query.filter_by(status='Submitted').count(),
        'approved_today': Epic.query.filter(
            Epic.status == 'Approved',
            Epic.approved_at >= datetime.utcnow().date()
        ).count(),
        'total_reviewed': Epic.query.filter(
            Epic.status.in_(['Approved', 'Rejected'])
        ).count(),
        'changes_requested': Epic.query.filter_by(status='Changes Requested').count()
    }
    
    return jsonify(stats)


# Business Case Review Routes
@review_bp.route('/business-cases')
@login_required
@require_role('Director', 'CEO', 'Admin')
def review_business_cases():
    """Show submitted business cases for Director review"""
    # Filter for submitted business cases (status 'Submitted')
    cases = BusinessCase.query.filter_by(status=StatusEnum.Submitted).order_by(BusinessCase.submitted_at.desc()).all()
    return render_template('review/business_cases.html', cases=cases)


@review_bp.route('/business-case/<int:case_id>')
@login_required
@require_role('Director', 'CEO', 'Admin')
def business_case_detail(case_id):
    """Show detailed view of a business case for review"""
    case = BusinessCase.query.get_or_404(case_id)
    comments = BusinessCaseComment.query.filter_by(case_id=case_id).order_by(BusinessCaseComment.created_at.desc()).all()
    
    # Generate AI reviewer insights (existing system)
    ai_insights = generate_business_case_insights(case)
    
    # Generate enhanced AI review insights with confidence scoring
    enhanced_ai_insights = get_ai_review_insights(
        content_type="business case",
        title=case.title,
        description=case.description or "No description provided",
        cost=case.estimated_cost,
        benefit=case.expected_benefit,
        additional_context=f"Status: {case.status}, ROI: {case.roi if case.roi else 'Not calculated'}"
    )
    
    return render_template('review/business_case_detail.html', 
                         case=case, 
                         comments=comments, 
                         ai_insights=ai_insights,
                         enhanced_ai_insights=enhanced_ai_insights,
                         get_confidence_badge_class=get_confidence_badge_class,
                         get_confidence_label=get_confidence_label)


@review_bp.route('/business-case/<int:case_id>/action', methods=['POST'])
@login_required
@require_role('Director', 'CEO', 'Admin')
def handle_business_case_action(case_id):
    """Handle business case approval or rejection actions"""
    case = BusinessCase.query.get_or_404(case_id)
    
    comment_text = request.form.get('comment', '').strip()
    action = request.form.get('action')
    
    # Add comment if provided
    if comment_text:
        comment = BusinessCaseComment(
            case_id=case.id,
            author_id=current_user.id,
            content=comment_text
        )
        db.session.add(comment)
    
    # Handle the action
    if action == 'approve':
        case.status = StatusEnum.Approved
        case.approved_by = current_user.id
        case.approved_at = datetime.utcnow()
        
        # Create notification for case creator
        notification = Notification(
            user_id=case.created_by,
            message=f'Your Business Case "{case.title}" has been approved by {current_user.first_name} {current_user.last_name}.',
            link=url_for('business.view_case', id=case.id),
            event_type='BUSINESS_CASE_APPROVED'
        )
        db.session.add(notification)
        
        flash(f'Business Case "{case.title}" has been approved.', 'success')
        
    elif action == 'send_back':
        case.status = StatusEnum.Open  # Send back to Draft status
        case.approved_by = None
        case.approved_at = None
        
        # Create notification for case creator
        notification = Notification(
            user_id=case.created_by,
            message=f'Your Business Case "{case.title}" has been sent back for revisions by {current_user.first_name} {current_user.last_name}.',
            link=url_for('business.view_case', id=case.id),
            event_type='BUSINESS_CASE_CREATED'
        )
        db.session.add(notification)
        
        flash(f'Business Case "{case.title}" has been sent back for revisions.', 'warning')
    
    db.session.commit()
    
    return redirect(url_for('review.review_business_cases'))


@review_bp.route('/business-case/<int:case_id>/comment', methods=['POST'])
@login_required
@require_role('Director', 'CEO', 'Manager', 'BA', 'Staff', 'PM')
def add_business_case_comment(case_id):
    """Add a comment to a business case"""
    case = BusinessCase.query.get_or_404(case_id)
    
    comment_text = request.form.get('comment', '').strip()
    if not comment_text:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('review.business_case_detail', case_id=case_id))
    
    comment = BusinessCaseComment(
        case_id=case.id,
        author_id=current_user.id,
        content=comment_text
    )
    db.session.add(comment)
    
    # Create notification for case creator (if not the commenter)
    if case.created_by != current_user.id:
        notification = Notification(
            user_id=case.created_by,
            message=f'{current_user.first_name} {current_user.last_name} commented on Business Case "{case.title}".',
            link=url_for('review.business_case_detail', case_id=case.id)
        )
        db.session.add(notification)
    
    db.session.commit()
    flash('Comment added successfully.', 'success')
    
    return redirect(url_for('review.business_case_detail', case_id=case_id))


# Project Review Routes
@review_bp.route('/projects')
@login_required
@require_role('Manager', 'Director', 'CEO', 'PM', 'Admin')
def review_projects():
    """Show submitted projects for Manager/Director review"""
    # Filter for submitted projects (status 'Submitted')
    projects = Project.query.filter_by(status=StatusEnum.Submitted).order_by(Project.submitted_at.desc()).all()
    return render_template('review/projects.html', projects=projects)


@review_bp.route('/project/<int:project_id>')
@login_required
@require_role('Manager', 'Director', 'CEO', 'PM', 'Admin')
def project_detail(project_id):
    """Show detailed view of a project for review"""
    project = Project.query.get_or_404(project_id)
    
    # Get related comments for the project
    comments = ProjectComment.query.filter_by(project_id=project_id).order_by(ProjectComment.created_at.desc()).all()
    
    # Generate AI reviewer insights (existing system)
    ai_insights = generate_project_insights(project)
    
    # Generate enhanced AI review insights with confidence scoring
    enhanced_ai_insights = get_ai_review_insights(
        content_type="project",
        title=project.name,
        description=project.description or "No description provided",
        cost=project.budget,
        additional_context=f"Status: {project.status}, Timeline: {project.end_date if project.end_date else 'Not specified'}"
    )
    
    return render_template('review/project_detail.html', 
                         project=project, 
                         comments=comments, 
                         ai_insights=ai_insights,
                         enhanced_ai_insights=enhanced_ai_insights,
                         get_confidence_badge_class=get_confidence_badge_class,
                         get_confidence_label=get_confidence_label)


@review_bp.route('/project/<int:project_id>/action', methods=['POST'])
@login_required
@require_role('Manager', 'Director', 'CEO', 'PM', 'Admin')
def handle_project_action(project_id):
    """Handle project approval or rejection actions"""
    project = Project.query.get_or_404(project_id)
    comment_text = request.form.get('comment', '').strip()
    action = request.form.get('action')
    
    # Add comment if provided
    if comment_text:
        comment = ProjectComment(
            project_id=project.id,
            author_id=current_user.id,
            content=comment_text
        )
        db.session.add(comment)
    
    # Handle action
    if action == 'approve':
        project.status = StatusEnum.Approved
        project.approved_by = current_user.id
        project.approved_at = datetime.utcnow()
        
        # Create notification for project manager and submitter
        notification = Notification(
            user_id=project.project_manager_id,
            message=f'Project "{project.name}" has been approved by {current_user.name}.',
            link=f'/projects/{project.id}',
            event_type=NotificationEventEnum.PROJECT_APPROVED
        )
        db.session.add(notification)
        
        # Also notify submitter if different from project manager
        if project.submitted_by and project.submitted_by != project.project_manager_id:
            submitter_notification = Notification(
                user_id=project.submitted_by,
                message=f'Your submitted project "{project.name}" has been approved.',
                link=f'/projects/{project.id}',
                event_type=NotificationEventEnum.PROJECT_APPROVED
            )
            db.session.add(submitter_notification)
        
        flash(f'Project "{project.name}" has been approved.', 'success')
        
    elif action == 'send_back':
        project.status = StatusEnum.Open  # Reset to Draft/Open status
        project.approved_by = None
        project.approved_at = None
        
        # Create notification for project manager and submitter
        notification = Notification(
            user_id=project.project_manager_id,
            message=f'Project "{project.name}" has been sent back for revisions by {current_user.name}.',
            link=f'/projects/{project.id}',
            event_type=NotificationEventEnum.PROJECT_NEEDS_REVISION
        )
        db.session.add(notification)
        
        # Also notify submitter if different from project manager
        if project.submitted_by and project.submitted_by != project.project_manager_id:
            submitter_notification = Notification(
                user_id=project.submitted_by,
                message=f'Your submitted project "{project.name}" needs revisions.',
                link=f'/projects/{project.id}',
                event_type=NotificationEventEnum.PROJECT_NEEDS_REVISION
            )
            db.session.add(submitter_notification)
        
        flash(f'Project "{project.name}" has been sent back for revisions.', 'success')
    
    db.session.commit()
    return redirect(url_for('review.review_projects'))


@review_bp.route('/summary')
@login_required
@require_role('Manager', 'Director', 'CEO', 'PM', 'Admin')
def review_summary():
    """Comprehensive review dashboard showing all submitted items in one place"""
    # Get all pending items for review
    epics = Epic.query.filter_by(status='Submitted').order_by(Epic.submitted_at.desc()).all()
    cases = BusinessCase.query.filter_by(status=StatusEnum.Submitted).order_by(BusinessCase.submitted_at.desc()).all()
    projects = Project.query.filter_by(status=StatusEnum.Submitted).order_by(Project.submitted_at.desc()).all()
    
    # Calculate summary statistics
    total_pending = len(epics) + len(cases) + len(projects)
    
    return render_template('review/summary.html', 
                         epics=epics, 
                         cases=cases, 
                         projects=projects,
                         total_pending=total_pending)