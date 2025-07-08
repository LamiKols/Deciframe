/**
 * DeciFrame Theme Toggle System
 * Handles dynamic theme switching between light and dark modes
 */

class ThemeManager {
    constructor() {
        this.init();
    }

    init() {
        // Initialize theme system on page load
        this.applyTheme(this.getUserEffectiveTheme());
        this.createToggleButton();
        this.setupEventListeners();
    }

    getUserEffectiveTheme() {
        // Use theme data from server context
        if (window.THEME_DATA) {
            return window.THEME_DATA.effective_theme || 'light';
        }
        
        // Fallback to light theme
        return 'light';
    }

    applyTheme(theme) {
        // Apply theme to HTML element
        document.documentElement.setAttribute('data-theme', theme);
        
        // Update theme toggle button if it exists
        this.updateToggleButton();
        
        // Update any charts or dynamic content
        this.updateCharts();
    }

    toggleTheme() {
        const currentTheme = this.getCurrentTheme();
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        // Apply theme immediately for smooth transition
        this.applyTheme(newTheme);
        
        // Save preference to server
        this.saveThemePreference(newTheme);
    }

    saveThemePreference(theme) {
        // Only save if user is logged in
        if (!window.THEME_DATA || window.THEME_DATA.user_theme === undefined) {
            return;
        }

        fetch('/auth/update-theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({ theme: theme })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update local theme data
                if (window.THEME_DATA) {
                    window.THEME_DATA.user_theme = theme;
                    window.THEME_DATA.effective_theme = theme;
                }
                console.log('Theme preference saved:', theme);
            } else {
                console.error('Failed to save theme preference:', data.error);
            }
        })
        .catch(error => {
            console.error('Error saving theme preference:', error);
        });
    }

    getCSRFToken() {
        // Get CSRF token from meta tag if available
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            return csrfMeta.getAttribute('content');
        }
        
        // Fallback: get from form if available
        const csrfInput = document.querySelector('input[name="csrf_token"]');
        if (csrfInput) {
            return csrfInput.value;
        }
        
        return '';
    }

    createToggleButton() {
        // Theme toggle button is created in HTML template
        // This method can be used for dynamic button creation if needed
    }

    updateToggleButton() {
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');
        const currentTheme = this.getCurrentTheme();
        
        if (themeIcon && themeText) {
            if (currentTheme === 'dark') {
                themeIcon.textContent = '☀️';
                themeText.textContent = 'Light Mode';
            } else {
                themeIcon.textContent = '🌙';
                themeText.textContent = 'Dark Mode';
            }
        }
    }

    updateCharts() {
        // Update Chart.js charts if they exist
        if (window.Chart && window.Chart.instances) {
            Object.values(window.Chart.instances).forEach(chart => {
                this.updateChartTheme(chart);
            });
        }
    }

    updateChartTheme(chart) {
        const currentTheme = this.getCurrentTheme();
        const textColor = currentTheme === 'dark' ? '#ffffff' : '#212529';
        const gridColor = currentTheme === 'dark' ? '#495057' : '#dee2e6';
        
        if (chart.options) {
            // Update chart colors based on theme
            if (chart.options.plugins && chart.options.plugins.legend) {
                chart.options.plugins.legend.labels.color = textColor;
            }
            
            if (chart.options.scales) {
                Object.keys(chart.options.scales).forEach(scale => {
                    if (chart.options.scales[scale].ticks) {
                        chart.options.scales[scale].ticks.color = textColor;
                    }
                    if (chart.options.scales[scale].grid) {
                        chart.options.scales[scale].grid.color = gridColor;
                    }
                });
            }
            
            chart.update();
        }
    }

    setupEventListeners() {
        // Listen for system theme changes
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addListener((e) => {
                // Only respond to system changes if user hasn't set a preference
                if (window.THEME_DATA && !window.THEME_DATA.user_theme) {
                    const newTheme = e.matches ? 'dark' : 'light';
                    this.applyTheme(newTheme);
                }
            });
        }
    }

    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    }

    setTheme(theme) {
        this.applyTheme(theme);
        this.saveThemePreference(theme);
    }
}

// Global function for theme toggle (called from HTML)
function toggleTheme() {
    if (window.themeManager) {
        window.themeManager.toggleTheme();
    }
}

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.themeManager = new ThemeManager();
});

// Export for module use if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}