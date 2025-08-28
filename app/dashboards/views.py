from flask import render_template, request, abort, jsonify
from flask_login import login_required, current_user
from . import exec_dash_bp
from app.flags import is_enabled

@exec_dash_bp.route("/executive", methods=["GET"])
@login_required
def executive_dashboard():
    """Executive dashboard with role-based access control"""
    
    # Check feature flag
    if not is_enabled("FEATURE_EXEC_DASHBOARD", default=True):
        abort(404, "Executive dashboard is not available")
    
    # Check role access
    if current_user.role not in ['admin', 'ceo', 'director']:
        abort(403, "Executive access required")
    
    org_id = current_user.organization_id
    
    return render_template(
        "dashboards/executive_dashboard.html", 
        org_id=org_id,
        user_role=current_user.role,
        organization_name=getattr(current_user.organization, 'name', f'Organization {org_id}')
    )

@exec_dash_bp.route("/executive/print", methods=["GET"])
@login_required
def executive_print_view():
    """Print-optimized version of executive dashboard"""
    
    if not is_enabled("FEATURE_EXEC_DASHBOARD", default=True):
        abort(404)
    
    if current_user.role not in ['admin', 'ceo', 'director']:
        abort(403)
    
    org_id = current_user.organization_id
    
    return render_template(
        "dashboards/executive_print.html", 
        org_id=org_id,
        user_role=current_user.role,
        organization_name=getattr(current_user.organization, 'name', f'Organization {org_id}')
    )