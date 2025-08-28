"""
Epic Management Routes
Handles epic and user story management
"""

from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

from . import epics_bp
from models import db, Epic, Story, BusinessCase, Project


@epics_bp.route('/')
@login_required
def view_epics():
    """View all epics for current organization"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    epics_query = Epic.query.filter_by(
        organization_id=current_user.organization_id
    ).order_by(Epic.created_at.desc())
    
    epics = epics_query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return render_template('epics/view_epics.html', epics=epics)


@epics_bp.route('/create')
@login_required
def create_epic():
    """Create new epic form"""
    business_cases = BusinessCase.query.filter_by(
        organization_id=current_user.organization_id,
        status='approved'
    ).all()
    
    return render_template('epics/create_epic.html', business_cases=business_cases)


@epics_bp.route('/create', methods=['POST'])
@login_required
def create_epic_post():
    """Handle epic creation"""
    title = request.form.get('title')
    description = request.form.get('description')
    business_case_id = request.form.get('business_case_id')
    
    if not title:
        flash('Epic title is required', 'error')
        return redirect(url_for('epics.create_epic'))
    
    epic = Epic(
        title=title,
        description=description,
        business_case_id=business_case_id if business_case_id else None,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        status='draft',
        created_at=datetime.utcnow()
    )
    
    db.session.add(epic)
    db.session.commit()
    
    flash(f'Epic "{title}" created successfully', 'success')
    return redirect(url_for('epics.view_epics'))


@epics_bp.route('/edit/<int:epic_id>')
@login_required
def edit_epic(epic_id):
    """Edit epic form"""
    epic = Epic.query.filter_by(
        id=epic_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    business_cases = BusinessCase.query.filter_by(
        organization_id=current_user.organization_id,
        status='approved'
    ).all()
    
    return render_template('epics/edit_epic.html', epic=epic, business_cases=business_cases)


@epics_bp.route('/edit/<int:epic_id>', methods=['POST'])
@login_required
def edit_epic_post(epic_id):
    """Handle epic editing"""
    epic = Epic.query.filter_by(
        id=epic_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    epic.title = request.form.get('title', epic.title)
    epic.description = request.form.get('description', epic.description)
    epic.business_case_id = request.form.get('business_case_id') or None
    epic.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Epic "{epic.title}" updated successfully', 'success')
    return redirect(url_for('epics.view_epics'))


@epics_bp.route('/stories/<int:epic_id>')
@login_required
def view_stories(epic_id):
    """View stories for an epic"""
    epic = Epic.query.filter_by(
        id=epic_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    stories = Story.query.filter_by(epic_id=epic_id).all()
    
    return render_template('epics/view_stories.html', epic=epic, stories=stories)


@epics_bp.route('/story/edit/<int:story_id>')
@login_required
def edit_story(story_id):
    """Edit user story form"""
    story = Story.query.filter_by(
        id=story_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    return render_template('epics/edit_story.html', story=story)


@epics_bp.route('/story/edit/<int:story_id>', methods=['POST'])
@login_required
def edit_story_post(story_id):
    """Handle story editing"""
    story = Story.query.filter_by(
        id=story_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    story.title = request.form.get('title', story.title)
    story.description = request.form.get('description', story.description)
    story.acceptance_criteria = request.form.get('acceptance_criteria', story.acceptance_criteria)
    story.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Story "{story.title}" updated successfully', 'success')
    return redirect(url_for('epics.view_stories', epic_id=story.epic_id))


@epics_bp.route('/delete/<int:epic_id>', methods=['POST'])
@login_required
def delete_epic(epic_id):
    """Delete epic"""
    epic = Epic.query.filter_by(
        id=epic_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    epic_title = epic.title
    db.session.delete(epic)
    db.session.commit()
    
    flash(f'Epic "{epic_title}" deleted', 'warning')
    return redirect(url_for('epics.view_epics'))