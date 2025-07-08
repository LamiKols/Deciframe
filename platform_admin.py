"""
DeciFrame Platform Admin Interface
Secure admin interface for DeciFrame platform staff to manage global waitlist
This is NOT visible to client organizations or their admins
"""

import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session, abort
from functools import wraps
from models import Waitlist, db
import csv
from io import StringIO

platform_admin_bp = Blueprint('platform_admin', __name__, url_prefix='/platform-admin')

# Platform admin credentials (environment-based for security)
PLATFORM_ADMIN_USERNAME = os.getenv('PLATFORM_ADMIN_USERNAME', 'deciframe_admin')
PLATFORM_ADMIN_PASSWORD = os.getenv('PLATFORM_ADMIN_PASSWORD', 'secure_platform_key_2025')

def platform_admin_required(f):
    """Decorator to require platform admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('platform_admin_authenticated'):
            return redirect(url_for('platform_admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@platform_admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Platform admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == PLATFORM_ADMIN_USERNAME and password == PLATFORM_ADMIN_PASSWORD:
            session['platform_admin_authenticated'] = True
            session['platform_admin_login_time'] = datetime.utcnow().isoformat()
            flash('Successfully logged in to Platform Admin', 'success')
            return redirect(url_for('platform_admin.dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('platform_admin/login.html')

@platform_admin_bp.route('/logout')
@platform_admin_required
def logout():
    """Platform admin logout"""
    session.pop('platform_admin_authenticated', None)
    session.pop('platform_admin_login_time', None)
    flash('Successfully logged out', 'info')
    return redirect(url_for('platform_admin.login'))

@platform_admin_bp.route('/')
@platform_admin_bp.route('/dashboard')
@platform_admin_required
def dashboard():
    """Platform admin dashboard showing waitlist overview"""
    # Get waitlist statistics
    total_entries = Waitlist.query.count()
    contacted_entries = Waitlist.query.filter_by(contacted=True).count()
    uncontacted_entries = total_entries - contacted_entries
    
    # Recent signups (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_signups = Waitlist.query.filter(Waitlist.created_at >= seven_days_ago).count()
    
    # Top companies by signup count
    top_companies_raw = db.session.query(
        Waitlist.company, 
        db.func.count(Waitlist.id).label('count')
    ).filter(
        Waitlist.company.isnot(None),
        Waitlist.company != ''
    ).group_by(Waitlist.company).order_by(
        db.func.count(Waitlist.id).desc()
    ).limit(10).all()
    
    # Convert to JSON-serializable format
    top_companies = [{'company': row.company, 'signups': row.count} for row in top_companies_raw]
    
    # Role distribution
    role_distribution_raw = db.session.query(
        Waitlist.role,
        db.func.count(Waitlist.id).label('count')
    ).filter(
        Waitlist.role.isnot(None),
        Waitlist.role != ''
    ).group_by(Waitlist.role).order_by(
        db.func.count(Waitlist.id).desc()
    ).all()
    
    # Convert to JSON-serializable format
    role_distribution = [[row.role, row.count] for row in role_distribution_raw]
    
    # Company size distribution
    size_distribution_raw = db.session.query(
        Waitlist.company_size,
        db.func.count(Waitlist.id).label('count')
    ).filter(
        Waitlist.company_size.isnot(None),
        Waitlist.company_size != ''
    ).group_by(Waitlist.company_size).order_by(
        db.func.count(Waitlist.id).desc()
    ).all()
    
    # Convert to JSON-serializable format
    size_distribution = [[row.company_size, row.count] for row in size_distribution_raw]
    
    return render_template('platform_admin/dashboard.html',
                         total_entries=total_entries,
                         contacted_entries=contacted_entries,
                         uncontacted_entries=uncontacted_entries,
                         recent_signups=recent_signups,
                         top_companies=top_companies,
                         role_distribution=role_distribution,
                         size_distribution=size_distribution)

@platform_admin_bp.route('/waitlist')
@platform_admin_required
def waitlist_management():
    """Comprehensive waitlist management interface"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    # Filters
    search = request.args.get('search', '').strip()
    contacted_filter = request.args.get('contacted')
    role_filter = request.args.get('role')
    company_size_filter = request.args.get('company_size')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Build query
    query = Waitlist.query
    
    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Waitlist.first_name.ilike(search_term),
                Waitlist.last_name.ilike(search_term),
                Waitlist.email.ilike(search_term),
                Waitlist.company.ilike(search_term),
                Waitlist.use_case.ilike(search_term)
            )
        )
    
    # Contacted filter
    if contacted_filter == 'contacted':
        query = query.filter_by(contacted=True)
    elif contacted_filter == 'uncontacted':
        query = query.filter_by(contacted=False)
    
    # Role filter
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    # Company size filter
    if company_size_filter:
        query = query.filter_by(company_size=company_size_filter)
    
    # Date range filter
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Waitlist.created_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Waitlist.created_at < date_to_obj)
        except ValueError:
            pass
    
    # Order by most recent first
    query = query.order_by(Waitlist.created_at.desc())
    
    # Paginate
    entries = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get filter options
    all_roles = db.session.query(Waitlist.role).filter(
        Waitlist.role.isnot(None), Waitlist.role != ''
    ).distinct().all()
    all_company_sizes = db.session.query(Waitlist.company_size).filter(
        Waitlist.company_size.isnot(None), Waitlist.company_size != ''
    ).distinct().all()
    
    return render_template('platform_admin/waitlist.html',
                         entries=entries,
                         search=search,
                         contacted_filter=contacted_filter,
                         role_filter=role_filter,
                         company_size_filter=company_size_filter,
                         date_from=date_from,
                         date_to=date_to,
                         all_roles=[r[0] for r in all_roles],
                         all_company_sizes=[cs[0] for cs in all_company_sizes])

