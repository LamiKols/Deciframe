from flask import Blueprint

exec_dash_bp = Blueprint("exec_dash", __name__, url_prefix="/dashboard")

from .views import *  # noqa