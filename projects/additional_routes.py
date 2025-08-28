"""
Additional project management routes
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Project, ProjectMilestone, User, AuditLog
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


def init_additional_project_routes(app):
    """Initialize additional project routes on the Flask app"""
    
    @app.route('/projects/<int:project_id>/detail')
    @app.route('/projects/project_detail/<int:project_id>')
    @login_required
    def project_detail(project_id):
        """Display detailed project view (unified endpoint)"""
        try:
            project = Project.query.filter_by(
                id=project_id,
                organization_id=current_user.organization_id
            ).first()
            
            if not project:
                flash('Project not found', 'error')
                return redirect(url_for('projects.index'))
            
            # Get project milestones
            milestones = ProjectMilestone.query.filter_by(
                project_id=project.id
            ).order_by(ProjectMilestone.due_date).all()
            
            return render_template('projects/detail.html', 
                                 project=project, 
                                 milestones=milestones)
            
        except Exception as e:
            logger.error(f"Error loading project detail: {e}")
            flash('Unable to load project details', 'error')
            return redirect(url_for('projects.index'))
    
    @app.route('/projects/milestones')
    @app.route('/projects/milestones_list')
    @login_required
    def milestones_list():
        """Display project milestones list"""
        try:
            # Get user's accessible projects
            if current_user.role.value in ['Admin', 'CEO']:
                projects = Project.query.filter_by(
                    organization_id=current_user.organization_id
                ).all()
            elif current_user.role.value == 'Director':
                projects = Project.query.filter_by(
                    organization_id=current_user.organization_id,
                    department_id=current_user.department_id
                ).all()
            else:
                projects = Project.query.filter(
                    Project.organization_id == current_user.organization_id,
                    (Project.project_manager_id == current_user.id) | 
                    (Project.created_by_id == current_user.id)
                ).all()
            
            # Get all milestones for accessible projects
            project_ids = [p.id for p in projects]
            milestones = ProjectMilestone.query.filter(
                ProjectMilestone.project_id.in_(project_ids)
            ).order_by(ProjectMilestone.due_date).all() if project_ids else []
            
            return render_template('projects/milestones.html', 
                                 milestones=milestones,
                                 projects=projects)
            
        except Exception as e:
            logger.error(f"Error loading milestones: {e}")
            flash('Unable to load milestones', 'error')
            return redirect(url_for('projects.index'))
    
    @app.route('/projects/<int:project_id>/milestones/new', methods=['GET', 'POST'])
    @login_required
    def new_milestone(project_id):
        """Create new project milestone"""
        try:
            project = Project.query.filter_by(
                id=project_id,
                organization_id=current_user.organization_id
            ).first()
            
            if not project:
                flash('Project not found', 'error')
                return redirect(url_for('projects.index'))
            
            # Check permission
            if (current_user.id not in [project.project_manager_id, project.created_by_id] and 
                current_user.role.value not in ['Admin', 'Director']):
                flash('Insufficient permissions to create milestones', 'error')
                return redirect(url_for('projects.project_detail', project_id=project.id))
            
            if request.method == 'GET':
                return render_template('projects/new_milestone.html', project=project)
            
            # Handle milestone creation
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            due_date_str = request.form.get('due_date', '').strip()
            owner_id = request.form.get('owner_id')
            
            # Validation
            if not name or not due_date_str:
                flash('Name and due date are required', 'error')
                return render_template('projects/new_milestone.html', project=project)
            
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid due date format', 'error')
                return render_template('projects/new_milestone.html', project=project)
            
            # Validate owner if provided
            if owner_id:
                owner = User.query.filter_by(
                    id=owner_id,
                    organization_id=current_user.organization_id
                ).first()
                if not owner:
                    flash('Invalid milestone owner', 'error')
                    return render_template('projects/new_milestone.html', project=project)
            
            # Create milestone
            milestone = ProjectMilestone(
                name=name,
                description=description,
                due_date=due_date,
                project_id=project.id,
                owner_id=owner_id,
                created_by_id=current_user.id,
                completed=False
            )
            
            db.session.add(milestone)
            db.session.commit()
            
            # Log the creation
            audit_log = AuditLog(
                user_id=current_user.id,
                action='CREATE_MILESTONE',
                details=f'Created milestone "{name}" for project {project.name}',
                ip_address=request.remote_addr,
                organization_id=current_user.organization_id
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Milestone created successfully', 'success')
            return redirect(url_for('projects.project_detail', project_id=project.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating milestone: {e}")
            flash('Failed to create milestone', 'error')
            return redirect(url_for('projects.project_detail', project_id=project_id))
    
    @app.route('/projects/milestones/<int:milestone_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_milestone(milestone_id):
        """Edit project milestone"""
        try:
            milestone = ProjectMilestone.query.join(Project).filter(
                ProjectMilestone.id == milestone_id,
                Project.organization_id == current_user.organization_id
            ).first()
            
            if not milestone:
                flash('Milestone not found', 'error')
                return redirect(url_for('projects.milestones_list'))
            
            # Check permission
            project = milestone.project
            if (current_user.id not in [project.project_manager_id, project.created_by_id, milestone.owner_id] and 
                current_user.role.value not in ['Admin', 'Director']):
                flash('Insufficient permissions to edit milestone', 'error')
                return redirect(url_for('projects.project_detail', project_id=project.id))
            
            if request.method == 'GET':
                return render_template('projects/edit_milestone.html', 
                                     milestone=milestone, 
                                     project=project)
            
            # Handle milestone update
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            due_date_str = request.form.get('due_date', '').strip()
            completed = request.form.get('completed') == 'on'
            
            # Validation
            if not name or not due_date_str:
                flash('Name and due date are required', 'error')
                return render_template('projects/edit_milestone.html', 
                                     milestone=milestone, 
                                     project=project)
            
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid due date format', 'error')
                return render_template('projects/edit_milestone.html', 
                                     milestone=milestone, 
                                     project=project)
            
            # Update milestone
            milestone.name = name
            milestone.description = description
            milestone.due_date = due_date
            
            # Handle completion status
            if completed and not milestone.completed:
                milestone.completed = True
                milestone.completion_date = date.today()
            elif not completed and milestone.completed:
                milestone.completed = False
                milestone.completion_date = None
            
            db.session.commit()
            
            # Log the update
            audit_log = AuditLog(
                user_id=current_user.id,
                action='UPDATE_MILESTONE',
                details=f'Updated milestone "{name}" for project {project.name}',
                ip_address=request.remote_addr,
                organization_id=current_user.organization_id
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Milestone updated successfully', 'success')
            return redirect(url_for('projects.project_detail', project_id=project.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating milestone: {e}")
            flash('Failed to update milestone', 'error')
            return redirect(url_for('projects.milestones_list'))
    
    @app.route('/projects/milestones/<int:milestone_id>/delete', methods=['POST'])
    @login_required
    def delete_milestone(milestone_id):
        """Delete project milestone"""
        try:
            milestone = ProjectMilestone.query.join(Project).filter(
                ProjectMilestone.id == milestone_id,
                Project.organization_id == current_user.organization_id
            ).first()
            
            if not milestone:
                return jsonify({'error': 'Milestone not found'}), 404
            
            # Check permission
            project = milestone.project
            if (current_user.id not in [project.project_manager_id, project.created_by_id] and 
                current_user.role.value not in ['Admin', 'Director']):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            milestone_name = milestone.name
            project_name = project.name
            
            db.session.delete(milestone)
            db.session.commit()
            
            # Log the deletion
            audit_log = AuditLog(
                user_id=current_user.id,
                action='DELETE_MILESTONE',
                details=f'Deleted milestone "{milestone_name}" from project {project_name}',
                ip_address=request.remote_addr,
                organization_id=current_user.organization_id
            )
            db.session.add(audit_log)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Milestone "{milestone_name}" deleted successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting milestone: {e}")
            return jsonify({'error': 'Failed to delete milestone'}), 500