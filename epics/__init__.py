"""
Epics Blueprint
Handles epic and story management functionality
"""

from flask import Blueprint

epics_bp = Blueprint('epics', __name__, url_prefix='/epics', template_folder='templates')

from . import routes