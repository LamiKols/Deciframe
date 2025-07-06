from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Department
from dept.forms import DepartmentForm

dept = Blueprint('dept', __name__, template_folder='templates')

@dept.route('/', methods=['GET'])
@login_required
def index():
    deps = Department.query.order_by(Department.level, Department.name).all()
    return render_template('departments.html', departments=deps, user=current_user, logged_in=True)

@dept.route('/new', methods=['GET','POST'])
@login_required
def create():
    # Load only parents with level < 5
    form = DepartmentForm()
    form.parent.choices = [(0, '— Top Level —')] + [
        (d.id, f"{'—' * (d.level-1)} {d.name}") for d in Department.query.filter(Department.level < 5).all()
    ]
    
    if form.validate_on_submit():
        parent = Department.query.get(form.parent.data) if form.parent.data != 0 else None
        level = parent.level + 1 if parent else 1
        if level > 5:
            flash("Cannot exceed 5 levels", "danger")
        else:
            dep = Department(name=form.name.data, parent=parent, level=level)
            db.session.add(dep)
            db.session.commit()
            flash("Department created", "success")
            return redirect(url_for('dept.index'))
    return render_template('department_form.html', form=form)

@dept.route('/<int:id>/edit', methods=['GET','POST'])
@login_required
def edit(id):
    dep = Department.query.get_or_404(id)
    form = DepartmentForm(obj=dep)
    # Set the current parent value for the form
    if dep.parent:
        form.parent.data = dep.parent.id
    else:
        form.parent.data = 0
    
    form.parent.choices = [(0, '— Top Level —')] + [
        (d.id, f"{'—' * (d.level-1)} {d.name}") for d in Department.query.filter(Department.id != id, Department.level < 5).all()
    ]
    if form.validate_on_submit():
        parent = Department.query.get(form.parent.data) if form.parent.data != 0 else None
        dep.name = form.name.data
        dep.parent = parent
        dep.level = parent.level + 1 if parent else 1
        db.session.commit()
        flash("Department updated", "success")
        return redirect(url_for('dept.index'))
    return render_template('department_form.html', form=form)

@dept.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    dep = Department.query.get_or_404(id)
    db.session.delete(dep)
    db.session.commit()
    flash("Department deleted", "success")
    return redirect(url_for('dept.index'))