"""
Additional problem management routes
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Problem, User, AuditLog
import logging

logger = logging.getLogger(__name__)


def init_additional_problem_routes(app):
    """Initialize additional problem routes on the Flask app"""
    
    @app.route('/problems/<int:problem_id>/detail')
    @app.route('/problems/problem_detail/<int:problem_id>')
    @login_required
    def problem_detail(problem_id):
        """Display detailed problem view (unified endpoint)"""
        try:
            problem = Problem.query.filter_by(
                id=problem_id,
                organization_id=current_user.organization_id
            ).first()
            
            if not problem:
                flash('Problem not found', 'error')
                return redirect(url_for('problems.index'))
            
            return render_template('problems/detail.html', problem=problem)
            
        except Exception as e:
            logger.error(f"Error loading problem detail: {e}")
            flash('Unable to load problem details', 'error')
            return redirect(url_for('problems.index'))
    
    @app.route('/problems/<int:problem_id>/assign', methods=['POST'])
    @login_required
    def assign_problem(problem_id):
        """Assign problem to a user"""
        try:
            problem = Problem.query.filter_by(
                id=problem_id,
                organization_id=current_user.organization_id
            ).first()
            
            if not problem:
                return jsonify({'error': 'Problem not found'}), 404
            
            # Check permission to assign
            if current_user.role.value not in ['Admin', 'Director', 'Manager']:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            user_id = request.json.get('user_id')
            if not user_id:
                return jsonify({'error': 'User ID required'}), 400
            
            # Verify user exists and is in same organization
            user = User.query.filter_by(
                id=user_id,
                organization_id=current_user.organization_id
            ).first()
            
            if not user:
                return jsonify({'error': 'Invalid user'}), 400
            
            # Update assignment
            old_assignee = problem.assigned_to.name if problem.assigned_to else 'Unassigned'
            problem.assigned_to_id = user_id
            db.session.commit()
            
            # Log the assignment
            audit_log = AuditLog(
                user_id=current_user.id,
                action='ASSIGN_PROBLEM',
                details=f'Assigned problem {problem.code or problem.id} from {old_assignee} to {user.name}',
                ip_address=request.remote_addr,
                organization_id=current_user.organization_id
            )
            db.session.add(audit_log)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Problem assigned to {user.name}',
                'assigned_to': user.name
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error assigning problem: {e}")
            return jsonify({'error': 'Failed to assign problem'}), 500
    
    @app.route('/problems/<int:problem_id>/status', methods=['POST'])
    @login_required
    def update_problem_status(problem_id):
        """Update problem status"""
        try:
            problem = Problem.query.filter_by(
                id=problem_id,
                organization_id=current_user.organization_id
            ).first()
            
            if not problem:
                return jsonify({'error': 'Problem not found'}), 404
            
            # Check permission to update status
            if (current_user.id != problem.assigned_to_id and 
                current_user.role.value not in ['Admin', 'Director', 'Manager']):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            new_status = request.json.get('status')
            if not new_status:
                return jsonify({'error': 'Status required'}), 400
            
            # Validate status
            valid_statuses = ['Open', 'In_Progress', 'Resolved', 'Closed']
            if new_status not in valid_statuses:
                return jsonify({'error': 'Invalid status'}), 400
            
            old_status = problem.status.value if problem.status else 'Unknown'
            problem.status = new_status
            db.session.commit()
            
            # Log the status change
            audit_log = AuditLog(
                user_id=current_user.id,
                action='UPDATE_PROBLEM_STATUS',
                details=f'Changed problem {problem.code or problem.id} status from {old_status} to {new_status}',
                ip_address=request.remote_addr,
                organization_id=current_user.organization_id
            )
            db.session.add(audit_log)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Status updated to {new_status}',
                'status': new_status
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating problem status: {e}")
            return jsonify({'error': 'Failed to update status'}), 500
    
    @app.route('/problems/classify/<int:problem_id>', methods=['GET', 'POST'])
    @login_required
    def classify_problem(problem_id):
        """Classify problem using AI assistance"""
        try:
            problem = Problem.query.filter_by(
                id=problem_id,
                organization_id=current_user.organization_id
            ).first()
            
            if not problem:
                flash('Problem not found', 'error')
                return redirect(url_for('problems.index'))
            
            if request.method == 'GET':
                return render_template('problems/classify.html', problem=problem)
            
            # Handle classification update
            classification = request.form.get('classification', '').strip()
            confidence = request.form.get('confidence', 0.0)
            
            try:
                confidence = float(confidence)
            except (ValueError, TypeError):
                confidence = 0.0
            
            # Update problem classification
            problem.classification = classification
            problem.classification_confidence = confidence
            db.session.commit()
            
            # Log the classification
            audit_log = AuditLog(
                user_id=current_user.id,
                action='CLASSIFY_PROBLEM',
                details=f'Classified problem {problem.code or problem.id} as {classification} (confidence: {confidence}%)',
                ip_address=request.remote_addr,
                organization_id=current_user.organization_id
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Problem classified successfully', 'success')
            return redirect(url_for('problems.problem_detail', problem_id=problem.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error classifying problem: {e}")
            flash('Failed to classify problem', 'error')
            return redirect(url_for('problems.index'))