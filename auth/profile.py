"""
User profile management routes
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, User, AuditLog
import logging

logger = logging.getLogger(__name__)


def init_profile_routes(app):
    """Initialize profile routes on the Flask app"""
    
    @app.route('/auth/profile')
    @login_required
    def profile():
        """Display user profile page"""
        try:
            return render_template('auth/profile.html', user=current_user)
        except Exception as e:
            logger.error(f"Error loading profile: {e}")
            flash('Unable to load profile page', 'error')
            return redirect(url_for('index'))
    
    @app.route('/auth/profile/edit', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        """Edit user profile information"""
        if request.method == 'GET':
            return render_template('auth/edit_profile.html', user=current_user)
        
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            timezone = request.form.get('timezone', 'UTC')
            theme = request.form.get('theme', 'light')
            
            # Validation
            if not name or not email:
                flash('Name and email are required', 'error')
                return render_template('auth/edit_profile.html', user=current_user)
            
            # Check if email is already taken by another user
            existing_user = User.query.filter(
                User.email == email,
                User.id != current_user.id,
                User.organization_id == current_user.organization_id
            ).first()
            
            if existing_user:
                flash('Email is already in use by another user', 'error')
                return render_template('auth/edit_profile.html', user=current_user)
            
            # Update user profile
            current_user.name = name
            current_user.email = email
            current_user.timezone = timezone
            current_user.theme = theme
            
            db.session.commit()
            
            # Log the profile update
            audit_log = AuditLog(
                user_id=current_user.id,
                action='UPDATE_PROFILE',
                details=f'Updated profile for {name}',
                ip_address=request.remote_addr,
                organization_id=current_user.organization_id
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Profile updated successfully', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile: {e}")
            flash('Failed to update profile', 'error')
            return render_template('auth/edit_profile.html', user=current_user)
    
    @app.route('/auth/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        """Change user password"""
        if request.method == 'GET':
            return render_template('auth/change_password.html')
        
        try:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validation
            if not current_password or not new_password or not confirm_password:
                flash('All fields are required', 'error')
                return render_template('auth/change_password.html')
            
            # Check current password
            if not check_password_hash(current_user.password_hash, current_password):
                flash('Current password is incorrect', 'error')
                return render_template('auth/change_password.html')
            
            # Check new password confirmation
            if new_password != confirm_password:
                flash('New passwords do not match', 'error')
                return render_template('auth/change_password.html')
            
            # Password strength validation
            if len(new_password) < 8:
                flash('Password must be at least 8 characters long', 'error')
                return render_template('auth/change_password.html')
            
            # Update password
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            # Log the password change
            audit_log = AuditLog(
                user_id=current_user.id,
                action='CHANGE_PASSWORD',
                details='Password changed successfully',
                ip_address=request.remote_addr,
                organization_id=current_user.organization_id
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Password changed successfully', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error changing password: {e}")
            flash('Failed to change password', 'error')
            return render_template('auth/change_password.html')
    
    @app.route('/auth/profile/activity')
    @login_required
    def profile_activity():
        """Show user activity log"""
        try:
            activities = AuditLog.query.filter_by(
                user_id=current_user.id,
                organization_id=current_user.organization_id
            ).order_by(AuditLog.timestamp.desc()).limit(50).all()
            
            return render_template('auth/profile_activity.html', activities=activities)
            
        except Exception as e:
            logger.error(f"Error loading profile activity: {e}")
            flash('Unable to load activity log', 'error')
            return redirect(url_for('auth.profile'))