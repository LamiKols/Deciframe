"""
Dashboard access helper - generates fresh URLs for dashboard access
"""

from app import app, db
from models import User, RoleEnum
from stateless_auth import create_auth_token

def get_dashboard_url():
    """Generate a fresh dashboard URL with authentication token"""
    with app.app_context():
        admin = User.query.filter(User.role.in_([RoleEnum.Admin, RoleEnum.Director, RoleEnum.CEO])).first()
        if admin:
            token = create_auth_token(admin.id)
            return f"http://0.0.0.0:5000/admin/dashboard?auth_token={token}"
        return None

if __name__ == "__main__":
    url = get_dashboard_url()
    if url:
        print(f"Dashboard URL: {url}")
    else:
        print("No admin user found")