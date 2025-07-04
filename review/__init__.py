"""
Review Blueprint for Epic Collaborative Review System
"""
from flask import Blueprint

review_bp = Blueprint('review', __name__, url_prefix='/review', template_folder='templates')

from . import routes