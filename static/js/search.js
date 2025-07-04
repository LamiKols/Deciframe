/**
 * Search JavaScript - Handles navbar and main search functionality
 * Uses the simplified SQLAlchemy API at /api/search/
 */

class SearchManager {
    constructor() {
        this.initializeEventListeners();
        this.resultTemplate = document.getElementById('resultTemplate');
    }

    initializeEventListeners() {
        // Navbar search form
        const navSearchForm = document.getElementById('searchForm');
        if (navSearchForm) {
            navSearchForm.onsubmit = (e) => this.handleNavbarSearch(e);
        }

        // Main search form (on search page)
        const mainSearchForm = document.getElementById('mainSearchForm');
        if (mainSearchForm) {
            mainSearchForm.onsubmit = (e) => this.handleMainSearch(e);
        }

        // Handle URL parameters on page load
        this.handleUrlParameters();
    }

    async handleNavbarSearch(e) {
        e.preventDefault();
        const query = document.getElementById('searchInput').value.trim();
        if (query) {
            // Redirect to search page with query parameter
            window.location.href = `/search/?q=${encodeURIComponent(query)}`;
        }
    }

    async handleMainSearch(e) {
        e.preventDefault();
        const query = document.getElementById('mainSearchInput').value.trim();
        if (query) {
            // Update URL without reload
            const url = new URL(window.location);
            url.searchParams.set('q', query);
            window.history.pushState({}, '', url);
            
            // Perform search
            await this.performSearch(query);
        }
    }

    handleUrlParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        const query = urlParams.get('q');
        if (query) {
            const mainSearchInput = document.getElementById('mainSearchInput');
            if (mainSearchInput) {
                mainSearchInput.value = query;
                this.performSearch(query);
            }
        }
    }

    async performSearch(query) {
        this.showLoading(true);
        this.hideStates();

        try {
            const response = await fetch(`/api/search/?q=${encodeURIComponent(query)}`, {
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`Search failed: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            this.displayResults(data.results || [], query);

        } catch (error) {
            console.error('Search error:', error);
            this.showError(error.message);
        } finally {
            this.showLoading(false);
        }
    }

    displayResults(results, query) {
        const resultsContainer = document.getElementById('searchResults');
        if (!resultsContainer) return;

        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            this.showNoResults();
            return;
        }

        // Add search summary
        const summaryHtml = `
            <div class="col-12 mb-3">
                <p class="text-muted">
                    Found <strong>${results.length}</strong> result${results.length !== 1 ? 's' : ''} for "<strong>${this.escapeHtml(query)}</strong>"
                </p>
            </div>
        `;
        resultsContainer.innerHTML = summaryHtml;

        // Render each result
        results.forEach(result => {
            const resultElement = this.createResultElement(result);
            resultsContainer.appendChild(resultElement);
        });
    }

    createResultElement(result) {
        if (!this.resultTemplate) return document.createElement('div');

        const clone = this.resultTemplate.content.cloneNode(true);
        
        // Set type badge
        const typeBadge = clone.querySelector('.result-type-badge');
        typeBadge.textContent = this.formatType(result.type);
        typeBadge.classList.add(result.type);

        // Set relevance rank
        const rankElement = clone.querySelector('.result-rank');
        if (result.rank) {
            rankElement.textContent = `Relevance: ${(result.rank * 100).toFixed(1)}%`;
        } else {
            rankElement.style.display = 'none';
        }

        // Set title and link
        const linkElement = clone.querySelector('.result-link');
        linkElement.textContent = result.title || 'Untitled';
        linkElement.href = result.url || '#';

        // Set description
        const descElement = clone.querySelector('.result-description');
        if (result.description) {
            descElement.textContent = result.description.length > 150 
                ? result.description.substring(0, 150) + '...'
                : result.description;
        } else {
            descElement.style.display = 'none';
        }

        // Set code
        const codeElement = clone.querySelector('.result-code');
        if (result.code) {
            codeElement.textContent = result.code;
        } else {
            codeElement.style.display = 'none';
        }

        return clone;
    }

    formatType(type) {
        const typeMap = {
            'problems': 'Problem',
            'business_cases': 'Business Case',
            'projects': 'Project'
        };
        return typeMap[type] || type;
    }

    showLoading(show) {
        const loadingState = document.getElementById('loadingState');
        if (loadingState) {
            loadingState.style.display = show ? 'block' : 'none';
        }
    }

    showNoResults() {
        const noResultsState = document.getElementById('noResultsState');
        if (noResultsState) {
            noResultsState.style.display = 'block';
        }
    }

    showError(message) {
        const errorState = document.getElementById('errorState');
        const errorMessage = document.getElementById('errorMessage');
        if (errorState && errorMessage) {
            errorMessage.textContent = message;
            errorState.style.display = 'block';
        }
    }

    hideStates() {
        const states = ['noResultsState', 'errorState'];
        states.forEach(stateId => {
            const element = document.getElementById(stateId);
            if (element) {
                element.style.display = 'none';
            }
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize search manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.searchManager = new SearchManager();
});