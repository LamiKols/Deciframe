from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask.helpers import url_for
from flask_login import login_required, current_user
from sqlalchemy import and_
from datetime import datetime, date
from app import db
from models import Project, ProjectMilestone, Department, StatusEnum, PriorityEnum, Epic
from projects.forms import ProjectForm, MilestoneForm, ProjectFilterForm


projects_bp = Blueprint('projects', __name__, url_prefix='/projects')


@projects_bp.route('/')
@login_required
def index():
    """List all projects with filtering"""
    user = current_user
    filter_form = ProjectFilterForm()
    
    # Determine allowed departments
    if user.role.value == 'Admin':
        # Admin users can see projects from ALL departments regardless of their assigned department
        allowed = [d.id for d in Department.query.with_entities(Department.id).all()]
    else:
        # Non-admin users are restricted to their department hierarchy
        own = user.department  # may be None for users without dept assignment
        if own:
            allowed = own.get_descendant_ids(include_self=True)
        else:
            # For users without department assignment (unassigned users)
            # Show all departments to prevent access issues
            allowed = [d.id for d in Department.query.with_entities(Department.id).all()]
    
    # Add extra departments if user has any
    if hasattr(user, 'extra_departments') and user.extra_departments:
        extras = [d.id for d in user.extra_departments]
        allowed = list(set(allowed + extras))
    
    # Handle department selection from dropdown
    sel = request.args.get('dept', type=int)
    if sel and sel in allowed:
        allowed = [sel]
    
    # Build query with department filtering
    query = Project.query.filter_by(organization_id=current_user.organization_id).filter(Project.department_id.in_(allowed))
    
    # Apply filters
    if request.args.get('status'):
        query = query.filter(Project.status == request.args.get('status'))
    
    if request.args.get('priority'):
        query = query.filter(Project.priority == request.args.get('priority'))
    
    # Additional department filter (user-selected filter within allowed departments)
    if request.args.get('department_id') and int(request.args.get('department_id')) > 0:
        department_id = int(request.args.get('department_id'))
        # Verify the selected department is within user's allowed departments
        if user.department_id:
            user_department = Department.query.get(user.department_id)
            allowed_dept_ids = user_department.get_descendant_ids(include_self=True)
            if department_id in allowed_dept_ids:
                query = query.filter(Project.department_id == department_id)
    
    if request.args.get('project_manager_id') and int(request.args.get('project_manager_id')) > 0:
        query = query.filter(Project.project_manager_id == int(request.args.get('project_manager_id')))
    

    
    # Order by creation date (newest first)
    projects = query.order_by(Project.created_at.desc()).all()
    
    # Calculate project statistics
    project_stats = {
        'total': len(projects),
        'open': len([p for p in projects if p.status == StatusEnum.Open]),
        'in_progress': len([p for p in projects if p.status == StatusEnum.InProgress]),
        'resolved': len([p for p in projects if p.status == StatusEnum.Resolved]),
        'on_hold': len([p for p in projects if p.status == StatusEnum.OnHold])
    }
    
    # Get departments for filter dropdown (only user's allowed departments)
    departments = Department.query.filter(Department.id.in_(allowed)).order_by(Department.name).all()
    
    return render_template('projects/index.html', 
                         projects=projects, 
                         filter_form=filter_form,
                         project_stats=project_stats,
                         departments=departments,
                         current_user=current_user)


