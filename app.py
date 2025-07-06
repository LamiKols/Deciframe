# This is a compatibility layer to provide database objects without circular imports
# All blueprints expect to import from 'app' but the main app is now in app_new.py

import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Create shared database instance that can be imported without circular dependencies
db = SQLAlchemy(model_class=Base)

# Create shared login manager instance
login_manager = LoginManager()

# These will be configured when the actual app is created in app_new.py
__all__ = ['db', 'login_manager']