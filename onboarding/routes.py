"""
Safe onboarding wizard routes - NO automatic redirects
"""
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from onboarding import onboard_bp
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
from flags import is_enabled

@onboard_bp.route('/step1')
@login_required
def step1_org_setup():
    """First step of onboarding wizard - organizational setup"""
    
    # Safety check: only proceed if flag is enabled
    if not is_enabled("ENABLE_ONBOARDING_FLOW", default=False):
        flash("Onboarding wizard is currently unavailable.", "warning")
        return redirect(url_for('index'))
    
    # Role check: only admins can access onboarding
    if current_user.role not in ['admin', 'ceo', 'director']:
        flash("Only organization administrators can access the setup wizard.", "warning")
        return redirect(url_for('index'))
    
    return render_template('onboarding/step1.html', 
                           title="Organization Setup",
                           user=current_user)

@onboard_bp.route('/step2')
@login_required
def step2_departments():
    """Second step - department structure"""
    
    if not is_enabled("ENABLE_ONBOARDING_FLOW", default=False):
        return redirect(url_for('index'))
    
    if current_user.role not in ['admin', 'ceo', 'director']:
        return redirect(url_for('index'))
    
    return render_template('onboarding/step2.html',
                           title="Department Setup",
                           user=current_user)

@onboard_bp.route('/step3')
@login_required
def step3_workflows():
    """Third step - workflow configuration"""
    
    if not is_enabled("ENABLE_ONBOARDING_FLOW", default=False):
        return redirect(url_for('index'))
    
    if current_user.role not in ['admin', 'ceo', 'director']:
        return redirect(url_for('index'))
    
    return render_template('onboarding/step3.html',
                           title="Workflow Setup",
                           user=current_user)

@onboard_bp.route('/complete')
@login_required
def complete():
    """Onboarding completion - mark as done and redirect to dashboard"""
    
    if not is_enabled("ENABLE_ONBOARDING_FLOW", default=False):
        return redirect(url_for('index'))
    
    # Mark onboarding as complete in session (internal to onboarding only)
    session['onboarding_complete'] = True
    
    flash("Welcome to DeciFrame! Your organization setup is complete.", "success")
    
    # Safe redirect back to main dashboard
    return redirect(url_for('index'))