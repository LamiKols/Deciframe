/**
 * Story Refinement Manager
 * Handles modal interactions and API communication for project backlog management
 */
class StoryRefinementManager {
    constructor() {
        this.currentProjectId = null;
        this.currentEpicId = null;
        this.currentStoryId = null;
        this.isLoading = false;
    }

    init() {
        this.loadProjectData();
        this.bindEvents();
    }

    bindEvents() {
        // Create Epic Modal
        $(document).on('click', '.create-epic-btn', () => {
            this.openNewEpicModal();
        });

        $(document).on('click', '#newEpicModal .btn-primary', () => {
            this.createEpic();
        });

        // Edit Epic Modal
        $(document).on('click', '.edit-epic-btn', (e) => {
            const epicId = $(e.target).data('epic-id');
            const title = $(e.target).data('epic-title');
            const description = $(e.target).data('epic-description');
            this.openEditEpicModal(epicId, title, description);
        });

        $(document).on('click', '#editEpicModal .btn-primary', () => {
            this.updateEpic();
        });

        // Create Story Modal
        $(document).on('click', '.add-story-btn', (e) => {
            const epicId = $(e.target).data('epic-id');
            this.openNewStoryModal(epicId);
        });

        $(document).on('click', '#newStoryModal .btn-primary', () => {
            this.createStory();
        });

        // Edit Story Modal
        $(document).on('click', '.edit-story-btn', (e) => {
            const storyId = $(e.target).data('story-id');
            this.openEditStoryModal(storyId);
        });

        $(document).on('click', '#editStoryModal .btn-primary', () => {
            this.saveStory();
        });

        // Delete Story
        $(document).on('click', '.delete-story-btn', (e) => {
            const storyId = $(e.target).data('story-id');
            this.deleteStory(storyId);
        });

        // Refresh button
        $(document).on('click', '.refresh-backlog-btn', () => {
            this.loadProjectData();
        });
    }

    loadProjectData() {
        // Extract project ID from URL or data attribute
        const urlParts = window.location.pathname.split('/');
        this.currentProjectId = urlParts[urlParts.indexOf('projects') + 1];
        
        if (!this.currentProjectId) {
            console.error('Project ID not found');
            return;
        }

        this.fetchProjectBacklog();
    }

    fetchProjectBacklog() {
        this.showLoadingState();
        
        fetch(`/api/ai/epics-stories/${this.currentProjectId}`, {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            this.renderProjectBacklog(data);
            this.hideLoadingState();
        })
        .catch(error => {
            console.error('Error fetching project backlog:', error);
            this.showErrorNotification('Failed to load project backlog: ' + error.message);
            this.hideLoadingState();
        });
    }

    renderProjectBacklog(data) {
        const container = $('#project-backlog-container');
        
        if (!data.epics || data.epics.length === 0) {
            container.html(`
                <div class="alert alert-info">
                    <h5>No Epics Found</h5>
                    <p>This project doesn't have any epics yet. Create your first epic to start organizing user stories.</p>
                    <button class="btn btn-primary create-epic-btn">
                        <i class="fas fa-plus"></i> Create First Epic
                    </button>
                </div>
            `);
            return;
        }

        let html = `
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h4>Project Backlog</h4>
                <div>
                    <button class="btn btn-outline-primary create-epic-btn me-2">
                        <i class="fas fa-plus"></i> Add Epic
                    </button>
                    <button class="btn btn-outline-secondary refresh-backlog-btn">
                        <i class="fas fa-sync"></i> Refresh
                    </button>
                </div>
            </div>
        `;

        data.epics.forEach(epic => {
            html += this.renderEpicCard(epic);
        });

        container.html(html);
    }

