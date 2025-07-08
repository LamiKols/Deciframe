/**
 * Admin Workflow Builder JavaScript
 * Handles visual workflow creation and editing with real-time JSON preview
 */

// Global workflow data storage
let editWorkflowData = {};

/**
 * Initialize edit workflow with existing definition
 */
function initializeEditWorkflow(workflowId, definition) {
    editWorkflowData[workflowId] = {
        triggers: definition.triggers || [],
        steps: definition.steps || [],
        stepCounter: 0
    };
    
    // Populate existing steps
    populateSteps(workflowId);
    updateWorkflowJSON(workflowId);
}

/**
 * Populate steps container with existing step data
 */
function populateSteps(workflowId) {
    const container = document.getElementById(`stepsContainer${workflowId}`);
    const data = editWorkflowData[workflowId];
    
    if (!container) return;
    
    container.innerHTML = '';
    
    if (data.steps.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-3">No steps defined. Click "Add Step" to create one.</p>';
        return;
    }
    
    data.steps.forEach((step, index) => {
        const stepDiv = createStepElement(workflowId, step, index);
        container.appendChild(stepDiv);
    });
}

/**
 * Create DOM element for a single workflow step
 */
function createStepElement(workflowId, step, index) {
    const stepDiv = document.createElement('div');
    stepDiv.className = 'step-item border border-secondary rounded p-3 mb-3 bg-secondary';
    stepDiv.dataset.stepIndex = index;
    
    // Dynamic fields based on action type
    const actionSpecificFields = getActionSpecificFields(step.action, step, workflowId, index);
    
    stepDiv.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="text-light mb-0">Step ${index + 1}</h6>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeStep(${workflowId}, ${index})">
                <i class="fas fa-trash"></i>
            </button>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <label class="form-label text-light">Action</label>
                <select class="form-control bg-dark text-light border-secondary" 
                        onchange="updateStepField(${workflowId}, ${index}, 'action', this.value); refreshStepFields(${workflowId}, ${index})">
                    <option value="">Select Action</option>
                    <option value="send_notification" ${step.action === 'send_notification' ? 'selected' : ''}>Send Notification</option>
                    <option value="create_task" ${step.action === 'create_task' ? 'selected' : ''}>Create Task</option>
                    <option value="update_status" ${step.action === 'update_status' ? 'selected' : ''}>Update Status</option>
                    <option value="assign_user" ${step.action === 'assign_user' ? 'selected' : ''}>Assign User</option>
                    <option value="conditional_approval" ${step.action === 'conditional_approval' ? 'selected' : ''}>Conditional Approval</option>
                </select>
            </div>
            <div class="col-md-6">
                <label class="form-label text-light">Target</label>
                <select class="form-control bg-dark text-light border-secondary" 
                        onchange="updateStepField(${workflowId}, ${index}, 'target', this.value)">
                    <option value="">Select Target</option>
                    <option value="department_manager" ${step.target === 'department_manager' ? 'selected' : ''}>Department Manager</option>
                    <option value="project_manager" ${step.target === 'project_manager' ? 'selected' : ''}>Project Manager</option>
                    <option value="business_analyst" ${step.target === 'business_analyst' ? 'selected' : ''}>Business Analyst</option>
                    <option value="problem_reporter" ${step.target === 'problem_reporter' ? 'selected' : ''}>Problem Reporter</option>
                    <option value="case_creator" ${step.target === 'case_creator' ? 'selected' : ''}>Case Creator</option>
                </select>
            </div>
        </div>
        
        <div class="row mt-2">
            <div class="col-md-6">
                <label class="form-label text-light">Template</label>
                <input type="text" class="form-control bg-dark text-light border-secondary" 
                       value="${step.template || ''}" placeholder="e.g., problem_escalation"
                       onchange="updateStepField(${workflowId}, ${index}, 'template', this.value)">
            </div>
            <div class="col-md-6">
                <label class="form-label text-light">Conditions</label>
                <input type="text" class="form-control bg-dark text-light border-secondary" 
                       value="${(step.conditions || []).join(', ')}" placeholder="e.g., priority == 'High'"
                       onchange="updateStepConditions(${workflowId}, ${index}, this.value)">
            </div>
        </div>
        
        <div id="actionFields${workflowId}_${index}" class="row mt-2">
            ${actionSpecificFields}
        </div>
    `;
    
    return stepDiv;
}

/**
 * Generate action-specific form fields
 */
function getActionSpecificFields(action, step, workflowId, index) {
    switch (action) {
        case 'create_task':
            return `
                <div class="col-md-6">
                    <label class="form-label text-light">Assignee</label>
                    <select class="form-control bg-dark text-light border-secondary" 
                            onchange="updateStepField(${workflowId}, ${index}, 'assignee', this.value)">
                        <option value="">Select Assignee</option>
                        <option value="business_analyst" ${step.assignee === 'business_analyst' ? 'selected' : ''}>Business Analyst</option>
                        <option value="project_manager" ${step.assignee === 'project_manager' ? 'selected' : ''}>Project Manager</option>
                        <option value="department_manager" ${step.assignee === 'department_manager' ? 'selected' : ''}>Department Manager</option>
                    </select>
                </div>
                <div class="col-md-6">
                    <label class="form-label text-light">Due Days</label>
                    <input type="number" class="form-control bg-dark text-light border-secondary" 
                           value="${step.due_days || 3}" min="1" max="30"
                           onchange="updateStepField(${workflowId}, ${index}, 'due_days', this.value)">
                </div>
            `;
        case 'update_status':
            return `
                <div class="col-md-6">
                    <label class="form-label text-light">New Status</label>
                    <select class="form-control bg-dark text-light border-secondary" 
                            onchange="updateStepField(${workflowId}, ${index}, 'new_status', this.value)">
                        <option value="">Select Status</option>
                        <option value="In Progress" ${step.new_status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                        <option value="On Hold" ${step.new_status === 'On Hold' ? 'selected' : ''}>On Hold</option>
                        <option value="Resolved" ${step.new_status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                        <option value="Under Review" ${step.new_status === 'Under Review' ? 'selected' : ''}>Under Review</option>
                    </select>
                </div>
            `;
        default:
            return '';
    }
}

/**
 * Add new step to workflow
 */
function addStep(workflowId) {
    const data = editWorkflowData[workflowId];
    if (!data) return;
    
    const newStep = { action: '', target: '', template: '', conditions: [] };
    data.steps.push(newStep);
    populateSteps(workflowId);
    updateWorkflowJSON(workflowId);
}

/**
 * Remove step from workflow
 */
function removeStep(workflowId, stepIndex) {
    const data = editWorkflowData[workflowId];
    if (!data) return;
    
    data.steps.splice(stepIndex, 1);
    populateSteps(workflowId);
    updateWorkflowJSON(workflowId);
}

/**
 * Update individual step field
 */
function updateStepField(workflowId, stepIndex, field, value) {
    const data = editWorkflowData[workflowId];
    if (data && data.steps[stepIndex]) {
        data.steps[stepIndex][field] = value;
        updateWorkflowJSON(workflowId);
    }
}

/**
 * Update step conditions (comma-separated string to array)
 */
function updateStepConditions(workflowId, stepIndex, value) {
    const data = editWorkflowData[workflowId];
    if (data && data.steps[stepIndex]) {
        data.steps[stepIndex].conditions = value.split(',').map(c => c.trim()).filter(c => c);
        updateWorkflowJSON(workflowId);
    }
}

/**
 * Refresh step fields after action type change
 */
function refreshStepFields(workflowId, index) {
    setTimeout(() => {
        populateSteps(workflowId);
    }, 100);
}

/**
 * Update workflow JSON definition and preview
 */
function updateWorkflowJSON(workflowId) {
    const data = editWorkflowData[workflowId];
    if (!data) return;
    
    // Get triggers from select
    const triggersSelect = document.getElementById(`triggersSelect${workflowId}`);
    if (triggersSelect) {
        const selectedTriggers = Array.from(triggersSelect.selectedOptions).map(option => option.value);
        data.triggers = selectedTriggers;
    }
    
    // Build definition with all step fields
    const definition = {
        triggers: data.triggers,
        steps: data.steps.filter(step => step.action).map(step => {
            const cleanStep = { action: step.action };
            
            // Add optional fields only if they have values
            if (step.target) cleanStep.target = step.target;
            if (step.template) cleanStep.template = step.template;
            if (step.assignee) cleanStep.assignee = step.assignee;
            if (step.due_days) cleanStep.due_days = parseInt(step.due_days);
            if (step.new_status) cleanStep.new_status = step.new_status;
            if (step.conditions && step.conditions.length > 0) cleanStep.conditions = step.conditions;
            
            return cleanStep;
        })
    };
    
    // Update preview
    const preview = document.getElementById(`jsonPreview${workflowId}`);
    if (preview) {
        preview.textContent = JSON.stringify(definition, null, 2);
    }
    
    // Update hidden field
    const hiddenField = document.getElementById(`template_content${workflowId}`);
    if (hiddenField) {
        hiddenField.value = JSON.stringify(definition);
    }
    
    // Validate and store
    validateWorkflow(workflowId, definition);
    if (editWorkflowData[workflowId]) {
        editWorkflowData[workflowId].currentDefinition = definition;
    }
}

/**
 * Validate workflow definition
 */
function validateWorkflow(workflowId, definition) {
    const statusDiv = document.getElementById(`validationStatus${workflowId}`);
    if (!statusDiv) return false;
    
    if (definition.triggers.length === 0) {
        statusDiv.innerHTML = '<small class="text-warning"><i class="fas fa-exclamation-triangle"></i> No triggers selected</small>';
        return false;
    }
    
    if (definition.steps.length === 0) {
        statusDiv.innerHTML = '<small class="text-warning"><i class="fas fa-exclamation-triangle"></i> No steps defined</small>';
        return false;
    }
    
    const incompleteSteps = definition.steps.filter(step => !step.action || !step.target);
    if (incompleteSteps.length > 0) {
        statusDiv.innerHTML = '<small class="text-warning"><i class="fas fa-exclamation-triangle"></i> Some steps are incomplete</small>';
        return false;
    }
    
    statusDiv.innerHTML = '<small class="text-success"><i class="fas fa-check"></i> Workflow is valid</small>';
    return true;
}

/**
 * Setup save workflow button handler
 */
function setupSaveWorkflowHandler(workflowId) {
    const saveBtn = document.getElementById(`saveWorkflowBtn${workflowId}`);
    const form = document.getElementById(`editForm${workflowId}`);
    
    if (saveBtn && form) {
        saveBtn.onclick = function(e) {
            e.preventDefault();
            saveWorkflow(workflowId);
        };
    }
}

/**
 * Save workflow via AJAX
 */
async function saveWorkflow(workflowId) {
    const data = editWorkflowData[workflowId];
    const saveBtn = document.getElementById(`saveWorkflowBtn${workflowId}`);
    
    if (!data || !data.currentDefinition) {
        alert('No workflow data to save');
        return;
    }
    
    // Validate before saving
    if (!validateWorkflow(workflowId, data.currentDefinition)) {
        alert('Please fix validation errors before saving');
        return;
    }
    
    // Disable save button during request
    const originalText = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Saving...';
    
    try {
        // Collect workflow data
        const workflowData = {
            name: document.getElementById(`workflowName${workflowId}`).value,
            description: document.getElementById(`workflowDescription${workflowId}`).value,
            definition: data.currentDefinition,
            is_active: document.getElementById(`workflowActive${workflowId}`).checked
        };
        
        // Send POST request with JSON data and authentication
        const response = await fetch(`/admin/workflows/${workflowId}/edit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(workflowData),
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Success - show message and close modal
            showSuccessMessage(result.message || 'Workflow saved successfully!');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById(`editWorkflowModal${workflowId}`));
            if (modal) modal.hide();
            
            // Refresh page to show updated data
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || `Save failed: ${response.status}`);
        }
    } catch (error) {
        console.error('Save workflow error:', error);
        showErrorMessage(`Failed to save workflow: ${error.message}`);
    } finally {
        // Re-enable save button
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalText;
    }
}

/**
 * Show success message
 */
function showSuccessMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed';
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    // Auto-dismiss after 3 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 3000);
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

/**
 * Initialize workflow builder when edit modals open
 */
document.addEventListener('shown.bs.modal', function(event) {
    const modal = event.target;
    if (modal.id.startsWith('editWorkflowModal')) {
        const workflowId = modal.id.replace('editWorkflowModal', '');
        // Get workflow definition from the hidden field
        const hiddenField = document.getElementById(`template_content${workflowId}`);
        if (hiddenField) {
            const definition = JSON.parse(hiddenField.value);
            initializeEditWorkflow(workflowId, definition);
            
            // Setup save button handler
            setupSaveWorkflowHandler(workflowId);
        }
    }
});