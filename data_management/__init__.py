"""
Data Management Blueprint
Handles data export, import, and retention management
"""

from flask import Blueprint

data_management_bp = Blueprint('data_management', __name__, url_prefix='/data-management', template_folder='templates')

from . import routes