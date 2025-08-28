"""
Data Management Routes
Handles data export, import, and retention functionality
"""

from flask import render_template, request, jsonify, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import csv
import io

from . import data_management_bp
from models import db, User, BusinessCase, Problem, Project, Organization
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


@data_management_bp.route('/export')
@login_required
@admin_required
def export_data():
    """Data export interface"""
    export_type = request.args.get('type', 'business_cases')
    format_type = request.args.get('format', 'csv')
    
    if format_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        if export_type == 'business_cases':
            cases = BusinessCase.query.filter_by(
                organization_id=current_user.organization_id
            ).all()
            
            writer.writerow(['ID', 'Title', 'Status', 'Created', 'Updated', 'Owner'])
            for case in cases:
                writer.writerow([
                    case.id,
                    case.title,
                    case.status,
                    case.created_at.strftime('%Y-%m-%d'),
                    case.updated_at.strftime('%Y-%m-%d'),
                    case.user.username if case.user else 'N/A'
                ])
        
        elif export_type == 'problems':
            problems = Problem.query.filter_by(
                organization_id=current_user.organization_id
            ).all()
            
            writer.writerow(['ID', 'Title', 'Status', 'Classification', 'Created', 'Reporter'])
            for problem in problems:
                writer.writerow([
                    problem.id,
                    problem.title,
                    problem.status,
                    problem.classification,
                    problem.created_at.strftime('%Y-%m-%d'),
                    problem.user.username if problem.user else 'N/A'
                ])
        
        elif export_type == 'projects':
            projects = Project.query.filter_by(
                organization_id=current_user.organization_id
            ).all()
            
            writer.writerow(['ID', 'Name', 'Status', 'Progress', 'Created', 'Owner'])
            for project in projects:
                writer.writerow([
                    project.id,
                    project.name,
                    project.status,
                    f"{project.progress}%" if project.progress else '0%',
                    project.created_at.strftime('%Y-%m-%d'),
                    project.user.username if project.user else 'N/A'
                ])
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={export_type}_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
    
    # Default: show export interface
    return render_template('admin/data_management/export.html')


@data_management_bp.route('/retention')
@login_required
@admin_required
def data_retention_page():
    """Data retention management page"""
    # Calculate data age statistics
    cutoff_date = datetime.utcnow() - timedelta(days=365)  # 1 year old
    
    old_data_stats = {
        'business_cases': BusinessCase.query.filter(
            BusinessCase.organization_id == current_user.organization_id,
            BusinessCase.created_at < cutoff_date
        ).count(),
        'problems': Problem.query.filter(
            Problem.organization_id == current_user.organization_id,
            Problem.created_at < cutoff_date
        ).count(),
        'projects': Project.query.filter(
            Project.organization_id == current_user.organization_id,
            Project.created_at < cutoff_date
        ).count()
    }
    
    return render_template('admin/data_management/retention.html',
                         old_data_stats=old_data_stats,
                         cutoff_date=cutoff_date)


@data_management_bp.route('/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_old_data():
    """Clean up old data based on retention policy"""
    days = request.form.get('retention_days', 365, type=int)
    data_type = request.form.get('data_type', 'all')
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    cleaned_count = 0
    
    if data_type in ['all', 'business_cases']:
        old_cases = BusinessCase.query.filter(
            BusinessCase.organization_id == current_user.organization_id,
            BusinessCase.created_at < cutoff_date,
            BusinessCase.status.in_(['rejected', 'cancelled'])
        ).all()
        
        for case in old_cases:
            db.session.delete(case)
            cleaned_count += 1
    
    if data_type in ['all', 'problems']:
        old_problems = Problem.query.filter(
            Problem.organization_id == current_user.organization_id,
            Problem.created_at < cutoff_date,
            Problem.status.in_(['resolved', 'closed'])
        ).all()
        
        for problem in old_problems:
            db.session.delete(problem)
            cleaned_count += 1
    
    db.session.commit()
    
    flash(f'Cleaned up {cleaned_count} old records', 'success')
    return redirect(url_for('data_management.data_retention_page'))


@data_management_bp.route('/import')
@login_required
@admin_required
def import_data():
    """Data import interface"""
    return render_template('admin/data_management/import.html')