@platform_admin_bp.route('/waitlist/<int:entry_id>/toggle-contacted', methods=['POST'])
@platform_admin_required
def toggle_contacted(entry_id):
    """Toggle contacted status for a waitlist entry"""
    entry = Waitlist.query.get_or_404(entry_id)
    
    entry.contacted = not entry.contacted
    if entry.contacted:
        entry.contacted_at = datetime.utcnow()
    else:
        entry.contacted_at = None
        entry.contacted_by = None
    
    db.session.commit()
    
    status = "contacted" if entry.contacted else "uncontacted"
    flash(f'Entry marked as {status}', 'success')
    
    return redirect(url_for('platform_admin.waitlist_management'))

@platform_admin_bp.route('/waitlist/<int:entry_id>/delete', methods=['POST'])
@platform_admin_required
def delete_entry(entry_id):
    """Delete a waitlist entry (use with caution)"""
    entry = Waitlist.query.get_or_404(entry_id)
    
    name = entry.full_name
    email = entry.email
    
    db.session.delete(entry)
    db.session.commit()
    
    flash(f'Deleted waitlist entry: {name} ({email})', 'warning')
    return redirect(url_for('platform_admin.waitlist_management'))

@platform_admin_bp.route('/export/csv')
@platform_admin_required
def export_csv():
    """Export waitlist data as CSV"""
    # Get all entries
    entries = Waitlist.query.order_by(Waitlist.created_at.desc()).all()
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'First Name', 'Last Name', 'Email', 'Company', 'Role', 
        'Company Size', 'Use Case', 'Created At', 'Contacted', 
        'Contacted At', 'IP Address'
    ])
    
    # Write data
    for entry in entries:
        writer.writerow([
            entry.id,
            entry.first_name,
            entry.last_name,
            entry.email,
            entry.company or '',
            entry.role or '',
            entry.company_size or '',
            entry.use_case or '',
            entry.created_at.strftime('%Y-%m-%d %H:%M:%S') if entry.created_at else '',
            'Yes' if entry.contacted else 'No',
            entry.contacted_at.strftime('%Y-%m-%d %H:%M:%S') if entry.contacted_at else '',
            entry.ip_address or ''
        ])
    
    # Prepare response
    csv_content = output.getvalue()
    output.close()
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f'deciframe_waitlist_{timestamp}.csv'
    
    response = jsonify({
        'csv_content': csv_content,
        'filename': filename
    })
    response.headers['Content-Type'] = 'application/json'
    
    return response

@platform_admin_bp.route('/analytics')
@platform_admin_required
def analytics():
    """Advanced analytics for waitlist data"""
    # Time-based analytics
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Daily signups for last 30 days
    daily_signups_raw = db.session.query(
        db.func.date(Waitlist.created_at).label('date'),
        db.func.count(Waitlist.id).label('count')
    ).filter(
        Waitlist.created_at >= thirty_days_ago
    ).group_by(
        db.func.date(Waitlist.created_at)
    ).order_by(
        db.func.date(Waitlist.created_at)
    ).all()
    
    # Convert to JSON-serializable format
    daily_signups = [{'date': str(row.date), 'count': row.count} for row in daily_signups_raw]
    
    # Conversion metrics
    total_entries = Waitlist.query.count()
    contacted_rate = (Waitlist.query.filter_by(contacted=True).count() / total_entries * 100) if total_entries > 0 else 0
    
    # Geographic analysis (by company)
    company_analysis_raw = db.session.query(
        Waitlist.company,
        db.func.count(Waitlist.id).label('signups'),
        db.func.sum(db.case((Waitlist.contacted == True, 1), else_=0)).label('contacted')
    ).filter(
        Waitlist.company.isnot(None),
        Waitlist.company != ''
    ).group_by(Waitlist.company).having(
        db.func.count(Waitlist.id) > 0
    ).order_by(
        db.func.count(Waitlist.id).desc()
    ).all()
    
    # Convert to JSON-serializable format
    company_analysis = [{'company': row.company, 'signups': row.signups, 'contacted': row.contacted or 0} for row in company_analysis_raw]
    
    return render_template('platform_admin/analytics.html',
                         daily_signups=daily_signups,
                         contacted_rate=contacted_rate,
                         company_analysis=company_analysis,
                         total_entries=total_entries)