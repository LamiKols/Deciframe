from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from app import db
from models import BusinessCase, Problem, StatusEnum, CaseTypeEnum, CaseDepthEnum, ProjectTypeEnum, Department, RoleEnum, Epic, Story, PriorityEnum, Project, EpicComment, EpicSyncLog
from business.forms import BusinessCaseForm, AssignBAForm, BusinessCaseFilterForm
from flask_login import login_required, current_user
from auth.session_auth import require_session_auth, require_role
from config import Config
from datetime import datetime
from sqlalchemy import or_
import logging

business_bp = Blueprint('business', __name__, template_folder='templates')

@business_bp.route('/')
@login_required
def index():
    """Business module index - redirect to business cases listing"""
    return redirect(url_for('business.cases'))

def sync_epics_to_project(business_case_id, project_id):
    """Auto-link all epics in a business case to the project when case is approved"""
    try:
        epics = Epic.query.filter_by(case_id=business_case_id, project_id=None, organization_id=current_user.organization_id).all()
        linked_count = 0
        
        for epic in epics:
            epic.project_id = project_id
            linked_count += 1
            print(f"🔗 Synced Epic {epic.id} '{epic.title}' to Project {project_id}")
        
        if linked_count > 0:
            db.session.commit()
            print(f"✅ Successfully linked {linked_count} epic(s) to Project {project_id}")
            
        return linked_count
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error syncing epics to project: {str(e)}")
        return 0

@business_bp.route('/cases/new', methods=['GET','POST'])
@login_required
def new_case():
    print(f"🔧 Business case route called: {request.method}")
    from models import Solution
    
    form = BusinessCaseForm()
    # Populate problem choices including the specific problem if solution context exists
    problems = Problem.query.filter_by(organization_id=current_user.organization_id).all()  # Include all problems, not just open ones
    form.problem.choices = [(p.id, f"{p.code} – {p.title}") for p in problems]
    

    
    # Handle solution-to-business-case workflow
    solution_id = request.args.get('solution_id')
    solution = None
    if solution_id and request.method == 'GET':
        try:
            solution = Solution.query.get(int(solution_id))
            if solution:
                form.problem.data = solution.problem_id
                form.solution_id.data = solution_id
                form.solution_description.data = solution.description
                # Pre-populate title and description from solution
                form.title.data = f"Business Case for: {solution.title or solution.name}"
                form.description.data = f"Business case developed from AI-recommended solution.\n\nOriginal Solution: {solution.title or solution.name}\n\nSolution Details: {solution.description}"
                print(f"🔧 Pre-populated form with solution {solution_id}, problem {solution.problem_id}")
        except (ValueError, TypeError):
            flash("Invalid solution reference", "warning")
    
    if request.method == 'POST':
        print(f"🔧 POST request received, validating form...")
        # Re-populate choices for POST validation
        form.problem.choices = [(p.id, f"{p.code} – {p.title}") for p in problems]
        
        # Get solution context for POST requests
        if form.solution_id.data:
            try:
                solution = Solution.query.get(int(form.solution_id.data))
                print(f"🔧 POST with solution context: {form.solution_id.data}")
            except (ValueError, TypeError):
                solution = None
    
    if form.validate_on_submit():
        print(f"🔧 Form validated successfully")
        user = current_user
        
        # Determine case type, depth, and project type
        ct = CaseTypeEnum[form.case_type.data]
        cd = CaseDepthEnum[form.case_depth.data]
        pt = ProjectTypeEnum[form.project_type.data]  # Direct mapping since form now uses enum values
        cost = float(form.cost_estimate.data) if form.cost_estimate.data else 0.0
        
        # Validate case type requirements
        if ct is CaseTypeEnum.Reactive:
            if not form.problem.data:
                flash("Please select a Problem", "danger")
                return render_template('case_form.html', form=form)
            init_name = None
        else:
            if not form.initiative_name.data or not form.initiative_name.data.strip():
                flash("Please enter an Initiative Name", "danger")
                return render_template('case_form.html', form=form)
            init_name = form.initiative_name.data

        # Check cost threshold - if over threshold, require Full case
        if cost > Config.FULL_CASE_THRESHOLD and cd is CaseDepthEnum.Light:
            flash(f"Cost estimate (${cost:,.2f}) exceeds threshold (${Config.FULL_CASE_THRESHOLD:,.2f}). Full case elaboration is required.", "warning")
            return render_template('case_form.html', form=form)

        # Validate Full case requirements
        if cd is CaseDepthEnum.Full:
            full_fields = [
                ('strategic_alignment', form.strategic_alignment.data),
                ('benefit_breakdown', form.benefit_breakdown.data),
                ('risk_mitigation', form.risk_mitigation.data),
                ('stakeholder_analysis', form.stakeholder_analysis.data),
                ('dependencies', form.dependencies.data),
                ('roadmap', form.roadmap.data),
                ('sensitivity_analysis', form.sensitivity_analysis.data)
            ]
            
            missing_fields = [field_name.replace('_', ' ').title() for field_name, value in full_fields if not value or not value.strip()]
            
            if missing_fields:
                flash(f"Full case requires all sections to be completed. Missing: {', '.join(missing_fields)}", "danger")
                return render_template('case_form.html', form=form)

        # Determine department assignment - business cases need department references, not org_unit
        # For now, assign to the "General" department for the organization
        from models import Department
        default_dept = Department.query.filter_by(
            organization_id=user.organization_id,
            name='General'
        ).first()
        
        if not default_dept:
            # Create a default "General" department for organization
            default_dept = Department(
                name='General',
                description='Default department for users without specific department assignment',
                organization_id=user.organization_id
            )
            db.session.add(default_dept)
            db.session.flush()  # Get the ID
        
        dept_id = default_dept.id

        # Create BusinessCase
        bc = BusinessCase(
            problem_id=(form.problem.data if ct is CaseTypeEnum.Reactive else None),
            solution_id=int(form.solution_id.data) if form.solution_id.data else None,
            title=form.title.data,
            description=form.description.data,
            summary=form.summary.data,
            cost_estimate=cost,
            benefit_estimate=float(form.benefit_estimate.data) if form.benefit_estimate.data else 0.0,
            created_by=user.id,
            dept_id=dept_id,  # Use determined department (user's or default)
            organization_id=user.organization_id,  # Critical: enforce multi-tenant isolation
            case_type=ct,
            case_depth=cd,
            project_type=pt,
            initiative_name=init_name,
            strategic_alignment=form.strategic_alignment.data if cd is CaseDepthEnum.Full else None,
            benefit_breakdown=form.benefit_breakdown.data if cd is CaseDepthEnum.Full else None,
            risk_mitigation=form.risk_mitigation.data if cd is CaseDepthEnum.Full else None,
            stakeholder_analysis=form.stakeholder_analysis.data if cd is CaseDepthEnum.Full else None,
            dependencies=form.dependencies.data if cd is CaseDepthEnum.Full else None,
            roadmap=form.roadmap.data if cd is CaseDepthEnum.Full else None,
            sensitivity_analysis=form.sensitivity_analysis.data if cd is CaseDepthEnum.Full else None
        )
        
        db.session.add(bc)
        db.session.flush()
        
        # Generate unique code by finding the next available number
        existing_codes = [int(c.code[1:]) for c in BusinessCase.query.filter(BusinessCase.code.isnot(None)).all() if c.code and c.code.startswith('C')]
        next_code_num = 1
        while next_code_num in existing_codes:
            next_code_num += 1
        bc.code = f"C{next_code_num:04d}"
        
        bc.roi = ((bc.benefit_estimate - bc.cost_estimate) / bc.cost_estimate * 100) if bc.cost_estimate else None
        db.session.commit()
        
        # Use only the flash notification to avoid duplicate messages
        flash(f"Business Case {bc.code} created successfully!", 'success')
        return redirect(url_for('business.list_cases'))
    else:
        if request.method == 'POST':
            print(f"🔧 Form validation failed: {form.errors}")
            # Flash all field errors
            for field_name, errors in form.errors.items():
                field_label = getattr(form, field_name).label.text if hasattr(getattr(form, field_name), 'label') else field_name
                for error in errors:
                    flash(f"{field_label}: {error}", "danger")
        
    # Render the template with solution context
    return render_template('case_form.html', form=form, solution=solution)

