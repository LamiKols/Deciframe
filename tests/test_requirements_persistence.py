"""
Tests for Requirements Persistence System
Tests Epic & Story database persistence, role-based access, and inline editing functionality
"""

import pytest
import json
from app import app, db
from models import User, BusinessCase, Epic, Story, RoleEnum, StatusEnum, CaseTypeEnum, CaseDepthEnum
from datetime import datetime


@pytest.fixture
def client():
    """Create test client with in-memory database"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def test_users(client):
    """Create test users with different roles"""
    ba_user = User(
        id=1,
        name="Test BA",
        email="ba@test.com",
        role=RoleEnum.BA,
        password_hash="hashed_password"
    )
    
    manager_user = User(
        id=2,
        name="Test Manager",
        email="manager@test.com",
        role=RoleEnum.Manager,
        password_hash="hashed_password"
    )
    
    pm_user = User(
        id=3,
        name="Test PM",
        email="pm@test.com",
        role=RoleEnum.PM,
        password_hash="hashed_password"
    )
    
    db.session.add_all([ba_user, manager_user, pm_user])
    db.session.commit()
    
    return {
        'ba': ba_user,
        'manager': manager_user,
        'pm': pm_user
    }


@pytest.fixture
def test_business_case(client, test_users):
    """Create test business case"""
    case = BusinessCase(
        id=1,
        code="C0001",
        title="Test Business Case",
        description="Test case for requirements",
        status=StatusEnum.Open,
        case_type=CaseTypeEnum.Reactive,
        case_depth=CaseDepthEnum.Light,
        cost_estimate=10000.0,
        benefit_estimate=25000.0,
        roi=150.0,
        created_by=test_users['ba'].id,
        created_at=datetime.utcnow()
    )
    
    db.session.add(case)
    db.session.commit()
    
    return case


def get_auth_headers(user_id):
    """Generate auth headers for test requests"""
    # Mock JWT token - in real implementation would use proper JWT
    return {'Authorization': f'Bearer test_token_{user_id}'}


def mock_get_current_user(user_id):
    """Mock the get_current_user function"""
    return User.query.get(user_id)


class TestEpicStoragePersistence:
    """Test Epic and Story persistence after AI generation"""
    
    def test_epics_saved_after_ai_draft(self, client, test_business_case, test_users, monkeypatch):
        """Test that epics and stories are saved to database after AI generation"""
        # Mock the get_current_user function
        monkeypatch.setattr('ai.routes.get_current_user', lambda: test_users['ba'])
        
        # Simulate AI-generated epics data
        ai_response_data = {
            'epics': [
                {
                    'title': 'User Management System',
                    'description': 'Comprehensive user management and authentication system',
                    'stories': [
                        {
                            'title': 'User Registration',
                            'description': 'As a new user, I want to register an account',
                            'priority': 'High',
                            'effort_estimate': '5 story points',
                            'acceptance_criteria': ['Valid email required', 'Password strength validation']
                        },
                        {
                            'title': 'User Login',
                            'description': 'As a user, I want to login securely',
                            'priority': 'High',
                            'effort_estimate': '3 story points',
                            'acceptance_criteria': ['Multi-factor authentication', 'Session management']
                        }
                    ]
                },
                {
                    'title': 'Data Processing Engine',
                    'description': 'Core data processing and validation system',
                    'stories': [
                        {
                            'title': 'Data Validation',
                            'description': 'As a system, I want to validate all input data',
                            'priority': 'Medium',
                            'effort_estimate': '8 story points',
                            'acceptance_criteria': ['Real-time validation', 'Error reporting']
                        }
                    ]
                }
            ]
        }
        
        # Make request to AI generate requirements endpoint
        response = client.post(
            f'/api/ai/generate-requirements/{test_business_case.id}',
            headers=get_auth_headers(test_users['ba'].id),
            data=json.dumps(ai_response_data),
            content_type='application/json'
        )
        
        # Verify epics were saved to database
        epics = Epic.query.filter_by(case_id=test_business_case.id).all()
        assert len(epics) == 2
        
        # Verify epic details
        user_mgmt_epic = next(e for e in epics if e.title == 'User Management System')
        assert user_mgmt_epic.description == 'Comprehensive user management and authentication system'
        assert len(user_mgmt_epic.stories) == 2
        
        data_proc_epic = next(e for e in epics if e.title == 'Data Processing Engine')
        assert data_proc_epic.description == 'Core data processing and validation system'
        assert len(data_proc_epic.stories) == 1
        
        # Verify story details
        reg_story = next(s for s in user_mgmt_epic.stories if s.title == 'User Registration')
        assert reg_story.priority == 'High'
        assert reg_story.effort_estimate == '5 story points'
        assert 'Valid email required' in reg_story.acceptance_criteria
        
        login_story = next(s for s in user_mgmt_epic.stories if s.title == 'User Login')
        assert login_story.priority == 'High'
        assert login_story.effort_estimate == '3 story points'
        
        validation_story = data_proc_epic.stories[0]
        assert validation_story.title == 'Data Validation'
        assert validation_story.priority == 'Medium'


class TestRegenerateFlow:
    """Test regenerate functionality clears old data and saves new"""
    
    def test_regenerate_clears_old_data(self, client, test_business_case, test_users, monkeypatch):
        """Test that regenerate clears existing epics before creating new ones"""
        # Mock the get_current_user function
        monkeypatch.setattr('ai.routes.get_current_user', lambda: test_users['ba'])
        
        # Create initial epics
        original_epic = Epic(
            case_id=test_business_case.id,
            title="Original Epic",
            description="This should be deleted"
        )
        db.session.add(original_epic)
        db.session.flush()
        
        original_story = Story(
            epic_id=original_epic.id,
            title="Original Story",
            description="This should also be deleted",
            acceptance_criteria=json.dumps(["Original criteria"])
        )
        db.session.add(original_story)
        db.session.commit()
        
        # Verify original data exists
        assert Epic.query.filter_by(case_id=test_business_case.id).count() == 1
        assert Story.query.count() == 1
        
        # Call clear epics endpoint
        response = client.post(
            f'/api/ai/clear-epics/{test_business_case.id}',
            headers=get_auth_headers(test_users['ba'].id)
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['deleted_count'] == 1
        
        # Verify all epics and stories were deleted
        assert Epic.query.filter_by(case_id=test_business_case.id).count() == 0
        assert Story.query.count() == 0
        
        # Now generate new epics
        new_epics_data = {
            'epics': [
                {
                    'title': 'New Epic After Regenerate',
                    'description': 'This is the new epic after regeneration',
                    'stories': [
                        {
                            'title': 'New Story',
                            'description': 'New story after regeneration',
                            'acceptance_criteria': ['New criteria 1', 'New criteria 2']
                        }
                    ]
                }
            ]
        }
        
        # Simulate AI generation after clear
        response = client.post(
            f'/api/ai/generate-requirements/{test_business_case.id}',
            headers=get_auth_headers(test_users['ba'].id),
            data=json.dumps(new_epics_data),
            content_type='application/json'
        )
        
        # Verify new epics were created
        epics = Epic.query.filter_by(case_id=test_business_case.id).all()
        assert len(epics) == 1
        assert epics[0].title == 'New Epic After Regenerate'
        assert len(epics[0].stories) == 1
        assert epics[0].stories[0].title == 'New Story'


class TestRoleBasedAccess:
    """Test role-based access to requirements save API"""
    
    def test_only_ba_can_save_requirements(self, client, test_business_case, test_users, monkeypatch):
        """Test that only BA users can call the save requirements API"""
        # Create test epic and story
        epic = Epic(
            case_id=test_business_case.id,
            title="Test Epic",
            description="Test epic description"
        )
        db.session.add(epic)
        db.session.flush()
        
        story = Story(
            epic_id=epic.id,
            title="Test Story",
            description="Test story description",
            acceptance_criteria=json.dumps(["Test criteria"])
        )
        db.session.add(story)
        db.session.commit()
        
        # Test BA user can save (should succeed)
        monkeypatch.setattr('business.routes.get_current_user', lambda: test_users['ba'])
        
        save_data = {
            'epics': [
                {
                    'id': epic.id,
                    'title': 'Updated Epic Title',
                    'description': 'Updated epic description',
                    'stories': [
                        {
                            'id': story.id,
                            'title': 'Updated Story Title',
                            'criteria': 'Updated story criteria'
                        }
                    ]
                }
            ]
        }
        
        response = client.post(
            '/business/api/requirements/save',
            headers=get_auth_headers(test_users['ba'].id),
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Test Manager user cannot save (should fail)
        monkeypatch.setattr('business.routes.get_current_user', lambda: test_users['manager'])
        
        response = client.post(
            '/business/api/requirements/save',
            headers=get_auth_headers(test_users['manager'].id),
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Only Business Analysts' in data['error']
        
        # Test PM user cannot save (should fail)
        monkeypatch.setattr('business.routes.get_current_user', lambda: test_users['pm'])
        
        response = client.post(
            '/business/api/requirements/save',
            headers=get_auth_headers(test_users['pm'].id),
            data=json.dumps(save_data),
            content_type='application/json'
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Only Business Analysts' in data['error']
    
    def test_only_ba_can_clear_epics(self, client, test_business_case, test_users, monkeypatch):
        """Test that only BA users can clear epics"""
        # Create test epic
        epic = Epic(
            case_id=test_business_case.id,
            title="Epic to Clear",
            description="This epic should only be clearable by BA"
        )
        db.session.add(epic)
        db.session.commit()
        
        # Test Manager cannot clear epics
        monkeypatch.setattr('ai.routes.get_current_user', lambda: test_users['manager'])
        
        response = client.post(
            f'/api/ai/clear-epics/{test_business_case.id}',
            headers=get_auth_headers(test_users['manager'].id)
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Only Business Analysts' in data['error']
        
        # Verify epic still exists
        assert Epic.query.filter_by(case_id=test_business_case.id).count() == 1
        
        # Test BA can clear epics
        monkeypatch.setattr('ai.routes.get_current_user', lambda: test_users['ba'])
        
        response = client.post(
            f'/api/ai/clear-epics/{test_business_case.id}',
            headers=get_auth_headers(test_users['ba'].id)
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['deleted_count'] == 1
        
        # Verify epic was deleted
        assert Epic.query.filter_by(case_id=test_business_case.id).count() == 0


class TestInlineEditsPersistence:
    """Test inline edits via save API persist correctly"""
    
    def test_inline_edits_persist_correctly(self, client, test_business_case, test_users, monkeypatch):
        """Test that inline edits are persisted correctly to the database"""
        # Mock BA user
        monkeypatch.setattr('business.routes.get_current_user', lambda: test_users['ba'])
        
        # Create initial epic and stories
        epic1 = Epic(
            case_id=test_business_case.id,
            title="Original Epic 1",
            description="Original description 1"
        )
        epic2 = Epic(
            case_id=test_business_case.id,
            title="Original Epic 2", 
            description="Original description 2"
        )
        db.session.add_all([epic1, epic2])
        db.session.flush()
        
        story1 = Story(
            epic_id=epic1.id,
            title="Original Story 1",
            description="Original story 1 description",
            criteria="Original criteria 1"
        )
        story2 = Story(
            epic_id=epic1.id,
            title="Original Story 2",
            description="Original story 2 description", 
            criteria="Original criteria 2"
        )
        story3 = Story(
            epic_id=epic2.id,
            title="Original Story 3",
            description="Original story 3 description",
            criteria="Original criteria 3"
        )
        db.session.add_all([story1, story2, story3])
        db.session.commit()
        
        # Prepare inline edit data
        edit_data = {
            'epics': [
                {
                    'id': epic1.id,
                    'title': 'Edited Epic 1 Title',
                    'description': 'Edited epic 1 description',
                    'stories': [
                        {
                            'id': story1.id,
                            'title': 'Edited Story 1 Title',
                            'criteria': 'Edited story 1 criteria with new requirements'
                        },
                        {
                            'id': story2.id,
                            'title': 'Edited Story 2 Title',
                            'criteria': 'Completely new criteria for story 2'
                        }
                    ]
                },
                {
                    'id': epic2.id,
                    'title': 'Edited Epic 2 Title',
                    'description': 'Edited epic 2 description with more details',
                    'stories': [
                        {
                            'id': story3.id,
                            'title': 'Edited Story 3 Title',
                            'criteria': 'Updated criteria for story 3'
                        }
                    ]
                }
            ]
        }
        
        # Make save request
        response = client.post(
            '/business/api/requirements/save',
            headers=get_auth_headers(test_users['ba'].id),
            data=json.dumps(edit_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['updated_epics'] == 2
        assert data['updated_stories'] == 3
        
        # Verify changes were persisted to database
        db.session.refresh(epic1)
        db.session.refresh(epic2)
        db.session.refresh(story1)
        db.session.refresh(story2)
        db.session.refresh(story3)
        
        # Check epic changes
        assert epic1.title == 'Edited Epic 1 Title'
        assert epic1.description == 'Edited epic 1 description'
        assert epic2.title == 'Edited Epic 2 Title'
        assert epic2.description == 'Edited epic 2 description with more details'
        
        # Check story changes
        assert story1.title == 'Edited Story 1 Title'
        assert story1.criteria == 'Edited story 1 criteria with new requirements'
        assert story2.title == 'Edited Story 2 Title'
        assert story2.criteria == 'Completely new criteria for story 2'
        assert story3.title == 'Edited Story 3 Title'
        assert story3.criteria == 'Updated criteria for story 3'
    
    def test_partial_edits_handle_gracefully(self, client, test_business_case, test_users, monkeypatch):
        """Test that partial edits (missing fields) are handled gracefully"""
        # Mock BA user
        monkeypatch.setattr('business.routes.get_current_user', lambda: test_users['ba'])
        
        # Create test epic and story
        epic = Epic(
            case_id=test_business_case.id,
            title="Test Epic",
            description="Test description"
        )
        db.session.add(epic)
        db.session.flush()
        
        story = Story(
            epic_id=epic.id,
            title="Test Story",
            description="Test story description",
            criteria="Test criteria"
        )
        db.session.add(story)
        db.session.commit()
        
        # Save original values
        original_epic_title = epic.title
        original_story_criteria = story.criteria
        
        # Prepare partial edit data (missing some fields)
        partial_edit_data = {
            'epics': [
                {
                    'id': epic.id,
                    'description': 'Only description updated',
                    # title missing - should keep original
                    'stories': [
                        {
                            'id': story.id,
                            'title': 'Only title updated'
                            # criteria missing - should keep original
                        }
                    ]
                }
            ]
        }
        
        # Make save request
        response = client.post(
            '/business/api/requirements/save',
            headers=get_auth_headers(test_users['ba'].id),
            data=json.dumps(partial_edit_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify partial changes were applied while preserving existing values
        db.session.refresh(epic)
        db.session.refresh(story)
        
        assert epic.title == original_epic_title  # Unchanged
        assert epic.description == 'Only description updated'  # Changed
        assert story.title == 'Only title updated'  # Changed
        assert story.criteria == original_story_criteria  # Unchanged


class TestDataIntegrity:
    """Test data integrity and error handling"""
    
    def test_invalid_epic_id_handling(self, client, test_business_case, test_users, monkeypatch):
        """Test handling of invalid epic IDs in save request"""
        monkeypatch.setattr('business.routes.get_current_user', lambda: test_users['ba'])
        
        # Prepare data with non-existent epic ID
        invalid_data = {
            'epics': [
                {
                    'id': 99999,  # Non-existent ID
                    'title': 'This epic does not exist',
                    'description': 'Should be ignored',
                    'stories': []
                }
            ]
        }
        
        response = client.post(
            '/business/api/requirements/save',
            headers=get_auth_headers(test_users['ba'].id),
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['updated_epics'] == 0  # No epics updated
        assert data['updated_stories'] == 0  # No stories updated
    
    def test_malformed_request_data(self, client, test_business_case, test_users, monkeypatch):
        """Test handling of malformed request data"""
        monkeypatch.setattr('business.routes.get_current_user', lambda: test_users['ba'])
        
        # Test missing 'epics' key
        response = client.post(
            '/business/api/requirements/save',
            headers=get_auth_headers(test_users['ba'].id),
            data=json.dumps({'invalid': 'data'}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid data format' in data['error']
        
        # Test completely empty request
        response = client.post(
            '/business/api/requirements/save',
            headers=get_auth_headers(test_users['ba'].id),
            data='',
            content_type='application/json'
        )
        
        assert response.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])