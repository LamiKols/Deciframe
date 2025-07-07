"""
Predict Blueprint - ML-powered Project Success Forecasting
"""
from flask import Blueprint

predict_bp = Blueprint('predict', __name__, url_prefix='/predict')

from . import routes