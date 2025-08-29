"""
Safe onboarding wizard module - opt-in only, non-invasive
"""
from flask import Blueprint

onboard_bp = Blueprint('onboard', __name__, url_prefix='/onboarding')

from . import routes