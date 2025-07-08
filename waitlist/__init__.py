"""
Waitlist Blueprint for DeciFrame
Handles landing page waitlist signups and management
"""

from flask import Blueprint

waitlist_bp = Blueprint('waitlist', __name__, url_prefix='/waitlist')

from . import routes