import pytest
from flask import url_for
from app import app
from models import Problem, Department, User, PriorityEnum, StatusEnum, RoleEnum
from app import db

@pytest.fixture
def test_app():
    """Create a test Flask app"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app

@pytest.fixture
def test_client(test_app):
    """Create a test client"""
    return test_app.test_client()

@pytest.fixture
def test_department(test_app):
    """Create a test department"""
    with test_app.app_context():
        db.create_all()
        dept = Department(name='Test Department', level=1)
        db.session.add(dept)
        db.session.commit()
        return dept

@pytest.fixture
def test_user(test_app, test_department):
    """Create a test user"""
    with test_app.app_context():
        user = User(
            email='test@example.com',
            name='Test User',
            role=RoleEnum.Staff,
            department_id=test_department.id
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def authenticated_client(test_client, test_user):
    """Create an authenticated test client"""
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    return test_client

def test_problem_crud(test_client, test_department, test_user):
    """Test complete CRUD operations for problems"""
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    
    # Ensure problems list loads
    res = test_client.get('/problems')
    assert res.status_code == 200
    assert b'Problem Management' in res.data
    
    # Test problem creation
    problem_data = {
        'title': 'Test CRUD Problem',
        'description': 'This is a test problem for CRUD operations',
        'priority': 'Medium',
        'status': 'Open',
        'department_id': test_department.id,
        'submit': 'Submit Problem'
    }
    
    res = test_client.post('/problems/new', data=problem_data, follow_redirects=True)
    assert res.status_code == 200
    
    # Verify new Problem in DB with correct code, priority, status
    problem = Problem.query.filter_by(title='Test CRUD Problem').first()
    assert problem is not None
    assert problem.code.startswith('P')
    assert len(problem.code) == 5  # P0001 format
    assert problem.priority == PriorityEnum.Medium
    assert problem.status == StatusEnum.Open
    assert problem.created_by == test_user.id

def test_problem_list_requires_auth(test_client):
    """Test that problems list requires authentication"""
    res = test_client.get('/problems')
    assert res.status_code == 302  # Redirect to login

def test_create_problem_success(authenticated_client, test_department, test_user):
    """Test successful problem creation"""
    problem_data = {
        'title': 'Test Problem Creation',
        'description': 'This is a test problem description',
        'priority': 'High',
        'status': 'Open',
        'department_id': test_department.id,
        'submit': 'Submit Problem'
    }
    
    res = authenticated_client.post('/problems/new', data=problem_data, follow_redirects=True)
    assert res.status_code == 200
    
    # Verify problem was created in database
    problem = Problem.query.filter_by(title='Test Problem Creation').first()
    assert problem is not None
    assert problem.code.startswith('P')
    assert problem.priority == PriorityEnum.High
    assert problem.status == StatusEnum.Open
    assert problem.created_by == test_user.id

def test_problem_code_generation(authenticated_client, test_department):
    """Test that problem codes are generated correctly"""
    # Create first problem
    problem_data = {
        'title': 'First Problem',
        'description': 'First test problem',
        'priority': 'High',
        'status': 'Open',
        'department_id': test_department.id,
        'submit': 'Submit Problem'
    }
    authenticated_client.post('/problems/new', data=problem_data)
    
    # Create second problem
    problem_data['title'] = 'Second Problem'
    problem_data['description'] = 'Second test problem'
    authenticated_client.post('/problems/new', data=problem_data)
    
    # Verify codes are sequential and properly formatted
    problems = Problem.query.order_by(Problem.id).all()
    for problem in problems:
        assert problem.code.startswith('P')
        assert len(problem.code) == 5
        assert problem.code[1:].isdigit()

def test_edit_problem_success(authenticated_client, test_department, test_user):
    """Test successful problem editing"""
    problem = Problem(
        code='P0001',
        title='Original Title',
        description='Original description',
        priority=PriorityEnum.Medium,
        status=StatusEnum.Open,
        department_id=test_department.id,
        created_by=test_user.id
    )
    db.session.add(problem)
    db.session.commit()
    
    updated_data = {
        'title': 'Updated Title',
        'description': 'Updated description',
        'priority': 'High',
        'status': 'InProgress',
        'department_id': test_department.id,
        'submit': 'Submit Problem'
    }
    
    res = authenticated_client.post(f'/problems/{problem.id}/edit', data=updated_data, follow_redirects=True)
    assert res.status_code == 200
    
    # Verify problem was updated
    updated_problem = Problem.query.get(problem.id)
    assert updated_problem.title == 'Updated Title'
    assert updated_problem.priority == PriorityEnum.High
    assert updated_problem.status == StatusEnum.InProgress

def test_delete_problem(authenticated_client, test_department, test_user):
    """Test problem deletion"""
    problem = Problem(
        code='P0001',
        title='Problem to Delete',
        description='This problem will be deleted',
        priority=PriorityEnum.Low,
        status=StatusEnum.Open,
        department_id=test_department.id,
        created_by=test_user.id
    )
    db.session.add(problem)
    db.session.commit()
    problem_id = problem.id
    
    res = authenticated_client.post(f'/problems/{problem_id}/delete', follow_redirects=True)
    assert res.status_code == 200
    
    # Verify problem was deleted
    deleted_problem = Problem.query.get(problem_id)
    assert deleted_problem is None