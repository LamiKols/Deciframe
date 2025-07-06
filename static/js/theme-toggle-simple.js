/**
 * Simple Theme Toggle System
 * Template-based theme switching using separate CSS files
 */

function toggleTheme() {
    const currentTheme = document.querySelector('body').classList.contains('theme-dark') ? 'dark' : 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    // Update theme preference on server
    fetch('/auth/update-theme', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ theme: newTheme })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload page to apply new theme CSS
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error updating theme:', error);
    });
}

function getCsrfToken() {
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    return csrfToken ? csrfToken.getAttribute('content') : '';
}

// Initialize theme toggle on page load
document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle is ready
    console.log('Theme toggle initialized');
});