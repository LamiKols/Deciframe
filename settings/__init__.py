"""
Settings blueprint for user preferences
"""
from flask import Blueprint

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

from . import routes  # noqa: F401, E402