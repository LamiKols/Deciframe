from flask import Blueprint

metrics_bp = Blueprint("metrics", __name__, url_prefix="/api/metrics")

from .routes import *  # noqa