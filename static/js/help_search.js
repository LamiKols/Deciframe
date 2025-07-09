/**
 * Help Center Search and Filtering Functions
 * Provides real-time search and filtering capabilities
 */

// Global variables for search state
let searchTimer = null;
let articles = [];

// Initialize search functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
    loadArticleData();
});

function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    const moduleFilter = document.getElementById('moduleFilter');
    const roleFilter = document.getElementById('roleFilter');
    
    // Real-time search with debouncing
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(performSearch, 300);
        });
    }
    
    // Filter change handlers
    if (moduleFilter) {
        moduleFilter.addEventListener('change', performSearch);
    }
    
    if (roleFilter) {
        roleFilter.addEventListener('change', performSearch);
    }
}

function loadArticleData() {
    // Load article data from the page for client-side filtering
    const articleCards = document.querySelectorAll('.article-card');
    articles = Array.from(articleCards).map(card => ({
        element: card,
        title: card.querySelector('.card-header h6').textContent.toLowerCase(),
        content: card.querySelector('.card-text').textContent.toLowerCase(),
        module: card.dataset.module || '',
        role: card.dataset.role || '',
        tags: card.dataset.tags || ''
    }));
}

function performSearch() {
    const searchQuery = document.getElementById('searchInput')?.value.toLowerCase().trim() || '';
    const moduleFilter = document.getElementById('moduleFilter')?.value || '';
    const roleFilter = document.getElementById('roleFilter')?.value || '';
    
    let filteredArticles = articles;
    
    // Apply search filter
    if (searchQuery) {
        filteredArticles = filteredArticles.filter(article => 
            article.title.includes(searchQuery) ||
            article.content.includes(searchQuery) ||
            article.tags.includes(searchQuery)
        );
    }
    
    // Apply module filter
    if (moduleFilter) {
        filteredArticles = filteredArticles.filter(article => 
            article.module === moduleFilter
        );
    }
    
    // Apply role filter
    if (roleFilter) {
        filteredArticles = filteredArticles.filter(article => 
            article.role === roleFilter || (roleFilter === 'both' && !article.role)
        );
    }
    
    // Show/hide articles based on filters
    articles.forEach(article => {
        const isVisible = filteredArticles.includes(article);
        article.element.style.display = isVisible ? 'block' : 'none';
    });
    
    // Update results count
    updateResultsCount(filteredArticles.length, articles.length);
    
    // Show no results message if needed
    showNoResultsMessage(filteredArticles.length === 0);
}

function updateResultsCount(filtered, total) {
    let resultsElement = document.getElementById('searchResults');
    
    if (!resultsElement) {
        // Create results element if it doesn't exist
        resultsElement = document.createElement('div');
        resultsElement.id = 'searchResults';
        resultsElement.className = 'alert alert-info mb-3';
        
        const container = document.getElementById('articlesContainer');
        if (container) {
            container.insertBefore(resultsElement, container.firstChild);
        }
    }
    
    if (filtered < total) {
        resultsElement.style.display = 'block';
        resultsElement.innerHTML = `<i class="fas fa-search me-2"></i>Showing ${filtered} of ${total} articles`;
    } else {
        resultsElement.style.display = 'none';
    }
}

function showNoResultsMessage(show) {
    let noResultsElement = document.getElementById('noResults');
    
    if (!noResultsElement && show) {
        // Create no results element
        noResultsElement = document.createElement('div');
        noResultsElement.id = 'noResults';
        noResultsElement.className = 'text-center py-5';
        noResultsElement.innerHTML = `
            <i class="fas fa-search fa-3x text-muted mb-3"></i>
            <h5 class="text-muted">No articles found</h5>
            <p class="text-muted">Try adjusting your search terms or filters</p>
            <button class="btn btn-outline-primary" onclick="clearAllFilters()">
                <i class="fas fa-times me-2"></i>Clear Filters
            </button>
        `;
        
        const articlesList = document.getElementById('articlesList');
        if (articlesList) {
            articlesList.appendChild(noResultsElement);
        }
    } else if (noResultsElement) {
        noResultsElement.style.display = show ? 'block' : 'none';
    }
}

function clearAllFilters() {
    // Clear all form inputs
    const searchInput = document.getElementById('searchInput');
    const moduleFilter = document.getElementById('moduleFilter');
    const roleFilter = document.getElementById('roleFilter');
    
    if (searchInput) searchInput.value = '';
    if (moduleFilter) moduleFilter.value = '';
    if (roleFilter) roleFilter.value = '';
    
    // Perform search to show all articles
    performSearch();
}

// Legacy function names for backward compatibility
function searchArticles() {
    performSearch();
}

function filterByModule() {
    performSearch();
}

function filterByRole() {
    performSearch();
}