"""
Public Blueprint - Terms, Privacy, and Public Pages
"""
from flask import Blueprint

bp = Blueprint('public', __name__, url_prefix='/public')

from public import routes