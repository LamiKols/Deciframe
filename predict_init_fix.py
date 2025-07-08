"""
Fix for predict module - Missing __init__.py file
"""

# predict/__init__.py content that needs to be created
PREDICT_INIT_CONTENT = '''"""
Predict Blueprint - ML-powered Project Success Forecasting
"""
from flask import Blueprint

predict_bp = Blueprint('predict', __name__, url_prefix='/predict')

from . import routes
'''

print("Missing predict/__init__.py file needs to be created with:")
print(PREDICT_INIT_CONTENT)
print("\nThis will resolve the predict module import in app.py line 474")