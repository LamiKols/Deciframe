/**
 * Story Refinement Interface for Business Analysts
 * Provides AI-powered story enhancement and project backlog management
 */

class StoryRefinementManager {
    constructor() {
        this.currentStoryId = null;
        this.refinedData = null;
        this.initializeEventHandlers();
    }

    initializeEventHandlers() {
        // Refine story button handlers
        document.addEventListener('click', (e) => {
            if (e.target.matches('.refine-story-btn')) {
                e.preventDefault();
                const storyId = e.target.dataset.storyId;
                this.openRefinementModal(storyId);
            }
        });

        // Apply refined changes handler
        const applyChangesBtn = document.getElementById('applyRefinedChanges');
        if (applyChangesBtn) {
            applyChangesBtn.addEventListener('click', () => this.applyRefinedChanges());
        }

        // Modal event handlers
        const refinementModal = document.getElementById('storyRefinementModal');
        if (refinementModal) {
            refinementModal.addEventListener('hidden.bs.modal', () => this.resetModal());
        }
    }

    async openRefinementModal(storyId) {
        this.currentStoryId = storyId;
        this.showLoadingState();
        
        const modal = new bootstrap.Modal(document.getElementById('storyRefinementModal'));
        modal.show();

        try {
            const response = await fetch('/api/ai/refine-story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    story_id: storyId
                })
            });

            const data = await response.json();

            if (data.success) {
                this.refinedData = data.refined_story;
                this.displayRefinedStory(data.refined_story, data.ai_generated);
                this.showSuccessNotification('Story refinement completed successfully!');
            } else {
                this.showError(data.error || 'Failed to refine story');
            }
        } catch (error) {
            console.error('Story refinement error:', error);
            this.showError('Failed to connect to refinement service');
        }
    }

    displayRefinedStory(refinedStory, aiGenerated = true) {
        const container = document.getElementById('refinedStoryContent');
        if (!container) return;

        const aiIndicator = aiGenerated 
            ? '<span class="badge bg-info ms-2">AI Enhanced</span>' 
            : '<span class="badge bg-secondary ms-2">Fallback</span>';

        container.innerHTML = `
            <div class="refined-story-display">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="mb-0">Refined Story Details ${aiIndicator}</h5>
                    <button type="button" class="btn btn-outline-secondary btn-sm" onclick="storyRefinement.toggleEditMode()">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                </div>

                <div class="row">
                    <div class="col-md-12 mb-3">
                        <label class="form-label fw-bold text-light">Enhanced Title:</label>
                        <div class="refined-field" data-field="title">
                            <div class="display-mode p-2 bg-dark border rounded">
                                ${this.escapeHtml(refinedStory.title)}
                            </div>
                            <input type="text" class="form-control edit-mode d-none" value="${this.escapeHtml(refinedStory.title)}">
                        </div>
                    </div>

                    <div class="col-md-12 mb-3">
                        <label class="form-label fw-bold text-light">User Story Description:</label>
                        <div class="refined-field" data-field="description">
                            <div class="display-mode p-2 bg-dark border rounded">
                                ${this.escapeHtml(refinedStory.description)}
                            </div>
                            <textarea class="form-control edit-mode d-none" rows="3">${this.escapeHtml(refinedStory.description)}</textarea>
                        </div>
                    </div>

                    <div class="col-md-6 mb-3">
                        <label class="form-label fw-bold text-light">Priority:</label>
                        <div class="refined-field" data-field="priority">
                            <div class="display-mode p-2 bg-dark border rounded">
                                <span class="badge ${this.getPriorityBadgeClass(refinedStory.priority)}">${refinedStory.priority}</span>
                            </div>
                            <select class="form-select edit-mode d-none">
                                <option value="High" ${refinedStory.priority === 'High' ? 'selected' : ''}>High</option>
                                <option value="Medium" ${refinedStory.priority === 'Medium' ? 'selected' : ''}>Medium</option>
                                <option value="Low" ${refinedStory.priority === 'Low' ? 'selected' : ''}>Low</option>
                            </select>
                        </div>
                    </div>

                    <div class="col-md-6 mb-3">
                        <label class="form-label fw-bold text-light">Effort Estimate:</label>
                        <div class="refined-field" data-field="effort_estimate">
                            <div class="display-mode p-2 bg-dark border rounded">
                                ${this.escapeHtml(refinedStory.effort_estimate)}
                            </div>
                            <select class="form-select edit-mode d-none">
                                <option value="1 point" ${refinedStory.effort_estimate === '1 point' ? 'selected' : ''}>1 point</option>
                                <option value="2 points" ${refinedStory.effort_estimate === '2 points' ? 'selected' : ''}>2 points</option>
                                <option value="3 points" ${refinedStory.effort_estimate === '3 points' ? 'selected' : ''}>3 points</option>
                                <option value="5 points" ${refinedStory.effort_estimate === '5 points' ? 'selected' : ''}>5 points</option>
                                <option value="8 points" ${refinedStory.effort_estimate === '8 points' ? 'selected' : ''}>8 points</option>
                                <option value="13 points" ${refinedStory.effort_estimate === '13 points' ? 'selected' : ''}>13 points</option>
                            </select>
                        </div>
                    </div>

                    <div class="col-md-12 mb-3">
                        <label class="form-label fw-bold text-light">Acceptance Criteria:</label>
                        <div class="refined-field" data-field="acceptance_criteria">
                            <div class="display-mode p-2 bg-dark border rounded">
                                <ul class="mb-0 text-light">
                                    ${Array.isArray(refinedStory.acceptance_criteria) 
                                        ? refinedStory.acceptance_criteria.map(criteria => `<li>${this.escapeHtml(criteria)}</li>`).join('')
                                        : `<li>${this.escapeHtml(refinedStory.acceptance_criteria || 'No criteria defined')}</li>`
                                    }
                                </ul>
                            </div>
                            <textarea class="form-control edit-mode d-none" rows="4" placeholder="Enter each criterion on a new line">${
                                Array.isArray(refinedStory.acceptance_criteria) 
                                    ? refinedStory.acceptance_criteria.join('\n')
                                    : (refinedStory.acceptance_criteria || '')
                            }</textarea>
                        </div>
                    </div>

                    ${refinedStory.business_value ? `
                    <div class="col-md-12 mb-3">
                        <label class="form-label fw-bold text-light">Business Value:</label>
                        <div class="p-2 bg-primary bg-opacity-10 border border-primary rounded text-light">
                            ${this.escapeHtml(refinedStory.business_value)}
                        </div>
                    </div>
                    ` : ''}

                    ${refinedStory.technical_notes ? `
                    <div class="col-md-12 mb-3">
                        <label class="form-label fw-bold text-light">Technical Notes:</label>
                        <div class="p-2 bg-info bg-opacity-10 border border-info rounded text-light">
                            ${this.escapeHtml(refinedStory.technical_notes)}
                        </div>
                    </div>
                    ` : ''}
                </div>

                <div class="d-flex justify-content-end gap-2 mt-4">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-success" id="applyRefinedChanges">
                        <i class="fas fa-save"></i> Apply Changes
                    </button>
                </div>
            </div>
        `;

        this.hideLoadingState();
    }

    toggleEditMode() {
        const container = document.getElementById('refinedStoryContent');
        const isEditMode = container.classList.contains('edit-mode');
        
        if (isEditMode) {
            // Switch to display mode
            container.classList.remove('edit-mode');
            container.querySelectorAll('.edit-mode').forEach(el => el.classList.add('d-none'));
            container.querySelectorAll('.display-mode').forEach(el => el.classList.remove('d-none'));
        } else {
            // Switch to edit mode
            container.classList.add('edit-mode');
            container.querySelectorAll('.display-mode').forEach(el => el.classList.add('d-none'));
            container.querySelectorAll('.edit-mode').forEach(el => el.classList.remove('d-none'));
        }
    }

    async applyRefinedChanges() {
        if (!this.currentStoryId || !this.refinedData) {
            this.showError('No refined data to apply');
            return;
        }

        // Collect current values (potentially edited)
        const container = document.getElementById('refinedStoryContent');
        const updatedData = {
            story_id: this.currentStoryId,
            title: container.querySelector('[data-field="title"] input, [data-field="title"] .display-mode')?.textContent?.trim() || this.refinedData.title,
            description: container.querySelector('[data-field="description"] textarea, [data-field="description"] .display-mode')?.textContent?.trim() || this.refinedData.description,
            priority: container.querySelector('[data-field="priority"] select, [data-field="priority"] .display-mode')?.textContent?.trim() || this.refinedData.priority,
            effort_estimate: container.querySelector('[data-field="effort_estimate"] select, [data-field="effort_estimate"] .display-mode')?.textContent?.trim() || this.refinedData.effort_estimate,
            acceptance_criteria: this.parseAcceptanceCriteria(container.querySelector('[data-field="acceptance_criteria"] textarea, [data-field="acceptance_criteria"] .display-mode'))
        };

        try {
            const response = await fetch('/api/ai/update-story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify(updatedData)
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccessNotification('Story updated successfully!');
                
                // Close modal and refresh page to show updates
                const modal = bootstrap.Modal.getInstance(document.getElementById('storyRefinementModal'));
                modal.hide();
                
                // Refresh the page to show updated story
                setTimeout(() => window.location.reload(), 500);
            } else {
                this.showError(data.error || 'Failed to update story');
            }
        } catch (error) {
            console.error('Story update error:', error);
            this.showError('Failed to update story');
        }
    }

    parseAcceptanceCriteria(element) {
        if (!element) return this.refinedData.acceptance_criteria;
        
        const content = element.tagName === 'TEXTAREA' ? element.value : element.textContent;
        return content.trim().split('\n').filter(line => line.trim().length > 0);
    }

    getPriorityBadgeClass(priority) {
        switch (priority?.toLowerCase()) {
            case 'high': return 'bg-danger';
            case 'medium': return 'bg-warning';
            case 'low': return 'bg-success';
            default: return 'bg-secondary';
        }
    }

    showLoadingState() {
        const container = document.getElementById('refinedStoryContent');
        if (container) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2 text-light">Analyzing story with AI...</p>
                </div>
            `;
        }
    }

    hideLoadingState() {
        // Loading is automatically hidden when content is displayed
    }

    resetModal() {
        this.currentStoryId = null;
        this.refinedData = null;
        const container = document.getElementById('refinedStoryContent');
        if (container) {
            container.innerHTML = '';
            container.classList.remove('edit-mode');
        }
    }

    showSuccessNotification(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'danger');
    }

    showNotification(message, type = 'info') {
        // Create and show Bootstrap alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text || '').replace(/[&<>"']/g, (m) => map[m]);
    }
}

// Initialize the story refinement manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.storyRefinement = new StoryRefinementManager();
});

// Fallback function for showSuccessNotification if not defined elsewhere
if (typeof showSuccessNotification === 'undefined') {
    window.showSuccessNotification = function(message) {
        if (window.storyRefinement) {
            window.storyRefinement.showSuccessNotification(message);
        }
    };
}