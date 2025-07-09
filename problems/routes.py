from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app import db
from models import Problem, PriorityEnum, StatusEnum, Department, OrgUnit
from problems.forms import ProblemForm, ProblemFilterForm
from flask_login import login_required, current_user
from auth.session_auth import require_session_auth

problems = Blueprint('problems', __name__, template_folder='templates')
# Create alias for blueprint registration
problems_bp = problems

@problems.route('/')
@login_required
def index():
    """List all problems with search, filtering, and pagination"""
    from sqlalchemy import or_
    user = current_user
    
    # Get filter parameters
    q = request.args.get('q', '', type=str)
    department = request.args.get('department', type=int)

    status = request.args.get('status', type=str)
    page = request.args.get('page', 1, type=int)
    
    # Determine allowed departments
    if user.role.value == 'Admin':
        # Admin users can see problems from ALL departments regardless of their assigned department
        allowed = [d.id for d in Department.query.filter_by(organization_id=current_user.organization_id).with_entities(Department.id).all()]
    else:
        # Non-admin users are restricted to their department hierarchy
        own = user.department  # may be None for users without dept assignment
        if own:
            allowed = own.get_descendant_ids(include_self=True)
        else:
            # For users without department assignment (unassigned users)
            # Show all departments in their organization
            allowed = [d.id for d in Department.query.filter_by(organization_id=current_user.organization_id).with_entities(Department.id).all()]
    
    # Add extra departments if user has any
    if hasattr(user, 'extra_departments') and user.extra_departments:
        extras = [d.id for d in user.extra_departments]
        allowed = list(set(allowed + extras))
    
    # Handle department selection from dropdown
    sel = request.args.get('dept', type=int)
    if sel and sel in allowed:
        allowed = [sel]
    
    # Build query with department filtering
    # Include problems with no department (NULL department_id) for admin users or when user has no department
    base_query = Problem.query.filter_by(organization_id=current_user.organization_id)
    
    if user.role.value == 'Admin' or not user.dept_id:
        # Admin users or users without department can see all problems including unassigned ones
        query = base_query.filter(
            (Problem.department_id.in_(allowed)) | (Problem.department_id.is_(None))
        )
    else:
        # Regular users with department assignment see only their department's problems
        query = base_query.filter(Problem.department_id.in_(allowed))
    
    # Text search on title and description
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(Problem.title.ilike(like), Problem.description.ilike(like))
        )
    
    # Additional department filter (user-selected filter within allowed departments)
    if department and department in allowed:
        query = query.filter(Problem.department_id == department)
    

    
    # Status filter
    if status:
        query = query.filter(Problem.status == StatusEnum[status])
    
    # Pagination
    pagination = query.order_by(Problem.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    problems_list = pagination.items
    
    # Get departments for filter dropdown
    # Get departments for filter dropdown (only user's allowed departments within their organization)
    if allowed:
        departments = Department.query.filter(Department.id.in_(allowed)).filter_by(organization_id=current_user.organization_id).order_by(Department.name).all()
    else:
        departments = []
    
    return render_template('problems.html', 
                         problems=problems_list, 
                         pagination=pagination,
                         departments=departments,
                         StatusEnum=StatusEnum,
                         user=user)

@problems.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new problem"""
    user = current_user
    form = ProblemForm()
    
    # Strict department enforcement: users can only create problems for their own department
    # Exception: Admin users can select any department
    if user.role == 'Admin':
        form.department_id.choices = Department.get_hierarchical_choices()
    else:
        # For non-admin users, auto-assign to the General department since org_units != departments
        general_dept = Department.query.filter_by(name='General', organization_id=user.organization_id).first()
        if general_dept:
            form.department_id.choices = [(general_dept.id, general_dept.name)]
            form.department_id.data = general_dept.id
        else:
            # Fallback to any department in the organization
            any_dept = Department.query.filter_by(organization_id=user.organization_id).first()
            if any_dept:
                form.department_id.choices = [(any_dept.id, any_dept.name)]
                form.department_id.data = any_dept.id
            else:
                flash('No departments available. Please contact your administrator.', 'danger')
                return redirect(url_for('problems.index'))
    
    if form.validate_on_submit():
        org_unit_id = form.org_unit_id.data if form.org_unit_id.data != 0 else None
        issue_type = request.form.get('issue_type', 'PROCESS')
        
        # Try to get AI confidence from form if available
        ai_confidence = None
        try:
            if 'ai_confidence' in request.form:
                ai_confidence = float(request.form.get('ai_confidence', 0.0))
        except (ValueError, TypeError):
            ai_confidence = None
        
        # Enforce department assignment: non-admin users can only create for their org unit
        # For admin users, use the selected department_id from the form
        # For non-admin users, use the General department as default since org_units != departments
        if user.role.value == 'Admin':
            department_id = form.department_id.data
        else:
            # Find the General department for this organization or use any available department
            general_dept = Department.query.filter_by(name='General', organization_id=user.organization_id).first()
            if general_dept:
                department_id = general_dept.id
            else:
                # Fallback to any department in the organization
                any_dept = Department.query.filter_by(organization_id=user.organization_id).first()
                department_id = any_dept.id if any_dept else None
        
        # Validate department_id is not None or 0
        if not department_id or department_id == 0:
            flash('No valid department found. Please contact your administrator.', 'danger')
            return render_template('problem_form.html', form=form)
        
        # Generate next available problem code
        def get_next_problem_code():
            from sqlalchemy import text
            # Get the highest existing code number
            result = db.session.execute(
                text("SELECT code FROM problems WHERE code IS NOT NULL AND code LIKE 'P%' ORDER BY code DESC LIMIT 1")
            ).fetchone()
            
            if result and result[0]:
                # Extract number from code like 'P0057' -> 57
                try:
                    latest_num = int(result[0][1:])
                    next_num = latest_num + 1
                except (ValueError, IndexError):
                    next_num = 1
            else:
                next_num = 1
            
            return f"P{next_num:04d}"
        
        prob = Problem(
            title=form.title.data,
            description=form.description.data,
            priority=PriorityEnum[form.priority.data],
            department_id=department_id,
            status=StatusEnum[form.status.data],
            reported_by=user.id,
            created_by=user.id,
            organization_id=user.organization_id,  # Add organization_id for multi-tenant security
            issue_type=issue_type,
            code=get_next_problem_code(),  # Generate code before insert
            ai_confidence=ai_confidence
        )
        db.session.add(prob)
        db.session.commit()
        
        # Trigger workflow events asynchronously
        try:
            from workflows.event_queue import enqueue_workflow_event
            problem_context = {
                'problem': {
                    'id': prob.id,
                    'code': prob.code,
                    'title': prob.title,
                    'description': prob.description,
                    'priority': prob.priority.name,
                    'status': prob.status.name,
                    'created_by': prob.created_by,
                    'dept_id': prob.department_id
                },
                'user_id': user.id,
                'department_id': prob.department_id
            }
            enqueue_workflow_event('problem_created', problem_context)
        except Exception as e:
            # Don't break the user flow if workflow fails
            pass
        
        flash(f"Problem {prob.code} created successfully!", "success")
        return redirect(url_for('problems.view', id=prob.id))
    
    if request.method == 'POST':
        flash(f"Form validation errors: {form.errors}", "danger")
    
    return render_template('problem_form.html', form=form, user=user, action='Create')

@problems.route('/<int:id>')
@login_required
def view(id):
    """View a specific problem"""
    from models import BusinessCase
    user = current_user
    problem = Problem.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    
    # Get related business cases
    related_cases = BusinessCase.query.filter_by(problem_id=problem.id, organization_id=current_user.organization_id).all()
    
    return render_template('problem_detail.html', problem=problem, user=user, related_cases=related_cases)

@problems.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing problem"""
    user = current_user
    problem = Problem.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    form = ProblemForm(obj=problem)
    
    # Strict department enforcement: users can only edit problems for their own department
    # Exception: Admin users can select any department
    if user.role == 'Admin':
        form.department_id.choices = Department.get_hierarchical_choices()
    else:
        # Hide department field for non-admin users - auto-assign their department
        form.department_id.choices = [(user.dept_id, user.department.name if user.department else 'Unknown Department')]
        form.department_id.data = user.dept_id
    
    # Pre-populate form data
    if request.method == 'GET':
        form.priority.data = problem.priority.name
        form.status.data = problem.status.name
        form.department_id.data = getattr(problem, 'department_id', None)
        form.org_unit_id.data = getattr(problem, 'org_unit_id', 0) or 0
    
    if form.validate_on_submit():
        org_unit_id = form.org_unit_id.data if form.org_unit_id.data != 0 else None
        problem.title = form.title.data
        problem.description = form.description.data
        problem.priority = PriorityEnum[form.priority.data]
        problem.department_id = form.department_id.data
        problem.org_unit_id = org_unit_id
        problem.status = StatusEnum[form.status.data]
        
        try:
            db.session.commit()
            flash(f'Problem {problem.code} updated successfully!', 'success')
            return redirect(url_for('problems.view', id=problem.id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating problem. Please try again.', 'danger')
            print(f"Error updating problem: {e}")
    
    return render_template('problem_form.html', form=form, problem=problem, user=user, action='Edit')

@problems.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a problem"""
    problem = Problem.query.filter_by(id=id, organization_id=current_user.organization_id).first_or_404()
    problem_code = problem.code
    
    try:
        db.session.delete(problem)
        db.session.commit()
        flash(f'Problem {problem_code} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting problem. Please try again.', 'danger')
        print(f"Error deleting problem: {e}")
    
    return redirect(url_for('problems.index'))

@problems.route('/api/ai/classify-problem', methods=['POST'])
@login_required
def classify_problem():
    """AI-powered problem classification API endpoint"""
    try:
        data = request.get_json()
        if not data or 'title' not in data or 'description' not in data:
            return jsonify({'error': 'Title and description are required'}), 400
        
        title = data['title'].strip()
        description = data['description'].strip()
        
        if not title or not description:
            return jsonify({'error': 'Title and description cannot be empty'}), 400
        
        # Import the AI classifier
        from ai.problem_classifier import classify_problem as ai_classify, get_classification_explanation
        
        # Get AI classification
        issue_type, confidence = ai_classify(title, description)
        
        return jsonify({
            'issue_type': issue_type,
            'confidence': confidence,
            'explanation': get_classification_explanation(issue_type),
            'confidence_percentage': round(confidence * 100)
        })
        
    except Exception as e:
        print(f"Error in AI problem classification: {e}")
        # Return safe fallback
        return jsonify({
            'issue_type': 'PROCESS',
            'confidence': 0.5,
            'explanation': 'Workflow or procedural issue',
            'confidence_percentage': 50,
            'error': 'AI classification temporarily unavailable'
        }), 200