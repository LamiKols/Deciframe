"""
Public Routes - Terms of Use, Privacy Policy, and Other Public Pages
"""
from flask import render_template
from public import bp

@bp.route('/terms')
def terms():
    """Terms of Use page"""
    return render_template('public/terms.html')

@bp.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('public/privacy.html')