@projects_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_project():
    """Create a new project"""
    user = current_user
    form = ProjectForm()
    
    # Strict department enforcement: users can only create projects for their own department
    # Exception: Admin users can select any department
    if user.role.value == 'Admin':
        form.department_id.choices = Department.get_hierarchical_choices()
    else:
        # Hide department field for non-admin users - auto-assign their department
        form.department_id.choices = [(user.department_id, user.department.name if user.department else 'Unknown Department')]
        form.department_id.data = user.department_id
    
    if form.validate_on_submit():
        # Enforce department assignment: non-admin users can only create for their department
        department_id = user.department_id if user.role.value != 'Admin' else form.department_id.data
        
        project = Project(
            name=form.name.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            budget=form.budget.data,
            status=StatusEnum(form.status.data),
            priority=PriorityEnum(form.priority.data),
            business_case_id=form.business_case_id.data if form.business_case_id.data > 0 else None,
            project_manager_id=form.project_manager_id.data,
            department_id=department_id,
            organization_id=user.organization_id,  # Add organization_id for multi-tenant security
            created_by=user.id
        )
        
        db.session.add(project)
        db.session.flush()
        
        # Auto-generate project code
        project.code = f"PRJ{project.id:04d}"
        
        db.session.commit()
        
        # Trigger workflow events asynchronously
        try:
            from workflows.event_queue import enqueue_workflow_event
            project_context = {
                'project': {
                    'id': project.id,
                    'code': project.code,
                    'name': project.name,
                    'description': project.description,
                    'status': project.status.name,
                    'priority': project.priority.name,
                    'project_manager': project.project_manager_id,
                    'created_by': project.created_by,
                    'dept_id': project.department_id,
                    'start_date': project.start_date.isoformat() if project.start_date else None,
                    'end_date': project.end_date.isoformat() if project.end_date else None,
                    'budget': project.budget or 0
                },
                'user_id': current_user.id,
                'department_id': project.department_id
            }
            enqueue_workflow_event('project_created', project_context)
        except Exception:
            pass
        
        flash(f'Project "{project.code}" created successfully!', 'success')
        return redirect(url_for('projects.view_project', id=project.id))
    
    return render_template('projects/project_form.html', 
                         form=form, 
                         title='Create New Project',
                         current_user=current_user)


@projects_bp.route('/<int:id>')
@login_required
def view_project(id):
    """View a specific project with its milestones"""
    from flask_login import current_user
    project = Project.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    
    # Get milestones ordered by due date
    milestones = ProjectMilestone.query.filter_by(project_id=id).order_by(ProjectMilestone.due_date).all()
    
    # Calculate project progress
    total_milestones = len(milestones)
    completed_milestones = len([m for m in milestones if m.completed])
    progress_percentage = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
    
    # Check for overdue milestones
    today = date.today()
    overdue_milestones = [m for m in milestones if m.due_date < today and not m.completed]
    
    # Upcoming milestones (next 30 days)
    from datetime import timedelta
    upcoming_date = today + timedelta(days=30)
    upcoming_milestones = [m for m in milestones if today <= m.due_date <= upcoming_date and not m.completed]
    
    # Get epics linked to this project
    project_epics = Epic.query.filter_by(project_id=id, organization_id=current_user.organization_id).all()
    
    # Get all epics from linked business case for sync status comparison
    business_case_epics = []
    if project.business_case:
        business_case_epics = Epic.query.filter_by(case_id=project.business_case.id, organization_id=current_user.organization_id).all()
    
    project_stats = {
        'total_milestones': total_milestones,
        'completed_milestones': completed_milestones,
        'progress_percentage': round(progress_percentage, 1),
        'overdue_count': len(overdue_milestones),
        'upcoming_count': len(upcoming_milestones),
        'total_epics': len(project_epics),
        'synced_epics': len([e for e in project_epics if e.project_id == id]),
        'business_case_epics': len(business_case_epics)
    }
    
    return render_template('projects/project_detail.html', 
                         project=project,
                         milestones=milestones,
                         project_stats=project_stats,
                         overdue_milestones=overdue_milestones,
                         upcoming_milestones=upcoming_milestones,
                         project_epics=project_epics,
                         business_case_epics=business_case_epics,
                         current_user=current_user,
                         current_date=today,
                         upcoming_date=upcoming_date)


