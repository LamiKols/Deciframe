"""
Platform Admin Blueprint
Provides system-level administration features for platform management
"""

from flask import Blueprint

platform_admin_bp = Blueprint('platform_admin', __name__, url_prefix='/platform-admin', template_folder='templates')

from . import routes