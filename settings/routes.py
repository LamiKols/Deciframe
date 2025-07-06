"""
Settings routes for user preferences
"""
from flask import request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import settings_bp
from models import db

@settings_bp.route('/theme', methods=['POST'])
@login_required
def update_theme():
    """Update user theme preference via form submission"""
    theme = request.form.get('theme')
    
    print(f"🔧 Theme Update Request: {theme}")
    print(f"🔧 Current User Theme Before: {current_user.theme}")
    
    if theme in ['light', 'dark']:
        current_user.theme = theme
        db.session.commit()
        print(f"🔧 Current User Theme After: {current_user.theme}")
        flash(f'Theme updated to {theme} mode', 'success')
    else:
        flash('Invalid theme selection', 'error')
    
    # Redirect back to the referring page or profile
    return redirect(request.referrer or url_for('auth.profile'))