@projects_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(id):
    """Edit an existing project"""
    project = Project.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    form = ProjectForm(obj=project)
    
    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        project.start_date = form.start_date.data
        project.end_date = form.end_date.data
        project.budget = form.budget.data
        project.status = StatusEnum(form.status.data)
        project.priority = PriorityEnum(form.priority.data)
        project.business_case_id = form.business_case_id.data if form.business_case_id.data > 0 else None
        project.project_manager_id = form.project_manager_id.data
        project.department_id = form.department_id.data

        old_status = project.status.name if project.status else 'Unknown'
        project.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Trigger workflow events for status changes asynchronously
        try:
            from workflows.event_queue import enqueue_workflow_event
            if old_status != project.status.name:
                project_context = {
                    'project': {
                        'id': project.id,
                        'code': project.code,
                        'name': project.name,
                        'status': project.status.name,
                        'priority': project.priority.name,
                        'project_manager': project.project_manager_id,
                        'dept_id': project.department_id
                    },
                    'old_status': old_status,
                    'new_status': project.status.name,
                    'user_id': current_user.id,
                    'department_id': project.department_id
                }
                enqueue_workflow_event('project_status_change', project_context)
                
                # Check if project completed
                if project.status.name == 'Completed':
                    enqueue_workflow_event('project_completed', project_context)
        except Exception:
            pass
        
        flash(f'Project "{project.name}" updated successfully!', 'success')
        return redirect(url_for('projects.view_project', id=project.id))
    
    return render_template('projects/project_form.html', 
                         form=form, 
                         title=f'Edit Project: {project.name}',
                         project=project,
                         current_user=current_user)


@projects_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_project(id):
    """Delete a project"""
    project = Project.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    
    # Delete associated milestones first
    ProjectMilestone.query.filter_by(project_id=id).delete()
    
    project_name = project.name
    db.session.delete(project)
    db.session.commit()
    
    flash(f'Project "{project_name}" deleted successfully!', 'success')
    return redirect(url_for('projects.index'))


@projects_bp.route('/<int:id>/submit-for-review', methods=['POST'])
@login_required
def submit_for_review(id):
    """Submit a project for review"""
    project = Project.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    
    # Check if user has permission to submit this project
    if project.created_by != current_user.id and project.project_manager_id != current_user.id and current_user.role.value not in ['Admin', 'Manager', 'Director', 'CEO']:
        flash('You do not have permission to submit this project for review.', 'error')
        return redirect(url_for('projects.view_project', id=id))
    
    # Only allow submission if project is in Open or Draft status
    if project.status not in [StatusEnum.Open]:
        flash(f'Project cannot be submitted for review. Current status: {project.status.value}', 'error')
        return redirect(url_for('projects.view_project', id=id))
    
    # Update project status and submission fields
    project.status = StatusEnum.Submitted
    project.submitted_by = current_user.id
    project.submitted_at = datetime.utcnow()
    
    db.session.commit()
    
    # Send notifications to reviewers
    try:
        from review.routes import notify_reviewers_project_submitted
        notify_reviewers_project_submitted(project)
    except Exception as e:
        print(f"Error sending project submission notifications: {e}")
    
    flash(f'Project "{project.name}" has been submitted for review.', 'success')
    return redirect(url_for('projects.view_project', id=id))


@projects_bp.route('/<int:project_id>/milestones/new', methods=['GET', 'POST'])
@login_required
def new_milestone(project_id):
    """Create a new milestone for a project"""
    project = Project.query.filter_by(id=project_id, organization_id=current_user.organization_id).first_or_404()
    form = MilestoneForm(project_id=project_id)
    
    if form.validate_on_submit():
        # Convert status to boolean completed field
        is_completed = form.status.data == 'completed'
        
        milestone = ProjectMilestone(
            project_id=project_id,
            name=form.name.data,
            description=form.description.data,
            due_date=form.due_date.data,
            owner_id=form.owner_id.data,
            organization_id=current_user.organization_id,
            completed=is_completed,
            completion_date=form.completion_date.data if is_completed else None,
            completion_notes=form.completion_notes.data if is_completed else None
        )
        
        db.session.add(milestone)
        db.session.commit()
        
        # Trigger workflow events for milestone creation asynchronously
        try:
            from workflows.event_queue import enqueue_workflow_event
            milestone_context = {
                'milestone': {
                    'id': milestone.id,
                    'name': milestone.name,
                    'description': milestone.description,
                    'due_date': milestone.due_date.isoformat() if milestone.due_date else None,
                    'owner_id': milestone.owner_id,
                    'project_id': project_id,
                    'completed': milestone.completed
                },
                'project': {
                    'id': project.id,
                    'code': project.code,
                    'name': project.name,
                    'project_manager': project.project_manager_id,
                    'dept_id': project.department_id
                },
                'user_id': current_user.id,
                'department_id': project.department_id
            }
            enqueue_workflow_event('milestone_created', milestone_context)
        except Exception:
            pass
        
        flash(f'Milestone "{milestone.name}" created successfully!', 'success')
        return redirect(url_for('projects.view_project', id=project_id))
    
    return render_template('projects/milestone_form.html', 
                         form=form, 
                         project=project,
                         title=f'Add Milestone to {project.name}',
                         current_user=current_user)


