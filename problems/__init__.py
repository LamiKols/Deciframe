from flask import Blueprint

problems = Blueprint('problems', __name__, template_folder='templates')

from problems import routes