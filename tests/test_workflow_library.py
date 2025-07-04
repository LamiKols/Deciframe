"""
Tests for Workflow Library functionality
Tests seeding, import routes, visual builder, and API persistence
"""

import pytest
import json
from app import app, db
from models import WorkflowLibrary, WorkflowTemplate, AuditLog, User


@pytest.fixture
def client():
    """Create test client with database setup"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Create test user
            test_user = User(
                id='test_admin',
                email='admin@test.com',
                first_name='Test',
                last_name='Admin',
                role='Admin'
            )
            db.session.add(test_user)
            db.session.commit()
            
            yield client
            
            db.session.remove()
            db.drop_all()


@pytest.fixture
def auth_headers():
    """Mock authentication headers for testing"""
    return {'Authorization': 'Bearer test_token'}


class TestWorkflowLibrarySeeding:
    """Test WorkflowLibrary seeding on startup"""
    
    def test_library_seeding_creates_default_templates(self, client):
        """Test that default workflow templates are seeded"""
        # Check that library templates exist
        templates = WorkflowLibrary.query.all()
        assert len(templates) >= 6, "Should have at least 6 default templates"
        
        # Verify specific templates exist
        template_names = [t.name for t in templates]
        expected_templates = [
            "High-Priority Problem Escalation",
            "Business Case Auto-Approval",
            "Project Milestone Tracking",
            "Department Resource Allocation",
            "Problem-to-Case Conversion",
            "Stakeholder Communication Workflow"
        ]
        
        for expected in expected_templates:
            assert expected in template_names, f"Missing template: {expected}"
    
    def test_library_templates_have_valid_structure(self, client):
        """Test that seeded templates have valid JSON structure"""
        templates = WorkflowLibrary.query.all()
        
        for template in templates:
            assert template.name, "Template must have a name"
            assert template.description, "Template must have a description"
            assert template.category, "Template must have a category"
            assert isinstance(template.definition, dict), "Definition must be a dict"
            
            # Validate definition structure
            definition = template.definition
            assert 'triggers' in definition, "Definition must have triggers"
            assert 'steps' in definition, "Definition must have steps"
            assert isinstance(definition['triggers'], list), "Triggers must be a list"
            assert isinstance(definition['steps'], list), "Steps must be a list"
            
            # Validate steps have required fields
            for step in definition['steps']:
                assert 'action' in step, "Each step must have an action"
    
    def test_library_categories_are_organized(self, client):
        """Test that templates are properly categorized"""
        templates = WorkflowLibrary.query.all()
        categories = set(t.category for t in templates)
        
        expected_categories = {
            "Problem Management",
            "Case Management", 
            "Project Management",
            "Resource Management",
            "Communication"
        }
        
        assert expected_categories.issubset(categories), "Missing expected categories"


class TestWorkflowImportRoutes:
    """Test workflow import functionality"""
    
    def test_import_page_shows_library_items(self, client):
        """Test GET /admin/workflows/import shows library items"""
        # Mock authentication for the request
        with client.session_transaction() as sess:
            sess['user_id'] = 'test_admin'
        
        response = client.get('/admin/workflows/import')
        assert response.status_code == 200
        
        # Check that library templates are displayed
        html_content = response.data.decode('utf-8')
        assert 'High-Priority Problem Escalation' in html_content
        assert 'Business Case Auto-Approval' in html_content
        assert 'Project Milestone Tracking' in html_content
    
    def test_import_page_shows_categories(self, client):
        """Test that import page organizes templates by category"""
        with client.session_transaction() as sess:
            sess['user_id'] = 'test_admin'
        
        response = client.get('/admin/workflows/import')
        html_content = response.data.decode('utf-8')
        
        # Check for category headers
        assert 'Problem Management' in html_content
        assert 'Case Management' in html_content
        assert 'Project Management' in html_content
    
    def test_import_post_copies_definition(self, client):
        """Test POST import copies definition into WorkflowTemplate"""
        with client.session_transaction() as sess:
            sess['user_id'] = 'test_admin'
        
        # Get a library template
        library_template = WorkflowLibrary.query.first()
        assert library_template, "Should have library templates"
        
        # Test import
        response = client.post('/admin/workflows/import', data={
            'library_id': library_template.id,
            'custom_name': 'Test Imported Workflow'
        })
        
        # Should redirect after successful import
        assert response.status_code == 302
        
        # Verify workflow was created
        imported_workflow = WorkflowTemplate.query.filter_by(
            name='Test Imported Workflow'
        ).first()
        
        assert imported_workflow, "Workflow should be created"
        assert imported_workflow.description == library_template.description
        assert imported_workflow.definition == library_template.definition
        assert not imported_workflow.is_active, "Imported workflows should start inactive"
    
    def test_import_with_default_name(self, client):
        """Test import without custom name uses default 'My - ' prefix"""
        with client.session_transaction() as sess:
            sess['user_id'] = 'test_admin'
        
        library_template = WorkflowLibrary.query.first()
        
        response = client.post('/admin/workflows/import', data={
            'library_id': library_template.id
        })
        
        assert response.status_code == 302
        
        # Check default naming
        expected_name = f"My - {library_template.name}"
        imported_workflow = WorkflowTemplate.query.filter_by(
            name=expected_name
        ).first()
        
        assert imported_workflow, f"Should create workflow with name: {expected_name}"
    
    def test_import_duplicate_name_fails(self, client):
        """Test importing with duplicate name shows error"""
        with client.session_transaction() as sess:
            sess['user_id'] = 'test_admin'
        
        library_template = WorkflowLibrary.query.first()
        
        # Import once
        client.post('/admin/workflows/import', data={
            'library_id': library_template.id,
            'custom_name': 'Duplicate Name Test'
        })
        
        # Try to import again with same name
        response = client.post('/admin/workflows/import', data={
            'library_id': library_template.id,
            'custom_name': 'Duplicate Name Test'
        })
        
        # Should show error (200 with error message)
        assert response.status_code == 200
        html_content = response.data.decode('utf-8')
        assert 'already exists' in html_content


class TestVisualBuilderJSONPreview:
    """Test visual builder JSON preview functionality"""
    
    def test_json_preview_structure(self, client):
        """Test that JSON preview has correct structure"""
        # This test verifies the expected JSON structure
        # that the visual builder should generate
        
        expected_structure = {
            "triggers": ["problem_created", "case_approved"],
            "steps": [
                {
                    "action": "send_notification",
                    "target": "department_manager",
                    "template": "problem_escalation",
                    "conditions": ["priority == 'High'"]
                },
                {
                    "action": "create_task",
                    "assignee": "business_analyst",
                    "due_days": 3
                }
            ]
        }
        
        # Validate structure
        assert 'triggers' in expected_structure
        assert 'steps' in expected_structure
        assert isinstance(expected_structure['triggers'], list)
        assert isinstance(expected_structure['steps'], list)
        
        # Validate step structure
        for step in expected_structure['steps']:
            assert 'action' in step, "Each step must have an action"
            
            # Validate action-specific fields
            if step['action'] == 'send_notification':
                assert 'target' in step
                assert 'template' in step
            elif step['action'] == 'create_task':
                assert 'assignee' in step
                assert 'due_days' in step
    
    def test_workflow_validation_rules(self, client):
        """Test workflow validation logic"""
        # Test empty workflow (invalid)
        empty_workflow = {"triggers": [], "steps": []}
        assert not self._validate_workflow(empty_workflow)
        
        # Test workflow with triggers but no steps (invalid)
        no_steps = {"triggers": ["problem_created"], "steps": []}
        assert not self._validate_workflow(no_steps)
        
        # Test workflow with steps but no triggers (invalid)
        no_triggers = {
            "triggers": [],
            "steps": [{"action": "send_notification", "target": "manager"}]
        }
        assert not self._validate_workflow(no_triggers)
        
        # Test valid workflow
        valid_workflow = {
            "triggers": ["problem_created"],
            "steps": [{"action": "send_notification", "target": "manager"}]
        }
        assert self._validate_workflow(valid_workflow)
    
    def _validate_workflow(self, definition):
        """Helper method to simulate workflow validation"""
        if not definition.get('triggers'):
            return False
        if not definition.get('steps'):
            return False
        
        # Check that all steps have required fields
        for step in definition['steps']:
            if not step.get('action'):
                return False
            if not step.get('target') and step['action'] != 'conditional_approval':
                return False
        
        return True


class TestAPIWorkflowPersistence:
    """Test API saving and audit logging"""
    
    def test_api_save_persists_to_database(self, client):
        """Test that API saves persist workflow changes to database"""
        with client.session_transaction() as sess:
            sess['user_id'] = 'test_admin'
        
        # Create a workflow to edit
        workflow = WorkflowTemplate(
            name="Test Workflow",
            description="Test Description",
            definition={"triggers": ["test"], "steps": []},
            is_active=False,
            created_by='test_admin'
        )
        db.session.add(workflow)
        db.session.commit()
        
        # Test API update
        update_data = {
            "name": "Updated Workflow",
            "description": "Updated Description",
            "definition": {
                "triggers": ["problem_created"],
                "steps": [
                    {
                        "action": "send_notification",
                        "target": "department_manager",
                        "template": "escalation"
                    }
                ]
            },
            "is_active": True
        }
        
        response = client.post(
            f'/admin/workflows/{workflow.id}/edit',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        # Verify database changes
        updated_workflow = WorkflowTemplate.query.get(workflow.id)
        assert updated_workflow.name == "Updated Workflow"
        assert updated_workflow.description == "Updated Description"
        assert updated_workflow.is_active == True
        assert updated_workflow.definition == update_data["definition"]
    
    def test_api_save_creates_audit_log(self, client):
        """Test that API saves create audit log entries"""
        with client.session_transaction() as sess:
            sess['user_id'] = 'test_admin'
        
        # Create workflow
        workflow = WorkflowTemplate(
            name="Audit Test Workflow",
            description="Test",
            definition={"triggers": [], "steps": []},
            is_active=False,
            created_by='test_admin'
        )
        db.session.add(workflow)
        db.session.commit()
        
        initial_audit_count = AuditLog.query.count()
        
        # Update via API
        update_data = {
            "name": "Updated Name",
            "description": "Updated Description",
            "definition": {"triggers": ["test"], "steps": []},
            "is_active": True
        }
        
        response = client.post(
            f'/admin/workflows/{workflow.id}/edit',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        # Verify audit log was created
        final_audit_count = AuditLog.query.count()
        assert final_audit_count > initial_audit_count, "Audit log should be created"
        
        # Verify audit log details
        audit_log = AuditLog.query.order_by(AuditLog.timestamp.desc()).first()
        assert audit_log.user_id == 'test_admin'
        assert 'Edited workflow' in audit_log.action
        assert audit_log.target == 'WorkflowTemplate'
        assert audit_log.target_id == workflow.id
    
    def test_api_handles_invalid_json_definition(self, client):
        """Test API properly handles invalid workflow definitions"""
        with client.session_transaction() as sess:
            sess['user_id'] = 'test_admin'
        
        workflow = WorkflowTemplate(
            name="Test Workflow",
            description="Test",
            definition={"triggers": [], "steps": []},
            is_active=False,
            created_by='test_admin'
        )
        db.session.add(workflow)
        db.session.commit()
        
        # Test with invalid definition (missing action in step)
        invalid_data = {
            "name": "Test",
            "description": "Test",
            "definition": {
                "triggers": ["test"],
                "steps": [{"target": "manager"}]  # Missing 'action'
            },
            "is_active": False
        }
        
        response = client.post(
            f'/admin/workflows/{workflow.id}/edit',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        
        # Verify error message
        response_data = json.loads(response.data)
        assert 'error' in response_data
        assert 'missing required' in response_data['error'].lower()
    
    def test_form_data_fallback_still_works(self, client):
        """Test that traditional form submission still works"""
        with client.session_transaction() as sess:
            sess['user_id'] = 'test_admin'
        
        workflow = WorkflowTemplate(
            name="Form Test Workflow",
            description="Test",
            definition={"triggers": [], "steps": []},
            is_active=False,
            created_by='test_admin'
        )
        db.session.add(workflow)
        db.session.commit()
        
        # Test form submission
        form_data = {
            'name': 'Form Updated Workflow',
            'description': 'Form Updated Description',
            'template_content': json.dumps({
                "triggers": ["form_test"],
                "steps": [{"action": "send_notification", "target": "manager"}]
            }),
            'is_active': 'on'
        }
        
        response = client.post(
            f'/admin/workflows/{workflow.id}/edit',
            data=form_data
        )
        
        # Should redirect on success
        assert response.status_code == 302
        
        # Verify updates
        updated_workflow = WorkflowTemplate.query.get(workflow.id)
        assert updated_workflow.name == 'Form Updated Workflow'
        assert updated_workflow.is_active == True


def test_complete_workflow_library_integration(client):
    """Integration test covering the complete workflow library flow"""
    with client.session_transaction() as sess:
        sess['user_id'] = 'test_admin'
    
    # 1. Verify library is seeded
    library_count = WorkflowLibrary.query.count()
    assert library_count >= 6, "Library should be seeded"
    
    # 2. Import a workflow
    library_template = WorkflowLibrary.query.first()
    import_response = client.post('/admin/workflows/import', data={
        'library_id': library_template.id,
        'custom_name': 'Integration Test Workflow'
    })
    assert import_response.status_code == 302
    
    # 3. Verify workflow was created
    imported_workflow = WorkflowTemplate.query.filter_by(
        name='Integration Test Workflow'
    ).first()
    assert imported_workflow, "Workflow should be imported"
    
    # 4. Edit via API
    update_data = {
        "name": "Integration Test Updated",
        "description": "Updated via API",
        "definition": {
            "triggers": ["integration_test"],
            "steps": [
                {
                    "action": "send_notification",
                    "target": "department_manager",
                    "template": "test_template"
                }
            ]
        },
        "is_active": True
    }
    
    api_response = client.post(
        f'/admin/workflows/{imported_workflow.id}/edit',
        data=json.dumps(update_data),
        content_type='application/json'
    )
    assert api_response.status_code == 200
    
    # 5. Verify final state
    final_workflow = WorkflowTemplate.query.get(imported_workflow.id)
    assert final_workflow.name == "Integration Test Updated"
    assert final_workflow.is_active == True
    
    # 6. Verify audit trail
    audit_logs = AuditLog.query.filter_by(target_id=imported_workflow.id).all()
    assert len(audit_logs) > 0, "Should have audit logs"