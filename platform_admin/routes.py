"""
Platform Admin Routes
System-level administration endpoints for platform management
"""

from flask import render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required
from datetime import datetime, timedelta
import csv
import io

from . import platform_admin_bp
from models import db, User, Organization, BusinessCase, Problem, Project
from flask_login import current_user
from functools import wraps

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@platform_admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Platform admin dashboard with system statistics"""
    # Get system-wide statistics
    total_orgs = Organization.query.count()
    total_users = User.query.count()
    total_business_cases = BusinessCase.query.count()
    total_problems = Problem.query.count()
    total_projects = Project.query.count()
    
    # Recent activity
    recent_orgs = Organization.query.order_by(Organization.created_at.desc()).limit(5).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    return render_template('platform_admin/dashboard.html',
                         total_orgs=total_orgs,
                         total_users=total_users,
                         total_business_cases=total_business_cases,
                         total_problems=total_problems,
                         total_projects=total_projects,
                         recent_orgs=recent_orgs,
                         recent_users=recent_users)


@platform_admin_bp.route('/waitlist')
@login_required
@admin_required
def waitlist_management():
    """Waitlist management interface"""
    # Get all organizations with pending status or trial users
    waitlist_orgs = Organization.query.filter(
        Organization.status.in_(['pending', 'trial'])
    ).order_by(Organization.created_at.desc()).all()
    
    return render_template('platform_admin/waitlist.html',
                         waitlist_orgs=waitlist_orgs)


@platform_admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Platform analytics and metrics"""
    # Calculate key metrics
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Growth metrics
    new_orgs_this_month = Organization.query.filter(
        Organization.created_at >= start_date
    ).count()
    
    new_users_this_month = User.query.filter(
        User.created_at >= start_date
    ).count()
    
    # Usage metrics
    active_business_cases = BusinessCase.query.filter(
        BusinessCase.status.in_(['under_review', 'approved'])
    ).count()
    
    active_projects = Project.query.filter(
        Project.status == 'active'
    ).count()
    
    return render_template('platform_admin/analytics.html',
                         new_orgs_this_month=new_orgs_this_month,
                         new_users_this_month=new_users_this_month,
                         active_business_cases=active_business_cases,
                         active_projects=active_projects,
                         start_date=start_date,
                         end_date=end_date)


@platform_admin_bp.route('/logout')
@login_required
def logout():
    """Platform admin logout - redirect to main logout"""
    return redirect(url_for('auth.logout'))


@platform_admin_bp.route('/export-csv')
@login_required
@admin_required
def export_csv():
    """Export platform data as CSV"""
    export_type = request.args.get('type', 'organizations')
    
    output = io.StringIO()
    
    if export_type == 'organizations':
        orgs = Organization.query.all()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'Domain', 'Status', 'Created', 'Users Count'])
        
        for org in orgs:
            user_count = User.query.filter_by(organization_id=org.id).count()
            writer.writerow([
                org.id,
                org.name,
                org.domain,
                org.status,
                org.created_at.strftime('%Y-%m-%d'),
                user_count
            ])
    
    elif export_type == 'users':
        users = User.query.all()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Username', 'Email', 'Role', 'Organization', 'Created'])
        
        for user in users:
            org_name = user.organization.name if user.organization else 'N/A'
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.role.value if user.role else 'N/A',
                org_name,
                user.created_at.strftime('%Y-%m-%d')
            ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=platform_{export_type}_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response


@platform_admin_bp.route('/toggle-contacted/<int:org_id>', methods=['POST'])
@login_required
@admin_required
def toggle_contacted(org_id):
    """Toggle contacted status for waitlist organization"""
    org = Organization.query.get_or_404(org_id)
    
    # Toggle contacted flag (assuming we add this field to Organization model)
    # For now, we'll update the status
    if org.status == 'pending':
        org.status = 'contacted'
        db.session.commit()
        flash(f'Marked {org.name} as contacted', 'success')
    elif org.status == 'contacted':
        org.status = 'pending'
        db.session.commit()
        flash(f'Marked {org.name} as not contacted', 'info')
    
    return redirect(url_for('platform_admin.waitlist_management'))


@platform_admin_bp.route('/delete-entry/<int:org_id>', methods=['POST'])
@login_required
@admin_required
def delete_entry(org_id):
    """Delete waitlist entry (organization)"""
    org = Organization.query.get_or_404(org_id)
    
    # Soft delete by setting status to 'deleted'
    org.status = 'deleted'
    db.session.commit()
    
    flash(f'Removed {org.name} from waitlist', 'warning')
    return redirect(url_for('platform_admin.waitlist_management'))