@business_bp.route('/cases', methods=['GET'])
@login_required
def list_cases():
    user = current_user
    
    # Get filter parameters
    q = request.args.get('q', '', type=str)
    department = request.args.get('department', type=int)
    status = request.args.get('status', type=str)
    assigned = request.args.get('assigned')  # 'true', 'false', or None
    page = request.args.get('page', 1, type=int)
    
    # Determine allowed departments
    if user.role.value == 'Admin':
        # Admin users can see business cases from ALL departments regardless of their assigned department
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
    query = BusinessCase.query.filter_by(organization_id=current_user.organization_id).filter(BusinessCase.dept_id.in_(allowed))
    
    # Text search on title and description
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(BusinessCase.title.ilike(like), BusinessCase.description.ilike(like))
        )
    
    # Additional department filter (user-selected filter within allowed departments)
    if department and department in allowed:
        query = query.filter(BusinessCase.dept_id == department)
    
    # Status filter
    if status:
        query = query.filter(BusinessCase.status == StatusEnum[status])
    
    # Assignment filter
    if assigned == 'true':
        query = query.filter(BusinessCase.assigned_ba_id.isnot(None))
    elif assigned == 'false':
        query = query.filter(BusinessCase.assigned_ba_id.is_(None))
    
    # Pagination
    pagination = query.order_by(BusinessCase.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    cases = pagination.items
    
    # Get departments for filter dropdown (only user's allowed departments)
    departments = Department.query.filter(Department.id.in_(allowed)).order_by(Department.name).all()
    
    return render_template('cases.html', 
                         cases=cases, 
                         pagination=pagination,
                         departments=departments,
                         StatusEnum=StatusEnum,
                         user=user, 
                         assigned_filter=assigned)

@business_bp.route('/cases/<int:id>', methods=['GET', 'POST'])
@login_required
def view_case(id):
    """View a specific business case with BA assignment capability"""
    user = current_user
    business_case = BusinessCase.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    
    # Load associated epics and stories
    epics = Epic.query.filter_by(case_id=id, organization_id=current_user.organization_id).all()
    for epic in epics:
        epic.stories = Story.query.filter_by(epic_id=epic.id, organization_id=current_user.organization_id).all()
    
    # Check for linked project from business case approval
    linked_project = None
    if business_case.status == StatusEnum.Resolved:
        from models import Project
        linked_project = Project.query.filter_by(business_case_id=id, organization_id=current_user.organization_id).first()
    
    # Check if user can assign BAs (Manager, Director, CEO, Admin)
    can_assign = user.role.value in ['Manager', 'Director', 'CEO', 'Admin']
    
    form = None
    if can_assign:
        form = AssignBAForm()
        # Populate with all Business Analysts
        from models import RoleEnum, User
        form.assigned_ba.choices = [
            (u.id, u.name) for u in User.query.filter_by(role=RoleEnum.BA).order_by(User.name)
        ]
        
        if form.validate_on_submit():
            business_case.assigned_ba_id = form.assigned_ba.data
            db.session.commit()
            
            # Trigger workflow events for BA assignment asynchronously
            try:
                from workflows.event_queue import enqueue_workflow_event
                case_context = {
                    'case': {
                        'id': business_case.id,
                        'code': business_case.code,
                        'title': business_case.title,
                        'summary': business_case.summary,
                        'case_type': business_case.case_type.name,
                        'status': business_case.status.name,
                        'assigned_ba': business_case.assigned_ba_id,
                        'created_by': business_case.created_by,
                        'dept_id': business_case.dept_id
                    },
                    'user_id': user.id,
                    'department_id': business_case.dept_id
                }
                enqueue_workflow_event('case_assigned', case_context)
            except Exception as e:
                pass
            
            # Send notification to assigned BA
            try:
                from notifications.service import NotificationService
                from models import NotificationEventEnum
                service = NotificationService()
                service.notify_user(
                    user_id=business_case.assigned_ba_id,
                    event_type=NotificationEventEnum.BUSINESS_CASE_CREATED,
                    message=f"You have been assigned Business Case {business_case.code}.",
                    link=f"/business/cases/{business_case.id}"
                )
            except Exception as e:
                print(f"Notification failed: {e}")
            
            flash(f'Business Case {business_case.code} assigned to {business_case.assigned_ba.name}.', 'success')
            return redirect(url_for('business.view_case', id=id))
    
    return render_template('case_detail.html', business_case=business_case, user=user, form=form, can_assign=can_assign, epics=epics, linked_project=linked_project, epics_count=len(epics))

@business_bp.route('/cases/<int:id>/approve', methods=['POST'])
@login_required
def approve_case(id):
    """Approve a business case and create linked project"""
    user = current_user
    business_case = BusinessCase.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    
    # Check if user has approval authority (Director role required)
    if user.role.value not in ['Director', 'CEO', 'Admin']:
        flash("You don't have permission to approve business cases.", "danger")
        return redirect(url_for('business.view_case', id=id))
    
    try:
        from models import Project, Epic, Story, PriorityEnum
        from datetime import datetime
        
        # Update case status to approved
        business_case.status = StatusEnum.Approved
        business_case.approved_by = user.id
        business_case.approved_at = datetime.utcnow()
        
        # 1) Create Project with all required fields
        # Ensure department assignment: use business case dept, or fallback to user's department
        project_dept_id = business_case.dept_id or user.department_id
        
        # Clean up project title by removing "Business Case for:" prefix
        project_title = business_case.title
        if project_title.startswith("Business Case for:"):
            project_title = project_title.replace("Business Case for:", "").strip()
        
        project = Project(
            name=project_title,
            description=business_case.description or "Project created from approved business case",
            business_case_id=business_case.id,
            project_manager_id=user.id,
            department_id=project_dept_id,
            created_by=user.id,
            organization_id=user.organization_id,
            status=StatusEnum.Open,
            priority=PriorityEnum.Medium
        )
        db.session.add(project)
        db.session.flush()
        
        # Generate project code after creation
        project.code = f"PRJ{project.id:04d}"
        
        # 2) Link existing Epics & Stories to project
        epics = Epic.query.filter_by(case_id=business_case.id, organization_id=current_user.organization_id).all()
        for epic in epics:
            epic.project_id = project.id
            
        stories = Story.query.join(Epic).filter(Epic.case_id == business_case.id).all()
        for story in stories:
            story.project_id = project.id
        
        db.session.commit()
        
        flash(f'Business Case {business_case.code} approved and Project {project.code} ({project.name}) created successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving business case: {e}")
        flash(f'Error approving business case: {str(e)}', 'danger')
        return redirect(url_for('business.view_case', id=id))
    
    # Trigger workflow events for case approval asynchronously
    try:
        from workflows.event_queue import enqueue_workflow_event
        case_context = {
            'case': {
                'id': business_case.id,
                'code': business_case.code,
                'title': business_case.title,
                'summary': business_case.summary,
                'case_type': business_case.case_type.name,
                'status': business_case.status.name,
                'priority': business_case.priority.name if business_case.priority else 'Medium',
                'estimated_cost': business_case.cost_estimate or 0,
                'expected_benefit': business_case.benefit_estimate or 0,
                'approved_by': business_case.approved_by,
                'approved_at': business_case.approved_at.isoformat(),
                'created_by': business_case.created_by,
                'dept_id': business_case.department_id,
                'roi_percentage': business_case.roi or 0
            },
            'user_id': user.id,
            'department_id': business_case.department_id,
            'project_id': project.id if project else None
        }
        enqueue_workflow_event('case_approved', case_context)
        
        if project:
            project_context = {
                'project': {
                    'id': project.id,
                    'code': project.code,
                    'name': project.name,
                    'budget': project.budget,
                    'status': project.status.name,
                    'priority': project.priority.name,
                    'business_case_id': project.business_case_id,
                    'project_manager_id': project.project_manager_id,
                    'department_id': project.department_id
                },
                'user_id': user.id,
                'department_id': project.department_id
            }
            enqueue_workflow_event('project_created', project_context)
    except Exception as e:
        pass
    
    # 3) Redirect to backlog
    return redirect(url_for('projects.project_backlog', id=project.id))

@business_bp.route('/cases/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_case(id):
    """Edit an existing business case"""
    business_case = BusinessCase.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    form = BusinessCaseForm(obj=business_case)
    form.problem.choices = [(p.id, f"{p.code} – {p.title}") for p in Problem.query.filter_by(status=StatusEnum.Open, organization_id=current_user.organization_id).all()]
    
    if request.method == 'GET':
        form.problem.data = business_case.problem_id
        form.case_type.data = business_case.case_type.value if business_case.case_type else 'Reactive'
        form.initiative_name.data = getattr(business_case, 'initiative_name', '')
        form.summary.data = getattr(business_case, 'summary', '')
        # Populate all form fields for editing
        form.title.data = business_case.title
        form.description.data = business_case.description
        form.cost_estimate.data = business_case.cost_estimate
        form.benefit_estimate.data = business_case.benefit_estimate
        form.case_depth.data = business_case.case_depth.value if business_case.case_depth else 'Light'
    
    if form.validate_on_submit():
        # Determine case type
        ct = CaseTypeEnum[form.case_type.data]
        
        if ct is CaseTypeEnum.Reactive:
            if not form.problem.data:
                flash("Please select a Problem", "danger")
                return render_template('case_form.html', form=form, business_case=business_case, action='Edit')
            business_case.problem_id = form.problem.data
            business_case.initiative_name = None
        else:
            if not form.initiative_name.data or not form.initiative_name.data.strip():
                flash("Please enter an Initiative Name", "danger")
                return render_template('case_form.html', form=form, business_case=business_case, action='Edit')
            business_case.problem_id = None
            business_case.initiative_name = form.initiative_name.data
        
        business_case.case_type = ct
        business_case.title = form.title.data
        business_case.description = form.description.data
        business_case.cost_estimate = float(form.cost_estimate.data) if form.cost_estimate.data else 0.0
        business_case.benefit_estimate = float(form.benefit_estimate.data) if form.benefit_estimate.data else 0.0
        
        # Recalculate ROI
        business_case.roi = ((business_case.benefit_estimate - business_case.cost_estimate) / business_case.cost_estimate * 100) if business_case.cost_estimate else None
        
        db.session.commit()
        flash(f'Business Case {business_case.code} updated successfully!', 'success')
        return redirect(url_for('business.view_case', id=business_case.id))
    
    return render_template('case_form.html', form=form, business_case=business_case, action='Edit')

@business_bp.route('/cases/<int:id>/request-full', methods=['POST'])
@login_required
def request_full_case(id):
    """Request full case elaboration for a Light case"""
    user = current_user
    business_case = BusinessCase.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    
    # Only allow requesting full case for Light cases
    if business_case.case_depth != CaseDepthEnum.Light:
        flash("Full case elaboration can only be requested for Light cases", "warning")
        return redirect(url_for('business.view_case', id=id))
    
    # Mark case as having full elaboration requested
    business_case.full_case_requested = True
    business_case.full_case_requested_by = user.id
    business_case.full_case_requested_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f"Full case elaboration requested for {business_case.code}. The assigned Business Analyst will be notified to complete the additional sections.", "info")
    return redirect(url_for('business.view_case', id=id))

@business_bp.route('/cases/<int:id>/delete', methods=['POST'])
@login_required
def delete_case(id):
    """Delete a business case"""
    user = current_user
    business_case = BusinessCase.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    db.session.delete(business_case)
    db.session.commit()
    flash(f'Business Case {business_case.code} deleted successfully!', 'success')
    return redirect(url_for('business.list_cases'))

@business_bp.route('/cases')
@login_required
def cases():
    """Business cases list page - redirect to list_cases"""
    return redirect(url_for('business.list_cases'))

@business_bp.route('/cases/<int:id>/requirements', methods=['GET'])
@business_bp.route('/requirements/<int:id>', methods=['GET'])
@login_required
def requirements(id):
    """Requirements generator page"""
    user = current_user
    if not user:
        flash('Authentication required', 'error')
        return redirect(url_for('auth.login'))
    
    case = BusinessCase.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    # Eager load epics and stories for display
    case.epics = Epic.query.filter_by(case_id=id, organization_id=current_user.organization_id).all()
    for epic in case.epics:
        epic.stories = Story.query.filter_by(epic_id=epic.id, organization_id=current_user.organization_id).all()
    
    # Check if user can edit (BA only)
    can_edit = user.role == RoleEnum.BA
    can_regenerate = user.role == RoleEnum.BA
    
    return render_template('requirements_clean.html', 
                         case=case, 
                         current_user=user,
                         can_edit=can_edit,
                         can_regenerate=can_regenerate,
                         config=current_app.config)

@business_bp.route('/api/requirements/save', methods=['POST'])
@login_required
def save_requirements():
    """Save inline edits to epics and stories (BA only)"""
    user = current_user
    if not user:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    if user.role != RoleEnum.BA:
        return jsonify({'success': False, 'error': 'Only Business Analysts can edit requirements'}), 403
    
    try:
        data = request.get_json()
        if not data or 'epics' not in data:
            return jsonify({'success': False, 'error': 'Invalid data format'}), 400
        
        updated_epics = 0
        updated_stories = 0
        
        for e in data['epics']:
            if 'id' not in e:
                continue
                
            epic = Epic.query.get(e['id'])
            if epic:
                epic.title = e.get('title', epic.title)
                epic.description = e.get('description', epic.description)
                updated_epics += 1
                
                for s in e.get('stories', []):
                    if 'id' not in s:
                        continue
                        
                    story = Story.query.get(s['id'])
                    if story:
                        story.title = s.get('title', story.title)
                        # Use acceptance_criteria field instead of criteria
                        story.acceptance_criteria = s.get('criteria', story.acceptance_criteria)
                        updated_stories += 1
        
        db.session.commit()
        logging.info(f"BA user {user.id} saved {updated_epics} epics and {updated_stories} stories")
        
        return jsonify({
            'success': True,
            'message': f'Saved {updated_epics} epics and {updated_stories} stories',
            'updated_epics': updated_epics,
            'updated_stories': updated_stories
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error saving requirements: {e}")
        return jsonify({'success': False, 'error': 'Failed to save requirements'}), 500

@business_bp.route('/api/business-cases/<int:case_id>/epics')
@login_required
def get_case_epics(case_id):
    """API endpoint to get epics and stories for a business case"""
    try:
        business_case = BusinessCase.query.filter_by(id=case_id, organization_id=current_user.organization_id).first_or_404()
        
        # Refresh database connection to avoid SSL issues
        db.session.commit()
        
        # Get epics for this case with retry logic
        try:
            epics = Epic.query.filter_by(case_id=case_id, organization_id=current_user.organization_id).all()
        except Exception as db_error:
            # Database connection issue, try to recover
            db.session.rollback()
            db.session.close()
            epics = Epic.query.filter_by(case_id=case_id, organization_id=current_user.organization_id).all()
        
        epics_data = []
        for epic in epics:
            # Get stories for this epic with retry logic
            try:
                stories = Story.query.filter_by(epic_id=epic.id, organization_id=current_user.organization_id).all()
            except Exception as db_error:
                db.session.rollback()
                db.session.close()
                stories = Story.query.filter_by(epic_id=epic.id, organization_id=current_user.organization_id).all()
            
            stories_data = []
            for story in stories:
                stories_data.append({
                    'id': story.id,
                    'title': story.title,
                    'description': story.description,
                    'acceptance_criteria': story.acceptance_criteria,
                    'priority': story.priority,
                    'effort_estimate': story.effort_estimate
                })
            
            epics_data.append({
                'id': epic.id,
                'title': epic.title,
                'description': epic.description,
                'stories': stories_data
            })
        
        return jsonify({
            'success': True,
            'epics': epics_data,
            'case_id': case_id
        })
        
    except Exception as e:
        logging.error(f"Error loading epics for case {case_id}: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to load epics and stories'
        }), 500

# Epic CRUD API endpoints
@business_bp.route('/api/epics', methods=['POST'])
@login_required
def create_epic():
    """Create a new epic"""
    user = current_user
    if user.role.value != 'BA':
        return jsonify({'success': False, 'error': 'Only BAs can create epics'}), 403
    
    try:
        case_id = request.form.get('case_id')
        title = request.form.get('title')
        description = request.form.get('description', '')
        assigned_by = request.form.get('assigned_by', '').strip()
        
        if not case_id or not title:
            return jsonify({'success': False, 'error': 'Case ID and title are required'}), 400
        
        # Verify business case exists and user has access
        business_case = BusinessCase.query.filter_by(id=case_id, organization_id=current_user.organization_id).first_or_404()
        
        epic = Epic(
            title=title,
            description=description,
            case_id=case_id,
            creator_id=user.id,
            assigned_by=assigned_by if assigned_by else None
        )
        
        # Auto-link epic to project if business case is approved and has project
        if business_case.status.value == 'Approved' and business_case.project_id:
            epic.project_id = business_case.project_id
            print(f"🔗 Auto-linked Epic '{epic.title}' to Project {business_case.project_id} (Business Case {business_case.id} is approved)")
        
        db.session.add(epic)
        db.session.commit()
        
        # Log sync action if epic was auto-linked to project
        if epic.project_id:
            sync_log = EpicSyncLog(
                epic_id=epic.id, 
                project_id=epic.project_id, 
                action='synced'
            )
            db.session.add(sync_log)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'epic': {
                'id': epic.id,
                'title': epic.title,
                'description': epic.description
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@business_bp.route('/api/epics/<int:epic_id>', methods=['PUT'])
@login_required
def update_epic(epic_id):
    """Update an existing epic"""
    user = current_user
    if user.role.value != 'BA':
        return jsonify({'success': False, 'error': 'Only BAs can update epics'}), 403
    
    try:
        epic = Epic.query.filter_by(id=epic_id, organization_id=current_user.organization_id).first_or_404()
        
        title = request.form.get('title')
        description = request.form.get('description', '')
        assigned_by = request.form.get('assigned_by', '').strip()
        
        if not title:
            return jsonify({'success': False, 'error': 'Title is required'}), 400
        
        epic.title = title
        epic.description = description
        epic.assigned_by = assigned_by if assigned_by else None
        db.session.commit()
        
        return jsonify({
            'success': True,
            'epic': {
                'id': epic.id,
                'title': epic.title,
                'description': epic.description
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@business_bp.route('/api/epics/<int:epic_id>', methods=['DELETE'])
@login_required
def delete_epic(epic_id):
    """Delete an epic and all its stories"""
    user = current_user
    if user.role.value != 'BA':
        return jsonify({'success': False, 'error': 'Only BAs can delete epics'}), 403
    
    try:
        epic = Epic.query.filter_by(id=epic_id, organization_id=current_user.organization_id).first_or_404()
        
        # Delete all stories in this epic first
        Story.query.filter_by(epic_id=epic_id, organization_id=current_user.organization_id).delete()
        
        # Delete the epic
        db.session.delete(epic)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Story CRUD API endpoints
@business_bp.route('/api/stories', methods=['POST'])
@login_required
def create_story():
    """Create a new user story"""
    user = current_user
    if user.role.value != 'BA':
        return jsonify({'success': False, 'error': 'Only BAs can create stories'}), 403
    
    try:
        epic_id = request.form.get('epic_id')
        title = request.form.get('title')
        description = request.form.get('description', '')
        acceptance_criteria = request.form.get('acceptance_criteria', '')
        priority = request.form.get('priority', 'Medium')
        effort_estimate = request.form.get('effortEstimate')
        
        if not epic_id or not title:
            return jsonify({'success': False, 'error': 'Epic ID and title are required'}), 400
        
        # Verify epic exists and check if it's editable
        epic = Epic.query.filter_by(id=epic_id, organization_id=current_user.organization_id).first_or_404()
        
        if epic.status == 'Approved':
            return jsonify({'success': False, 'error': 'Cannot add stories - Epic is already approved'}), 403
        
        from models import PriorityEnum
        
        story = Story(
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            epic_id=epic_id,
            priority=priority,
            effort_estimate=effort_estimate
        )
        db.session.add(story)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'story': {
                'id': story.id,
                'title': story.title,
                'description': story.description,
                'acceptance_criteria': story.acceptance_criteria,
                'priority': story.priority,
                'effort_estimate': story.effort_estimate
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@business_bp.route('/api/stories/<int:story_id>', methods=['PUT'])
@login_required
def update_story(story_id):
    """Update an existing user story"""
    user = current_user
    if user.role.value != 'BA':
        return jsonify({'success': False, 'error': 'Only BAs can update stories'}), 403
    
    try:
        story = Story.query.filter_by(id=story_id, organization_id=current_user.organization_id).first_or_404()
        
        title = request.form.get('title')
        description = request.form.get('description', '')
        acceptance_criteria = request.form.get('acceptance_criteria', '')
        priority = request.form.get('priority', 'Medium')
        effort_estimate = request.form.get('effortEstimate')
        
        if not title:
            return jsonify({'success': False, 'error': 'Title is required'}), 400
        
        from models import PriorityEnum
        
        story.title = title
        story.description = description
        story.acceptance_criteria = acceptance_criteria
        story.priority = priority
        story.effort_estimate = effort_estimate
        db.session.commit()
        
        return jsonify({
            'success': True,
            'story': {
                'id': story.id,
                'title': story.title,
                'description': story.description,
                'acceptance_criteria': story.acceptance_criteria,
                'priority': story.priority,
                'effort_estimate': story.effort_estimate
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@business_bp.route('/api/stories/<int:story_id>', methods=['DELETE'])
@login_required
def delete_story(story_id):
    """Delete a user story"""
    user = current_user
    if user.role.value != 'BA':
        return jsonify({'success': False, 'error': 'Only BAs can delete stories'}), 403
    
    try:
        story = Story.query.filter_by(id=story_id, organization_id=current_user.organization_id).first_or_404()
        db.session.delete(story)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@business_bp.route('/cases/<int:id>/refine-stories')
@login_required
def refine_stories_page(id):
    """Story refinement UI page"""
    user = current_user
    business_case = BusinessCase.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    
    # Check if user is a Business Analyst
    if user.role.value != 'BA':
        flash("Only Business Analysts can access story refinement.", "danger")
        return redirect(url_for('business.view_case', id=id))
    
    # Load epics and stories directly for template
    epics = Epic.query.filter_by(case_id=id, organization_id=current_user.organization_id).all()
    for epic in epics:
        epic.stories = Story.query.filter_by(epic_id=epic.id, organization_id=current_user.organization_id).all()
    
    return render_template('refine_stories_simple.html', business_case=business_case, user=user, epics=epics)

@business_bp.route('/cases/<int:id>/refine-stories', methods=['POST'])
@login_required
def batch_refine_stories(id):
    """Batch update multiple stories (BA only)"""
    user = current_user
    business_case = BusinessCase.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    
    # Check if user is a Business Analyst
    if user.role.value != 'BA':
        return jsonify({'error': 'Only Business Analysts can refine stories'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        from models import PriorityEnum
        updates_count = 0
        errors = []
        
        # Handle epic updates
        if 'epics' in data:
            for epic_data in data['epics']:
                if 'id' in epic_data:
                    epic = Epic.query.get(epic_data['id'])
                    if epic and epic.case_id == id:
                        # Check if epic can be edited
                        if epic.status == 'Approved':
                            errors.append(f"Cannot edit epic '{epic.title}' - Epic is already approved")
                            continue
                        try:
                            if 'title' in epic_data:
                                epic.title = epic_data['title']
                            if 'description' in epic_data:
                                epic.description = epic_data['description']
                            if 'priority' in epic_data:
                                epic.priority = PriorityEnum(epic_data['priority'])
                            if 'effort_estimate' in epic_data:
                                epic.effort_estimate = epic_data['effort_estimate']
                            
                            epic.updated_at = datetime.utcnow()
                            updates_count += 1
                        except Exception as e:
                            errors.append(f"Failed to update epic {epic_data['id']}: {str(e)}")
        
        # Handle story updates
        if 'stories' in data:
            for story_data in data['stories']:
                if 'id' in story_data:
                    story = Story.query.get(story_data['id'])
                    if story and story.epic and story.epic.case_id == id:
                        try:
                            if 'title' in story_data:
                                story.title = story_data['title']
                            if 'description' in story_data:
                                story.description = story_data['description']
                            if 'priority' in story_data:
                                story.priority = PriorityEnum(story_data['priority'])
                            if 'effort_estimate' in story_data:
                                story.effort_estimate = story_data['effort_estimate']
                            if 'acceptance_criteria' in story_data:
                                story.acceptance_criteria = story_data['acceptance_criteria']
                            
                            story.updated_at = datetime.utcnow()
                            updates_count += 1
                        except Exception as e:
                            errors.append(f"Failed to update story {story_data['id']}: {str(e)}")
        
        # Handle new epics
        if 'new_epics' in data:
            for epic_data in data['new_epics']:
                try:
                    epic = Epic(
                        case_id=id,
                        title=epic_data['title'],
                        description=epic_data.get('description'),
                        priority=PriorityEnum(epic_data.get('priority', 'Medium')),
                        effort_estimate=epic_data.get('effort_estimate', 'M'),
                        creator_id=user.id
                    )
                    db.session.add(epic)
                    updates_count += 1
                except Exception as e:
                    errors.append(f"Failed to create new epic: {str(e)}")
        
        # Handle new stories
        if 'new_stories' in data:
            for story_data in data['new_stories']:
                try:
                    story = Story(
                        epic_id=story_data['epic_id'],
                        title=story_data['title'],
                        description=story_data.get('description'),
                        priority=PriorityEnum(story_data.get('priority', 'Medium')),
                        effort_estimate=story_data.get('effort_estimate', 'S'),
                        acceptance_criteria=story_data.get('acceptance_criteria'),
                        creator_id=user.id
                    )
                    db.session.add(story)
                    updates_count += 1
                except Exception as e:
                    errors.append(f"Failed to create new story: {str(e)}")
        
        # Commit all changes
        db.session.commit()
        
        result = {
            'success': True,
            'message': f'Successfully processed {updates_count} items',
            'updates_count': updates_count
        }
        
        if errors:
            result['warnings'] = errors
        
        return jsonify(result)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Batch update failed: {str(e)}'}), 500

@business_bp.route('/api/stories')
@login_required
def get_stories():
    """API endpoint to get stories by epic_id"""
    epic_id = request.args.get('epic_id')
    logging.info(f"🔍 get_stories called with epic_id: {epic_id}")
    
    if not epic_id:
        logging.error("❌ No epic_id provided")
        return jsonify({'error': 'epic_id parameter required'}), 400
    
    try:
        # Verify epic exists and user has access
        epic = Epic.query.filter_by(id=epic_id, organization_id=current_user.organization_id).first()
        if not epic:
            logging.error(f"❌ Epic {epic_id} not found")
            return jsonify({'error': f'Epic {epic_id} not found'}), 404
            
        business_case = BusinessCase.query.get(epic.case_id)
        if not business_case:
            logging.error(f"❌ Business case {epic.case_id} not found")
            return jsonify({'error': f'Business case not found'}), 404
        
        # Get stories for this epic
        stories = Story.query.filter_by(epic_id=epic_id, organization_id=current_user.organization_id).all()
        logging.info(f"✅ Found {len(stories)} stories for epic {epic_id}")
        
        result = []
        for s in stories:
            # Handle priority field - could be enum or string
            priority_value = 'Medium'
            if s.priority:
                if hasattr(s.priority, 'value'):
                    priority_value = s.priority.value
                else:
                    priority_value = str(s.priority)
            
            result.append({
                'id': s.id,
                'title': s.title,
                'acceptance_criteria': s.acceptance_criteria,
                'description': s.description,
                'priority': priority_value,
                'effort_estimate': s.effort_estimate or 'M'
            })
        
        logging.info(f"✅ Returning {len(result)} stories")
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"❌ Exception in get_stories: {str(e)}")
        return jsonify({'error': f'Failed to load stories: {str(e)}'}), 500

@business_bp.route('/api/stories/v2')
@login_required
def get_stories_v2():
    """Enhanced API endpoint with pagination and filtering"""
    epic_id = request.args.get('epic_id')
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    stakeholder = request.args.get('stakeholder')
    status = request.args.get('status')
    
    logging.info(f"🔍 get_stories_v2 called with epic_id: {epic_id}, limit: {limit}, offset: {offset}")
    
    if not epic_id:
        logging.error("❌ No epic_id provided")
        return jsonify({'error': 'epic_id parameter required'}), 400
    
    try:
        # Verify epic exists and user has access
        epic = Epic.query.filter_by(id=epic_id, organization_id=current_user.organization_id).first()
        if not epic:
            logging.error(f"❌ Epic {epic_id} not found")
            return jsonify({'error': f'Epic {epic_id} not found'}), 404
            
        business_case = BusinessCase.query.get(epic.case_id)
        if not business_case:
            logging.error(f"❌ Business case {epic.case_id} not found")
            return jsonify({'error': f'Business case not found'}), 404
        
        # Build query with filters
        query = Story.query.filter_by(epic_id=epic_id, organization_id=current_user.organization_id)
        
        if stakeholder:
            # Add stakeholder filter if the field exists on Story model
            # Note: This assumes stakeholder field exists, adjust if needed
            if hasattr(Story, 'stakeholder'):
                query = query.filter_by(stakeholder=stakeholder)
                
        if status:
            # Add status filter if the field exists on Story model
            if hasattr(Story, 'status'):
                query = query.filter_by(status=status)
        
        total = query.count()
        stories = query.offset(offset).limit(limit).all()
        
        logging.info(f"✅ Found {len(stories)} stories (total: {total}) for epic {epic_id}")
        
        result = {
            'stories': [],
            'total': total,
            'limit': limit,
            'offset': offset
        }
        
        for s in stories:
            # Handle priority field - could be enum or string
            priority_value = 'Medium'
            if s.priority:
                if hasattr(s.priority, 'value'):
                    priority_value = s.priority.value
                else:
                    priority_value = str(s.priority)
            
            story_data = {
                'id': s.id,
                'title': s.title,
                'description': s.description,
                'acceptance_criteria': s.acceptance_criteria,
                'priority': priority_value,
                'effort_estimate': s.effort_estimate or 'M'
            }
            
            # Add stakeholder if field exists
            if hasattr(s, 'stakeholder'):
                story_data['stakeholder'] = s.stakeholder
                
            # Add status if field exists
            if hasattr(s, 'status'):
                story_data['status'] = s.status
                
            result['stories'].append(story_data)
        
        logging.info(f"✅ Returning paginated stories: {len(result['stories'])}/{total}")
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"❌ Exception in get_stories_v2: {str(e)}")
        return jsonify({'error': f'Failed to load stories: {str(e)}'}), 500

# Epic Status Transition Routes
@business_bp.route('/epic/<int:epic_id>/submit', methods=['POST'])
@login_required
def submit_epic(epic_id):
    """Submit epic for review"""
    try:
        epic = Epic.query.filter_by(id=epic_id, organization_id=current_user.organization_id).first_or_404()
        
        # Debug logging
        print(f"🔍 Submit Epic - User: {current_user.email}, Role: {current_user.role.value}")
        print(f"🔍 Epic ID: {epic_id}, Current Status: {epic.status}, Creator: {epic.creator_id}")
        
        # Check if user has permission to submit this epic
        if epic.creator_id != current_user.id and current_user.role.value not in ['Admin', 'Manager', 'Director', 'BA']:
            flash('You do not have permission to submit this epic', 'error')
            print(f"❌ Permission denied for user {current_user.id}")
            return redirect(url_for('business.refine_stories_page', id=epic.case_id))
        
        # Check if epic is in draft status
        if epic.status != 'Draft':
            flash(f'Epic cannot be submitted - current status is {epic.status}', 'warning')
            print(f"❌ Epic status check failed: {epic.status}")
            return redirect(url_for('business.refine_stories_page', id=epic.case_id))
        
        epic.status = 'Submitted'
        epic.updated_at = datetime.utcnow()
        db.session.commit()
        
        print(f"✅ Epic {epic_id} status updated to Submitted")
        flash(f'Epic "{epic.title}" has been submitted for review', 'success')
        return redirect(url_for('business.refine_stories_page', id=epic.case_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting epic: {str(e)}', 'error')
        return redirect(url_for('business.refine_stories_page', id=epic.case_id))

@business_bp.route('/epic/<int:epic_id>/review', methods=['POST'])
@login_required
def review_epic(epic_id):
    """Approve or reject epic with comments"""
    try:
        epic = Epic.query.filter_by(id=epic_id, organization_id=current_user.organization_id).first_or_404()
        
        # Check if user has permission to review epics (Manager, Director, Admin)
        if current_user.role not in [RoleEnum.Admin, RoleEnum.Manager, RoleEnum.Director]:
            flash('You do not have permission to review epics', 'error')
            return redirect(url_for('business.refine_stories_page', id=epic.case_id))
        
        # Check if epic is in submitted status
        if epic.status != 'Submitted':
            flash(f'Epic cannot be reviewed - current status is {epic.status}', 'warning')
            return redirect(url_for('business.refine_stories_page', id=epic.case_id))
        
        action = request.form.get('action')  # 'approve' or 'reject'
        comment = request.form.get('comment', '').strip()
        
        if action == 'approve':
            epic.status = 'Approved'
            epic.assigned_by = f"{current_user.first_name} {current_user.last_name}" if current_user.first_name else current_user.email
            flash_message = f'Epic "{epic.title}" has been approved'
        elif action == 'reject':
            epic.status = 'Rejected'
            epic.assigned_by = f"{current_user.first_name} {current_user.last_name}" if current_user.first_name else current_user.email
            flash_message = f'Epic "{epic.title}" has been rejected'
        else:
            flash('Invalid action specified', 'error')
            return redirect(url_for('business.refine_stories_page', id=epic.case_id))
        
        # Add comment with reviewer information and timestamp
        review_comment = f"[{epic.status} by {epic.assigned_by} on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}]"
        if comment:
            review_comment += f"\n{comment}"
        
        # Append to existing comments or create new
        if epic.comments:
            epic.comments += f"\n\n{review_comment}"
        else:
            epic.comments = review_comment
            
        epic.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash(flash_message, 'success')
        return redirect(url_for('business.refine_stories_page', id=epic.case_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error reviewing epic: {str(e)}', 'error')
        return redirect(url_for('business.refine_stories_page', id=epic.case_id))

@business_bp.route('/epic/<int:epic_id>/reset', methods=['POST'])
@login_required
def reset_epic(epic_id):
    """Reset epic back to draft status for re-editing"""
    try:
        epic = Epic.query.filter_by(id=epic_id, organization_id=current_user.organization_id).first_or_404()
        
        # Check if user has permission (epic creator, manager, director, admin)
        if (epic.creator_id != current_user.id and 
            current_user.role not in [RoleEnum.Admin, RoleEnum.Manager, RoleEnum.Director]):
            flash('You do not have permission to reset this epic', 'error')
            return redirect(url_for('business.refine_stories_page', id=epic.case_id))
        
        # Only allow reset from Rejected or Submitted status
        if epic.status not in ['Rejected', 'Submitted']:
            flash(f'Epic cannot be reset - current status is {epic.status}', 'warning')
            return redirect(url_for('business.refine_stories_page', id=epic.case_id))
        
        previous_status = epic.status
        epic.status = 'Draft'
        epic.updated_at = datetime.utcnow()
        
        # Add reset comment
        reset_comment = f"[Reset to Draft from {previous_status} by {current_user.first_name} {current_user.last_name} on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}]"
        if epic.comments:
            epic.comments += f"\n\n{reset_comment}"
        else:
            epic.comments = reset_comment
            
        db.session.commit()
        
        flash(f'Epic "{epic.title}" has been reset to Draft status', 'success')
        return redirect(url_for('business.refine_stories_page', id=epic.case_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting epic: {str(e)}', 'error')
        return redirect(url_for('business.refine_stories_page', id=epic.case_id))

# Epic Comment Routes
@business_bp.route('/epic/<int:epic_id>/comment', methods=['POST'])
@login_required
def add_epic_comment(epic_id):
    """Add comment to epic"""
    try:
        epic = Epic.query.filter_by(id=epic_id, organization_id=current_user.organization_id).first_or_404()
        message = request.form.get('message', '').strip()
        
        if not message:
            flash('Comment message is required', 'error')
            return redirect(url_for('business.refine_stories_page', id=epic.case_id))
        
        # Create author name from current user
        author = f"{current_user.first_name} {current_user.last_name}" if current_user.first_name else current_user.email
        
        comment = EpicComment(
            epic_id=epic_id,
            author=author,
            message=message
        )
        
        db.session.add(comment)
        db.session.commit()
        
        flash(f'Comment added to epic "{epic.title}"', 'success')
        return redirect(url_for('business.refine_stories_page', id=epic.case_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding comment: {str(e)}', 'error')
        return redirect(url_for('business.refine_stories_page', id=epic.case_id))

@business_bp.route('/api/epic/<int:epic_id>/comments')
@login_required
def get_epic_comments(epic_id):
    """Get comments for an epic"""
    try:
        comments = EpicComment.query.filter_by(epic_id=epic_id).order_by(EpicComment.timestamp.asc()).all()
        return jsonify({
            'success': True,
            'comments': [comment.to_dict() for comment in comments]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@business_bp.route('/cases/<int:case_id>/epics/submit-all', methods=['POST'])
@login_required
def submit_all_draft_epics(case_id):
    """Submit all draft epics in a business case for review"""
    try:
        business_case = BusinessCase.query.filter_by(id=case_id, organization_id=current_user.organization_id).first_or_404()
        
        # Check if user has permission to submit epics
        if current_user.role.value not in ['Admin', 'Manager', 'Director', 'BA']:
            flash('You do not have permission to submit epics', 'error')
            return redirect(url_for('business.refine_stories_page', id=case_id))
        
        # Get all draft epics for this business case
        draft_epics = Epic.query.filter_by(case_id=case_id, status='Draft', organization_id=current_user.organization_id).all()
        
        if not draft_epics:
            flash('No draft epics found to submit', 'warning')
            return redirect(url_for('business.refine_stories_page', id=case_id))
        
        # Submit all draft epics
        submitted_count = 0
        for epic in draft_epics:
            # Check if user has permission to submit this specific epic
            if epic.creator_id == current_user.id or current_user.role.value in ['Admin', 'Manager', 'Director', 'BA']:
                epic.status = 'Submitted'
                epic.updated_at = datetime.utcnow()
                submitted_count += 1
                print(f"✅ Bulk Submit - Epic {epic.id} '{epic.title}' status updated to Submitted")
        
        db.session.commit()
        
        if submitted_count > 0:
            flash(f'Successfully submitted {submitted_count} epic(s) for review', 'success')
        else:
            flash('No epics were submitted (permission issues)', 'warning')
        
        return redirect(url_for('business.refine_stories_page', id=case_id))
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in bulk submit: {str(e)}")
        flash(f'Error submitting epics: {str(e)}', 'error')
        return redirect(url_for('business.refine_stories_page', id=case_id))

@business_bp.route('/cases/<int:case_id>/link-to-project/<int:project_id>', methods=['POST'])
@login_required
def link_case_to_project(case_id, project_id):
    """Link a business case to a project and sync all epics"""
    try:
        # Check permissions (Admin, Manager, Director can link cases to projects)
        if current_user.role.value not in ['Admin', 'Manager', 'Director']:
            flash('You do not have permission to link business cases to projects', 'error')
            return redirect(url_for('business.view_case', id=case_id))
        
        business_case = BusinessCase.query.filter_by(id=case_id, organization_id=current_user.organization_id).first_or_404()
        project = Project.query.filter_by(id=project_id, organization_id=current_user.organization_id).first_or_404()
        
        # Link business case to project
        business_case.project_id = project_id
        business_case.updated_at = datetime.utcnow()
        
        # If business case is approved, sync all epics to the project
        if business_case.status.value == 'Approved':
            linked_count = sync_epics_to_project(case_id, project_id)
            db.session.commit()
            
            flash(f'Business case linked to project "{project.name}" and {linked_count} epic(s) automatically linked', 'success')
        else:
            db.session.commit()
            flash(f'Business case linked to project "{project.name}". Epics will be auto-linked when case is approved.', 'info')
        
        return redirect(url_for('business.view_case', id=case_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error linking business case to project: {str(e)}', 'error')
        return redirect(url_for('business.view_case', id=case_id))

@business_bp.route('/test-auto-link-epics')
@login_required
def test_auto_link_epics():
    """Test route to demonstrate auto-linking epics to projects"""
    try:
        # Test with Business Case 26 and Project 15
        case_id = 26
        project_id = 15
        
        business_case = BusinessCase.query.filter_by(id=case_id, organization_id=current_user.organization_id).first()
        project = Project.query.filter_by(id=project_id, organization_id=current_user.organization_id).first()
        
        if not business_case or not project:
            return jsonify({
                'error': 'Business case 26 or Project 15 not found',
                'case_found': business_case is not None,
                'project_found': project is not None
            })
        
        # Show current state before linking
        epics_before = Epic.query.filter_by(case_id=case_id, organization_id=current_user.organization_id).all()
        unlinked_epics_before = [e for e in epics_before if e.project_id is None]
        
        print(f"🧪 BEFORE AUTO-LINK TEST:")
        print(f"   Business Case: {business_case.title}")
        print(f"   Status: {business_case.status.value}")
        print(f"   Current Project ID: {business_case.project_id}")
        print(f"   Total Epics: {len(epics_before)}")
        print(f"   Unlinked Epics: {len(unlinked_epics_before)}")
        
        # Link business case to project
        business_case.project_id = project_id
        business_case.updated_at = datetime.utcnow()
        
        # Auto-link epics since business case is approved
        linked_count = sync_epics_to_project(case_id, project_id)
        
        # Show state after linking
        epics_after = Epic.query.filter_by(case_id=case_id, organization_id=current_user.organization_id).all()
        linked_epics_after = [e for e in epics_after if e.project_id == project_id]
        
        print(f"🎯 AFTER AUTO-LINK TEST:")
        print(f"   Business Case Project ID: {business_case.project_id}")
        print(f"   Epics Linked to Project: {len(linked_epics_after)}")
        print(f"   Auto-linked Count: {linked_count}")
        
        return jsonify({
            'success': True,
            'business_case': {
                'id': case_id,
                'title': business_case.title,
                'status': business_case.status.value,
                'project_id': business_case.project_id
            },
            'project': {
                'id': project_id,
                'name': project.name
            },
            'before': {
                'total_epics': len(epics_before),
                'unlinked_epics': len(unlinked_epics_before)
            },
            'after': {
                'linked_epics': len(linked_epics_after),
                'auto_linked_count': linked_count
            },
            'message': f'Successfully auto-linked {linked_count} epic(s) to project "{project.name}"'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in auto-link test: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })