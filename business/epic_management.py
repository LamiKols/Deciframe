"""
Epic and Story Management Module
Handles CRUD operations for epics and stories with BA role restrictions
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from stateless_auth import require_auth, get_current_user
from models import BusinessCase, Epic, Story, RoleEnum
from app import db
import json
import logging

epic_bp = Blueprint('epics', __name__, url_prefix='/epics')

def is_business_analyst(user):
    """Check if user has Business Analyst role"""
    return user and user.role == RoleEnum.BA

@epic_bp.route('/case/<int:case_id>')
@require_auth
def view_epics(case_id):
    """View epics for a business case"""
    user = get_current_user()
    business_case = BusinessCase.query.get_or_404(case_id)
    
    # Check if user can view this case
    if not user:
        flash('Authentication required', 'error')
        return redirect(url_for('auth.login'))
    
    epics = Epic.query.filter_by(case_id=case_id).order_by(Epic.created_at).all()
    
    return render_template('epics/view_epics.html', 
                         business_case=business_case, 
                         epics=epics,
                         is_ba=is_business_analyst(user))

@epic_bp.route('/edit/<int:epic_id>', methods=['GET', 'POST'])
@require_auth
def edit_epic(epic_id):
    """Edit an epic (BA only)"""
    user = get_current_user()
    if not is_business_analyst(user):
        flash('Only Business Analysts can edit epics', 'error')
        return redirect(request.referrer or url_for('index'))
    
    epic = Epic.query.get_or_404(epic_id)
    
    if request.method == 'POST':
        try:
            epic.title = request.form.get('title', '').strip()
            epic.description = request.form.get('description', '').strip()
            
            if not epic.title or not epic.description:
                flash('Title and description are required', 'error')
                return render_template('epics/edit_epic.html', epic=epic)
            
            db.session.commit()
            flash('Epic updated successfully', 'success')
            return redirect(url_for('epics.view_epics', case_id=epic.case_id))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating epic {epic_id}: {e}")
            flash('Error updating epic', 'error')
    
    return render_template('epics/edit_epic.html', epic=epic)

@epic_bp.route('/story/edit/<int:story_id>', methods=['GET', 'POST'])
@require_auth
def edit_story(story_id):
    """Edit a story (BA only)"""
    user = get_current_user()
    if not is_business_analyst(user):
        flash('Only Business Analysts can edit stories', 'error')
        return redirect(request.referrer or url_for('index'))
    
    story = Story.query.get_or_404(story_id)
    
    if request.method == 'POST':
        try:
            story.title = request.form.get('title', '').strip()
            story.description = request.form.get('description', '').strip()
            story.priority = request.form.get('priority', 'Medium')
            story.effort_estimate = request.form.get('effort_estimate', '').strip()
            
            # Handle acceptance criteria
            criteria_input = request.form.get('acceptance_criteria', '').strip()
            if criteria_input:
                # Split by newlines and filter empty lines
                criteria_list = [line.strip() for line in criteria_input.split('\n') if line.strip()]
                story.acceptance_criteria = json.dumps(criteria_list)
            else:
                story.acceptance_criteria = json.dumps([])
            
            if not story.title or not story.description:
                flash('Title and description are required', 'error')
                return render_template('epics/edit_story.html', story=story)
            
            db.session.commit()
            flash('Story updated successfully', 'success')
            return redirect(url_for('epics.view_epics', case_id=story.epic.case_id))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating story {story_id}: {e}")
            flash('Error updating story', 'error')
    
    # Prepare acceptance criteria for form
    try:
        criteria_list = json.loads(story.acceptance_criteria) if story.acceptance_criteria else []
        criteria_text = '\n'.join(criteria_list)
    except:
        criteria_text = story.acceptance_criteria or ''
    
    return render_template('epics/edit_story.html', story=story, criteria_text=criteria_text)

@epic_bp.route('/delete/<int:epic_id>', methods=['POST'])
@require_auth
def delete_epic(epic_id):
    """Delete an epic (BA only)"""
    user = get_current_user()
    if not is_business_analyst(user):
        return jsonify({'success': False, 'error': 'Only Business Analysts can delete epics'}), 403
    
    try:
        epic = Epic.query.get_or_404(epic_id)
        case_id = epic.case_id
        
        db.session.delete(epic)
        db.session.commit()
        
        flash('Epic deleted successfully', 'success')
        return jsonify({'success': True, 'redirect': url_for('epics.view_epics', case_id=case_id)})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting epic {epic_id}: {e}")
        return jsonify({'success': False, 'error': 'Error deleting epic'}), 500

@epic_bp.route('/story/delete/<int:story_id>', methods=['POST'])
@require_auth
def delete_story(story_id):
    """Delete a story (BA only)"""
    user = get_current_user()
    if not is_business_analyst(user):
        return jsonify({'success': False, 'error': 'Only Business Analysts can delete stories'}), 403
    
    try:
        story = Story.query.get_or_404(story_id)
        case_id = story.epic.case_id
        
        db.session.delete(story)
        db.session.commit()
        
        flash('Story deleted successfully', 'success')
        return jsonify({'success': True, 'redirect': url_for('epics.view_epics', case_id=case_id)})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting story {story_id}: {e}")
        return jsonify({'success': False, 'error': 'Error deleting story'}), 500