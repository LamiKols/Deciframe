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
                
                const helpUrl = helpIcon.getAttribute('data-help-url');
                if (helpUrl) {
                    this.loadHelpContentFromUrl(helpUrl);
                }
            }
        });
    }

    async loadHelpContentFromUrl(helpUrl) {
        try {
            // Show modal with loading spinner
            this.showModal('Help', '<div class="d-flex justify-content-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>');
            
            // Fetch help content directly from the URL
            const response = await fetch(helpUrl, {
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const html = await response.text();
            
            // Extract content from the response HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const content = doc.querySelector('.container .card') || doc.querySelector('.container');
            
            if (content) {
                // Extract title from the card header or first h3
                const titleElement = content.querySelector('.card-header h3') || content.querySelector('h3') || content.querySelector('h2');
                const title = titleElement ? titleElement.textContent.trim() : 'Help';
                
                // Update modal with content
                this.showModal(title, content.innerHTML);
            } else {
                throw new Error('No content found in response');
            }
            
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

    // Keep the old method for backward compatibility
    async loadHelpContent(slug) {
        const helpUrl = `/help/${slug}`;
        return this.loadHelpContentFromUrl(helpUrl);
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