    renderEpicCard(epic) {
        const stories = epic.stories || [];
        const storiesHtml = stories.map(story => this.renderStoryCard(story)).join('');
        
        return `
            <div class="card bg-dark border-secondary mb-4">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div>
                        <h5 class="text-light mb-0">${this.escapeHtml(epic.title)}</h5>
                        <small class="text-muted">${this.escapeHtml(epic.description || '')}</small>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-outline-primary me-2 edit-epic-btn" 
                                data-epic-id="${epic.id}"
                                data-epic-title="${this.escapeHtml(epic.title)}"
                                data-epic-description="${this.escapeHtml(epic.description || '')}">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="btn btn-sm btn-outline-success add-story-btn" 
                                data-epic-id="${epic.id}">
                            <i class="fas fa-plus"></i> Add Story
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    ${stories.length === 0 ? 
                        '<p class="text-muted">No stories yet. Click "Add Story" to create the first one.</p>' : 
                        `<div class="row">${storiesHtml}</div>`
                    }
                </div>
            </div>
        `;
    }

    renderStoryCard(story) {
        const priorityClass = {
            'High': 'text-danger',
            'Medium': 'text-warning',
            'Low': 'text-success'
        }[story.priority] || 'text-muted';

        return `
            <div class="col-md-6 mb-3">
                <div class="card bg-secondary border-light">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title text-light">${this.escapeHtml(story.title)}</h6>
                            <div class="dropdown">
                                <button class="btn btn-sm btn-outline-light dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                    <i class="fas fa-ellipsis-v"></i>
                                </button>
                                <ul class="dropdown-menu">
                                    <li><a class="dropdown-item edit-story-btn" href="#" data-story-id="${story.id}">
                                        <i class="fas fa-edit"></i> Edit
                                    </a></li>
                                    <li><a class="dropdown-item delete-story-btn text-danger" href="#" data-story-id="${story.id}">
                                        <i class="fas fa-trash"></i> Delete
                                    </a></li>
                                </ul>
                            </div>
                        </div>
                        <p class="card-text text-light small">${this.escapeHtml(story.description || '')}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="badge ${priorityClass}">${story.priority || 'Medium'}</span>
                            <small class="text-muted">${story.effort_estimate || 'Not estimated'}</small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    openEditStoryModal(storyId) {
        this.currentStoryId = storyId;
        
        // Fetch story details
        fetch(`/api/stories/${storyId}`, {
            method: 'GET',
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const story = data.story;
                $('#editStoryTitle').val(story.title || '');
                $('#editStoryDescription').val(story.description || '');
                $('#editStoryPriority').val(story.priority || 'Medium');
                $('#editStoryEffort').val(story.effort_estimate || '');
                
                const modal = new bootstrap.Modal(document.getElementById('editStoryModal'));
                modal.show();
            } else {
                this.showErrorNotification('Failed to load story details');
            }
        })
        .catch(error => {
            console.error('Error loading story:', error);
            this.showErrorNotification('Failed to load story details');
        });
    }

    openNewEpicModal() {
        $('#newEpicTitle').val('');
        $('#newEpicDescription').val('');
        
        const modal = new bootstrap.Modal(document.getElementById('newEpicModal'));
        modal.show();
    }

    openEditEpicModal(epicId, title, description) {
        this.currentEpicId = epicId;
        $('#editEpicTitle').val(title);
        $('#editEpicDescription').val(description);
        
        const modal = new bootstrap.Modal(document.getElementById('editEpicModal'));
        modal.show();
    }

    openNewStoryModal(epicId) {
        this.currentEpicId = epicId;
        $('#newStoryTitle').val('');
        $('#newStoryDescription').val('');
        $('#newStoryPriority').val('Medium');
        $('#newStoryEffort').val('');
        
        const modal = new bootstrap.Modal(document.getElementById('newStoryModal'));
        modal.show();
    }

    saveStory() {
        const title = $('#editStoryTitle').val().trim();
        const description = $('#editStoryDescription').val().trim();
        const priority = $('#editStoryPriority').val();
        const effort = $('#editStoryEffort').val();
        
        if (!title) {
            this.showErrorNotification('Story title is required');
            return;
        }
        
        const data = {
            title: title,
            description: description,
            priority: priority,
            effort_estimate: effort
        };
        
        fetch(`/api/stories/${this.currentStoryId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                $('#editStoryModal').modal('hide');
                this.showSuccessNotification('Story updated successfully');
                this.fetchProjectBacklog();
            } else {
                this.showErrorNotification(data.error || 'Failed to update story');
            }
        })
        .catch(error => {
            console.error('Error updating story:', error);
            this.showErrorNotification('Failed to update story');
        });
    }

    createEpic() {
        const title = $('#newEpicTitle').val().trim();
        const description = $('#newEpicDescription').val().trim();
        
        if (!title) {
            this.showErrorNotification('Epic title is required');
            return;
        }
        
        const data = {
            title: title,
            description: description,
            project_id: this.currentProjectId
        };
        
        fetch('/api/epics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                $('#newEpicModal').modal('hide');
                this.showSuccessNotification('Epic created successfully');
                this.fetchProjectBacklog();
            } else {
                this.showErrorNotification(data.error || 'Failed to create epic');
            }
        })
        .catch(error => {
            console.error('Error creating epic:', error);
            this.showErrorNotification('Failed to create epic');
        });
    }

    updateEpic() {
        const title = $('#editEpicTitle').val().trim();
        const description = $('#editEpicDescription').val().trim();
        
        if (!title) {
            this.showErrorNotification('Epic title is required');
            return;
        }
        
        const data = {
            title: title,
            description: description
        };
        
        fetch(`/api/epics/${this.currentEpicId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                $('#editEpicModal').modal('hide');
                this.showSuccessNotification('Epic updated successfully');
                this.fetchProjectBacklog();
            } else {
                this.showErrorNotification(data.error || 'Failed to update epic');
            }
        })
        .catch(error => {
            console.error('Error updating epic:', error);
            this.showErrorNotification('Failed to update epic');
        });
    }

    createStory() {
        const title = $('#newStoryTitle').val().trim();
        const description = $('#newStoryDescription').val().trim();
        const priority = $('#newStoryPriority').val();
        const effort = $('#newStoryEffort').val();
        
        if (!title) {
            this.showErrorNotification('Story title is required');
            return;
        }
        
        const data = {
            title: title,
            description: description,
            priority: priority,
            effort_estimate: effort,
            epic_id: this.currentEpicId,
            project_id: this.currentProjectId
        };
        
        fetch('/api/stories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                $('#newStoryModal').modal('hide');
                this.showSuccessNotification('Story created successfully');
                this.fetchProjectBacklog();
            } else {
                this.showErrorNotification(data.error || 'Failed to create story');
            }
        })
        .catch(error => {
            console.error('Error creating story:', error);
            this.showErrorNotification('Failed to create story');
        });
    }

    deleteStory(storyId) {
        if (!confirm('Are you sure you want to delete this story? This action cannot be undone.')) {
            return;
        }
        
        fetch(`/api/stories/${storyId}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showSuccessNotification('Story deleted successfully');
                this.fetchProjectBacklog();
            } else {
                this.showErrorNotification(data.error || 'Failed to delete story');
            }
        })
        .catch(error => {
            console.error('Error deleting story:', error);
            this.showErrorNotification('Failed to delete story');
        });
    }

    showLoadingState() {
        this.isLoading = true;
        $('#project-backlog-container').html(`
            <div class="text-center p-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="text-muted mt-2">Loading project backlog...</p>
            </div>
        `);
    }

    hideLoadingState() {
        this.isLoading = false;
    }

    showSuccessNotification(message) {
        this.showNotification(message, 'success');
    }

    showErrorNotification(message) {
        this.showNotification(message, 'danger');
    }

    showNotification(message, type) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3" 
                 style="z-index: 9999; max-width: 400px;" role="alert">
                ${this.escapeHtml(message)}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        $('body').append(alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            $('.alert:last').fadeOut(() => {
                $('.alert:last').remove();
            });
        }, 5000);
    }

    escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// Global notification functions for compatibility
function showSuccessNotification(message) {
    if (window.storyManager) {
        window.storyManager.showSuccessNotification(message);
    } else {
        console.log('Success:', message);
    }
}

function showErrorNotification(message) {
    if (window.storyManager) {
        window.storyManager.showErrorNotification(message);
    } else {
        console.error('Error:', message);
    }
}

// Initialize when DOM is ready
$(document).ready(function() {
    // Only initialize on project backlog pages
    if (window.location.pathname.includes('/projects/') && window.location.pathname.includes('/backlog')) {
        window.storyManager = new StoryRefinementManager();
        window.storyManager.init();
    }
});