@projects_bp.route('/milestones/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_milestone(id):
    """Edit an existing milestone"""
    milestone = ProjectMilestone.query.get_or_404(id)
    form = MilestoneForm(project_id=milestone.project_id, obj=milestone)
    
    # Pre-populate status field based on completed boolean
    if request.method == 'GET':
        if milestone.completed:
            form.status.data = 'completed'
        else:
            form.status.data = 'open'  # Default for non-completed milestones
    
    if form.validate_on_submit():
        was_completed = milestone.completed
        
        milestone.name = form.name.data
        milestone.description = form.description.data
        milestone.due_date = form.due_date.data
        milestone.owner_id = form.owner_id.data
        
        # Convert status to boolean completed field
        is_completed = form.status.data == 'completed'
        milestone.completed = is_completed
        
        if is_completed and not milestone.completion_date:
            milestone.completion_date = form.completion_date.data or date.today()
            milestone.completion_notes = form.completion_notes.data
        elif not is_completed:
            milestone.completion_date = None
            milestone.completion_notes = None
        
        db.session.commit()
        
        # Trigger workflow events if milestone was just completed asynchronously
        try:
            if not was_completed and milestone.completed:
                from workflows.event_queue import enqueue_workflow_event
                milestone_context = {
                    'milestone': {
                        'id': milestone.id,
                        'name': milestone.name,
                        'description': milestone.description,
                        'due_date': milestone.due_date.isoformat() if milestone.due_date else None,
                        'completion_date': milestone.completion_date.isoformat() if milestone.completion_date else None,
                        'completion_notes': milestone.completion_notes,
                        'owner_id': milestone.owner_id,
                        'project_id': milestone.project_id,
                        'completed': True
                    },
                    'project': {
                        'id': milestone.project.id,
                        'code': milestone.project.code,
                        'name': milestone.project.name,
                        'project_manager': milestone.project.project_manager_id,
                        'dept_id': milestone.project.department_id
                    },
                    'user_id': current_user.id,
                    'department_id': milestone.project.department_id
                }
                enqueue_workflow_event('milestone_completed', milestone_context)
        except Exception:
            pass
        
        flash(f'Milestone "{milestone.name}" updated successfully!', 'success')
        return redirect(url_for('projects.view_project', id=milestone.project_id))
    
    return render_template('projects/milestone_form.html', 
                         form=form, 
                         project=milestone.project,
                         milestone=milestone,
                         title=f'Edit Milestone: {milestone.name}',
                         current_user=current_user)


@projects_bp.route('/milestones/<int:id>/complete', methods=['POST'])
@login_required
def complete_milestone(id):
    """Mark a milestone as completed"""
    milestone = ProjectMilestone.query.get_or_404(id)
    
    milestone.completed = True
    milestone.completion_date = date.today()
    milestone.completion_notes = request.form.get('completion_notes', '')
    
    db.session.commit()
    
    # Trigger workflow events for milestone completion asynchronously
    try:
        from workflows.event_queue import enqueue_workflow_event
        milestone_context = {
            'milestone': {
                'id': milestone.id,
                'name': milestone.name,
                'description': milestone.description,
                'due_date': milestone.due_date.isoformat() if milestone.due_date else None,
                'completion_date': milestone.completion_date.isoformat(),
                'completion_notes': milestone.completion_notes,
                'owner_id': milestone.owner_id,
                'project_id': milestone.project_id,
                'completed': True
            },
            'project': {
                'id': milestone.project.id,
                'code': milestone.project.code,
                'name': milestone.project.name,
                'project_manager': milestone.project.project_manager_id,
                'dept_id': milestone.project.department_id
            },
            'user_id': current_user.id,
            'department_id': milestone.project.department_id
        }
        enqueue_workflow_event('milestone_completed', milestone_context)
    except Exception:
        pass
    
    flash(f'Milestone "{milestone.name}" marked as completed!', 'success')
    return redirect(url_for('projects.view_project', id=milestone.project_id))


@projects_bp.route('/milestones/<int:id>/delete', methods=['POST'])
@login_required
def delete_milestone(id):
    """Delete a milestone"""
    milestone = ProjectMilestone.query.get_or_404(id)
    project_id = milestone.project_id
    milestone_name = milestone.name
    
    db.session.delete(milestone)
    db.session.commit()
    
    flash(f'Milestone "{milestone_name}" deleted successfully!', 'success')
    return redirect(url_for('projects.view_project', id=project_id))


@projects_bp.route('/<int:id>/backlog')
@login_required
def project_backlog(id):
    """Project Backlog - View and refine epics and stories for Business Analysts"""
    from flask_login import current_user
    project = Project.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    
    # Get all epics linked to this project
    from models import Epic, Story
    epics = Epic.query.filter_by(project_id=id, organization_id=current_user.organization_id).all()
    
    # Calculate summary statistics
    total_stories = 0
    high_priority_stories = 0
    estimated_stories = 0
    
    for epic in epics:
        epic_stories = Story.query.filter_by(epic_id=epic.id, organization_id=current_user.organization_id).all()
        epic.stories = epic_stories  # Add stories to epic for template access
        total_stories += len(epic_stories)
        
        for story in epic_stories:
            if story.priority and story.priority.lower() == 'high':
                high_priority_stories += 1
            if story.effort_estimate:
                estimated_stories += 1
    
    return render_template('projects/backlog.html',
                         project=project,
                         epics=epics,
                         total_stories=total_stories,
                         high_priority_stories=high_priority_stories,
                         estimated_stories=estimated_stories,
                         user=current_user)

@projects_bp.route('/dashboard')
@login_required
def dashboard():
    """Project management dashboard"""
    from flask_login import current_user
    
    # Overall project statistics
    total_projects = Project.query.count()
    active_projects = Project.query.filter(Project.status.in_([StatusEnum.Open, StatusEnum.InProgress])).count()
    completed_projects = Project.query.filter_by(status=StatusEnum.Resolved, organization_id=current_user.organization_id).count()
    
    # Projects by status
    status_stats = {}
    # Use database-compatible enum values
    db_status_mapping = {
        'Open': StatusEnum.Open,
        'InProgress': StatusEnum.InProgress,
        'Resolved': StatusEnum.Resolved,
        'OnHold': StatusEnum.OnHold
    }
    
    for status_name, status_enum in db_status_mapping.items():
        try:
            status_stats[status_name] = Project.query.filter_by(status=status_enum, organization_id=current_user.organization_id).count()
        except Exception:
            # Fallback for enum compatibility issues
            status_stats[status_name] = 0
    
    # Recent projects
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    
    # Overdue milestones across all projects
    today = date.today()
    overdue_milestones = ProjectMilestone.query.filter(
        and_(ProjectMilestone.due_date < today, ProjectMilestone.completed == False)
    ).order_by(ProjectMilestone.due_date).limit(10).all()
    
    # Upcoming milestones (next 14 days)
    from datetime import timedelta
    upcoming_date = today + timedelta(days=14)
    upcoming_milestones = ProjectMilestone.query.filter(
        and_(
            ProjectMilestone.due_date.between(today, upcoming_date),
            ProjectMilestone.completed == False
        )
    ).order_by(ProjectMilestone.due_date).limit(10).all()
    
    # Projects by department
    dept_stats = db.session.query(
        Department.name,
        db.func.count(Project.id).label('project_count')
    ).join(Project).group_by(Department.name).all()
    
    dashboard_data = {
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'status_stats': status_stats,
        'recent_projects': recent_projects,
        'overdue_milestones': overdue_milestones,
        'upcoming_milestones': upcoming_milestones,
        'dept_stats': dept_stats
    }
    
    return render_template('projects/dashboard.html', 
                         dashboard_data=dashboard_data,
                         current_user=current_user)