from flask import Blueprint

# Create auth blueprint with explicit template folder path
bp = Blueprint('auth', __name__, 
               template_folder='templates',
               static_folder='static',
               static_url_path='/auth/static')

from . import routes
