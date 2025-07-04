/**
 * Contextual Help System
 * Provides "❓" icons throughout the app that open modals with relevant help content
 */

class ContextualHelp {
    constructor() {
        this.modal = null;
        this.init();
    }

    init() {
        // Create the help modal HTML if it doesn't exist
        if (!document.getElementById('contextualHelpModal')) {
            this.createModal();
        }
        
        // Initialize event listeners for help icons
        this.bindHelpIcons();
        
        // Store modal reference
        this.modal = new bootstrap.Modal(document.getElementById('contextualHelpModal'));
    }

    createModal() {
        const modalHtml = `
            <div class="modal fade" id="contextualHelpModal" tabindex="-1" aria-labelledby="contextualHelpModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="contextualHelpModalLabel">Help</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" id="contextualHelpContent">
                            <div class="d-flex justify-content-center">
                                <div class="spinner-border" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <a href="/help" class="btn btn-primary">Browse All Help</a>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Append modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    bindHelpIcons() {
        // Use event delegation to handle dynamically added help icons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('contextual-help-icon') || 
                e.target.closest('.contextual-help-icon')) {
                e.preventDefault();
                
                const helpIcon = e.target.classList.contains('contextual-help-icon') ? 
                    e.target : e.target.closest('.contextual-help-icon');
                
                const helpSlug = helpIcon.getAttribute('data-help-slug');
                if (helpSlug) {
                    this.loadHelpContent(helpSlug);
                }
            }
        });
    }

    async loadHelpContent(slug) {
        try {
            // Show modal with loading spinner
            this.showModal('Help', '<div class="d-flex justify-content-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>');
            
            // Fetch help content via AJAX
            const response = await fetch(`/help/${slug}?partial=1`, {
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Update modal with content
            this.showModal(data.title, data.content);
            
        } catch (error) {
            console.error('Error loading help content:', error);
            this.showModal('Help Not Available', 
                '<div class="alert alert-warning">' +
                '<h6>Unable to load help content</h6>' +
                '<p>Please try again later or <a href="/help" class="alert-link">browse the help center</a>.</p>' +
                '</div>'
            );
        }
    }

    showModal(title, content) {
        document.getElementById('contextualHelpModalLabel').textContent = title;
        document.getElementById('contextualHelpContent').innerHTML = content;
        this.modal.show();
    }

    // Static method to create help icons
    static createHelpIcon(slug, className = '') {
        return `<span class="contextual-help-icon ${className}" 
                      data-help-slug="${slug}" 
                      style="cursor: pointer; color: var(--bs-info); margin-left: 0.5rem;"
                      title="Get help for this section">❓</span>`;
    }

    // Static method to add help icons to existing elements
    static addHelpIcon(element, slug) {
        if (element && !element.querySelector('.contextual-help-icon')) {
            element.insertAdjacentHTML('beforeend', ContextualHelp.createHelpIcon(slug));
        }
    }
}

// Initialize contextual help when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new ContextualHelp();
});

// Global helper function for templates
window.ContextualHelp = ContextualHelp;