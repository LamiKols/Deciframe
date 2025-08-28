"""
Test configuration and fixtures for DeciFrame Flask app
"""

import pytest
import os
from datetime import datetime

# Import app creation function
try:
    from app import create_app
except ImportError:
    from app import app as create_app

from models import db, User, Problem, BusinessCase, Project, Notification, RoleEnum, StatusEnum


@pytest.fixture
def app():
    """Create and configure a test application."""
    # Set testing environment variables
    os.environ['TESTING'] = 'true'
    os.environ['WTF_CSRF_ENABLED'] = 'false'
    
    # Create test app
    if callable(create_app):
        test_app = create_app()
    else:
        test_app = create_app
        
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'MAIL_SUPPRESS_SEND': True,
        'STRIPE_PUBLISHABLE_KEY': 'test_key',
        'STRIPE_SECRET_KEY': 'test_key',
    })
    
    return test_app


@pytest.fixture
def db_session(app):
    """Create a database session for testing."""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    user = User(
        email='admin@test.com',
        name='Test Admin',
        role=RoleEnum.Admin,
        organization_id=1,
        department_id=1,
        is_active=True,
        onboarded=True
    )
    user.set_password('test123')
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture
def regular_user(db_session):
    """Create a regular user for testing."""
    user = User(
        email='user@test.com',
        name='Test User',
        role=RoleEnum.Staff,
        organization_id=1,
        department_id=1,
        is_active=True,
        onboarded=True
    )
    user.set_password('test123')
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture
def sample_problem(db_session, regular_user):
    """Create a sample problem for testing."""
    problem = Problem(
        title='Test Problem',
        description='Test problem description',
        priority='High',
        status='Open',
        submitter_id=regular_user.id,
        organization_id=1,
        department_id=1,
        created_at=datetime.utcnow()
    )
    db_session.session.add(problem)
    db_session.session.commit()
    return problem


@pytest.fixture
def sample_business_case(db_session, regular_user):
    """Create a sample business case for testing."""
    case = BusinessCase(
        title='Test Business Case',
        description='Test case description',
        cost_estimate=50000,
        benefit_estimate=100000,
        roi=100.0,
        status=StatusEnum.Submitted,
        created_by_id=regular_user.id,
        organization_id=1,
        department_id=1,
        created_at=datetime.utcnow()
    )
    db_session.session.add(case)
    db_session.session.commit()
    return case


@pytest.fixture
def sample_project(db_session, regular_user, sample_business_case):
    """Create a sample project for testing."""
    project = Project(
        name='Test Project',
        description='Test project description',
        budget=75000,
        status='In_Progress',
        project_manager_id=regular_user.id,
        business_case_id=sample_business_case.id,
        organization_id=1,
        department_id=1,
        created_at=datetime.utcnow()
    )
    db_session.session.add(project)
    db_session.session.commit()
    return project


@pytest.fixture
def sample_notification(db_session, regular_user):
    """Create a sample notification for testing."""
    notification = Notification(
        user_id=regular_user.id,
        title='Test Notification',
        message='Test notification message',
        type='info',
        read=False,
        organization_id=1,
        created_at=datetime.utcnow()
    )
    db_session.session.add(notification)
    db_session.session.commit()
    return notification


def login(client, email='admin@test.com', password='test123'):
    """Helper function to log in a user."""
    return client.post('/auth/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)


def logout(client):
    """Helper function to log out a user."""
    return client.get('/auth/logout', follow_redirects=True)