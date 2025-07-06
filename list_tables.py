from app import db
from app import app
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("Tables in the database:", tables)