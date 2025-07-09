/**
 * AI Solution Recommendation Engine
 * Provides intelligent solution suggestions for problems
 */

class SolutionRecommendationEngine {
    constructor(problemId) {
        this.problemId = problemId;
        this.modal = null;
        this.isSuggesting = false;
        this.init();
    }

    init() {
        const suggestBtn = document.getElementById('aiSuggestBtn');
        if (suggestBtn) {
            suggestBtn.addEventListener('click', () => this.suggestSolutions());
        }
    }

    async suggestSolutions() {
        if (this.isSuggesting) return;

        this.isSuggesting = true;
        this.showLoadingState();

        try {
            // Get auth token from URL params for JWT authentication
            const urlParams = new URLSearchParams(window.location.search);
            const authToken = urlParams.get('auth_token');
            
            let url = '/api/ai/suggest-solutions';
            if (authToken) {
                url += `?auth_token=${authToken}`;
            }
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'include',
                body: JSON.stringify({ problem_id: this.problemId })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate solution suggestions');
            }

            // Debug logging
            console.log('AI Response received:', data);
            
            // Handle different response formats
            const solutions = data.solutions || data.variants || [];
            const problemTitle = data.problem_title || 'Current Problem';
            
            console.log('Parsed solutions:', solutions);
            console.log('Solutions count:', solutions.length);
            
            if (Array.isArray(solutions) && solutions.length > 0) {
                this.displaySolutions(solutions, problemTitle);
            } else {
                throw new Error(`No solutions received from server. Response: ${JSON.stringify(data)}`);
            }

        } catch (error) {
            console.error('Solution suggestion error:', error);
            
            // Show a user-friendly error message
            this.showError('Unable to generate solutions at this time. Please try again later.');
        } finally {
            this.isSuggesting = false;
            this.hideLoadingState();
        }
    }

    showLoadingState() {
        const btn = document.getElementById('aiSuggestBtn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Generating Solutions...';
        }
    }

    hideLoadingState() {
        const btn = document.getElementById('aiSuggestBtn');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-lightbulb me-1"></i>AI Suggest Solutions';
        }
    }

    displaySolutions(solutions, problemTitle) {
        const container = document.getElementById('aiSolutions');
        if (!container) return;

        container.innerHTML = `
            <div class="mb-3">
                <h6>AI-Generated Solutions for: "${this.escapeHtml(problemTitle)}"</h6>
                <p class="text-muted">Select a solution to create it in the system</p>
            </div>
            ${solutions.map((solution, index) => this.createSolutionCard(solution, index)).join('')}
        `;

        // Attach event listeners
        container.querySelectorAll('.select-solution').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const name = decodeURIComponent(e.target.dataset.name);
                const description = decodeURIComponent(e.target.dataset.desc);
                this.createSolution(name, description, e.target);
            });
        });

        // Show modal
        this.showModal();
    }

    createSolutionCard(solution, index) {
        return `
            <div class="card mb-3 bg-dark border-secondary">
                <div class="card-header bg-success text-white">
                    <h6 class="mb-0">
                        <i class="fas fa-lightbulb me-2"></i>
                        Solution ${index + 1}: ${this.escapeHtml(solution.title)}
                    </h6>
                </div>
                <div class="card-body">
                    <p class="card-text">${this.escapeHtml(solution.description)}</p>
                    <button class="btn btn-primary select-solution" 
                            data-name="${encodeURIComponent(solution.title)}"
                            data-desc="${encodeURIComponent(solution.description)}">
                        <i class="fas fa-plus me-1"></i>Create This Solution
                    </button>
                </div>
            </div>
        `;
    }

    async createSolution(name, description, button) {
        try {
            // Show loading state on button
            const originalText = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Creating...';

            const response = await fetch('/solutions/api/solutions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    problem_id: this.problemId,
                    title: name,
                    description: description
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Solution API error:', errorText);
                throw new Error('Failed to create solution');
            }

            const result = await response.json();
            console.log('Solution created successfully:', result);
            
            // Redirect directly to pre-populated business case form
            window.location.href = `/business/cases/new?problem_id=${this.problemId}&solution_id=${result.id}`;

        } catch (error) {
            console.error('Solution creation error:', error);
            this.showError(error.message || 'Failed to create solution');
            
            // Restore button
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    showModal() {
        const modalElement = document.getElementById('aiSuggestModal');
        if (modalElement) {
            this.modal = new bootstrap.Modal(modalElement);
            this.modal.show();
        }
    }

    hideModal() {
        if (this.modal) {
            this.modal.hide();
        }
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showAlert(message, type) {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alert);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Get problem ID from the page
    const problemIdElement = document.querySelector('[data-problem-id]');
    if (problemIdElement) {
        const problemId = problemIdElement.getAttribute('data-problem-id');
        new SolutionRecommendationEngine(parseInt(problemId));
    }
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SolutionRecommendationEngine;
}