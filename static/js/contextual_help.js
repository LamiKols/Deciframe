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
        
        // Store modal reference and setup cleanup handlers
        this.modal = new bootstrap.Modal(document.getElementById('contextualHelpModal'));
        this.setupModalCleanup();
    }
    
    setupModalCleanup() {
        const modalElement = document.getElementById('contextualHelpModal');
        
        // Clean up modal backdrop and body state when hidden
        modalElement.addEventListener('hidden.bs.modal', () => {
            console.log('🔧 ContextualHelp: Modal hidden event fired, cleaning up');
            
            // Force remove any remaining backdrops
            setTimeout(() => {
                const backdrops = document.querySelectorAll('.modal-backdrop');
                console.log('🔧 ContextualHelp: Found', backdrops.length, 'backdrops to remove');
                backdrops.forEach(backdrop => {
                    console.log('🔧 ContextualHelp: Removing backdrop');
                    backdrop.remove();
                });
                
                // Restore body state
                document.body.classList.remove('modal-open');
                document.body.style.removeProperty('padding-right');
                document.body.style.removeProperty('overflow');
                
                console.log('🔧 ContextualHelp: Modal cleanup complete');
            }, 50); // Small delay to ensure Bootstrap has finished
        });
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
                
                console.log('🔧 ContextualHelp: Help icon clicked');
                
                const helpIcon = e.target.classList.contains('contextual-help-icon') ? 
                    e.target : e.target.closest('.contextual-help-icon');
                
                const helpUrl = helpIcon.getAttribute('data-help-url');
                console.log('🔧 ContextualHelp: Help URL from icon:', helpUrl);
                
                if (helpUrl) {
                    this.loadHelpContentFromUrl(helpUrl);
                } else {
                    console.warn('🔧 ContextualHelp: No help URL found on icon');
                }
            }
        });
    }

    async loadHelpContentFromUrl(helpUrl) {
        try {
            console.log('🔧 ContextualHelp: Loading content from URL:', helpUrl);
            
            // Show modal with loading spinner
            this.showModal('Help', '<div class="d-flex justify-content-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>');
            
            // Fetch help content directly from the URL
            const response = await fetch(helpUrl, {
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'text/html'
                }
            });
            
            console.log('🔧 ContextualHelp: Response status:', response.status);
            console.log('🔧 ContextualHelp: Response URL:', response.url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const html = await response.text();
            console.log('🔧 ContextualHelp: Response length:', html.length);
            console.log('🔧 ContextualHelp: First 200 chars:', html.substring(0, 200));
            
            // Extract content from the response HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Try multiple selectors to find content
            let content = doc.querySelector('.container .card');
            if (!content) {
                content = doc.querySelector('.card');
            }
            if (!content) {
                content = doc.querySelector('.container');
            }
            if (!content) {
                content = doc.querySelector('main');
            }
            
            console.log('🔧 ContextualHelp: Found content element:', !!content);
            
            if (content) {
                // Extract title from the card header or first h3
                const titleElement = content.querySelector('.card-header h3') || 
                                  content.querySelector('h3') || 
                                  content.querySelector('h2') ||
                                  content.querySelector('h1');
                const title = titleElement ? titleElement.textContent.trim() : 'Help';
                
                console.log('🔧 ContextualHelp: Extracted title:', title);
                
                // Update modal with content
                this.showModal(title, content.innerHTML);
            } else {
                console.warn('🔧 ContextualHelp: No suitable content found, showing raw HTML sample');
                this.showModal('Help Content', 
                    '<div class="alert alert-info">' +
                    '<h6>Content Preview</h6>' +
                    '<pre style="max-height: 400px; overflow: auto;">' + 
                    html.substring(0, 1000) + '...</pre>' +
                    '</div>'
                );
            }
            
        } catch (error) {
            console.error('🔧 ContextualHelp: Detailed error:', error);
            console.error('🔧 ContextualHelp: Error stack:', error.stack);
            
            this.showModal('Help Not Available', 
                '<div class="alert alert-warning">' +
                '<h6>Unable to load help content</h6>' +
                '<p>Error: ' + error.message + '</p>' +
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
        console.log('🔧 ContextualHelp: Showing modal with title:', title);
        
        // Update modal content
        document.getElementById('contextualHelpModalLabel').textContent = title;
        document.getElementById('contextualHelpContent').innerHTML = content;
        
        // Ensure any previous modal state is cleaned up
        this.forceCleanup();
        
        // Show the modal
        this.modal.show();
    }
    
    forceCleanup() {
        // Remove any stray backdrops that might be left behind
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        
        // Reset body state
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('padding-right');
        document.body.style.removeProperty('overflow');
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