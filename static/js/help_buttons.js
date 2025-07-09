/**
 * Help Button Integration System
 * Automatically adds contextual help buttons throughout the application
 */

// Configuration for help button placement
const HELP_BUTTON_CONFIG = {
    // Admin pages
    'admin/dashboard': { module: 'Admin', section: 'overview', placement: '.admin-dashboard-header' },
    'admin/users': { module: 'Admin', section: 'users', placement: '.users-header' },
    'admin/departments': { module: 'Admin', section: 'departments', placement: '.departments-header' },
    'admin/triage-rules': { module: 'Admin', section: 'triage', placement: '.triage-header' },
    'admin/workflows': { module: 'Admin', section: 'workflows', placement: '.workflows-header' },
    'admin/settings': { module: 'Admin', section: 'settings', placement: '.settings-header' },
    
    // Business pages
    'business/cases': { module: 'Business', section: 'cases', placement: '.business-cases-header' },
    'business/create': { module: 'Business', section: 'creation', placement: '.create-case-header' },
    'business/epics': { module: 'Business', section: 'epics', placement: '.epics-header' },
    
    // Project pages
    'projects/': { module: 'Projects', section: 'management', placement: '.projects-header' },
    'projects/dashboard': { module: 'Projects', section: 'dashboard', placement: '.project-dashboard-header' },
    'projects/milestones': { module: 'Projects', section: 'milestones', placement: '.milestones-header' },
    
    // Problem pages
    'problems/': { module: 'Problems', section: 'management', placement: '.problems-header' },
    'problems/report': { module: 'Problems', section: 'reporting', placement: '.report-problem-header' }
};

// Initialize help buttons when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeHelpButtons();
    addGlobalHelpButtons();
});

function initializeHelpButtons() {
    const currentPath = window.location.pathname;
    
    // Find matching configuration
    for (const [path, config] of Object.entries(HELP_BUTTON_CONFIG)) {
        if (currentPath.includes(path)) {
            addHelpButton(config);
            break;
        }
    }
}

function addHelpButton(config) {
    const targetElement = document.querySelector(config.placement);
    if (targetElement && !targetElement.querySelector('.contextual-help-icon')) {
        const helpButton = createHelpButton(config.module, config.section);
        targetElement.appendChild(helpButton);
    }
}

function createHelpButton(module, section, className = '', style = '') {
    const button = document.createElement('span');
    button.className = `contextual-help-icon ${className}`;
    button.setAttribute('data-help-url', `/help/?module=${module}&section=${section}`);
    button.style.cssText = `cursor: pointer; color: var(--bs-info); margin-left: 0.5rem; ${style}`;
    button.title = 'Get help for this section';
    button.innerHTML = '❓';
    
    return button;
}

function addGlobalHelpButtons() {
    // Add help buttons to common page elements
    addHelpToCardHeaders();
    addHelpToFormSections();
    addHelpToTableHeaders();
    addHelpToDashboardCards();
}

function addHelpToCardHeaders() {
    const cardHeaders = document.querySelectorAll('.card-header h1, .card-header h2, .card-header h3, .card-header h4, .card-header h5, .card-header h6');
    
    cardHeaders.forEach(header => {
        if (header.querySelector('.contextual-help-icon')) return;
        
        const headerText = header.textContent.toLowerCase().trim();
        const helpConfig = getHelpConfigForText(headerText);
        
        if (helpConfig) {
            const helpButton = createHelpButton(helpConfig.module, helpConfig.section, 'ms-2');
            header.appendChild(helpButton);
        }
    });
}

function addHelpToFormSections() {
    const formHeaders = document.querySelectorAll('fieldset legend, .form-section h1, .form-section h2, .form-section h3, .form-section h4, .form-section h5, .form-section h6');
    
    formHeaders.forEach(header => {
        if (header.querySelector('.contextual-help-icon')) return;
        
        const headerText = header.textContent.toLowerCase().trim();
        const helpConfig = getHelpConfigForText(headerText);
        
        if (helpConfig) {
            const helpButton = createHelpButton(helpConfig.module, helpConfig.section, 'ms-2');
            header.appendChild(helpButton);
        }
    });
}

function addHelpToTableHeaders() {
    const tableHeaders = document.querySelectorAll('.table-responsive-header, .table-header, .datatable-header');
    
    tableHeaders.forEach(header => {
        if (header.querySelector('.contextual-help-icon')) return;
        
        const headerText = header.textContent.toLowerCase().trim();
        const helpConfig = getHelpConfigForText(headerText);
        
        if (helpConfig) {
            const helpButton = createHelpButton(helpConfig.module, helpConfig.section, 'ms-2');
            header.appendChild(helpButton);
        }
    });
}

function addHelpToDashboardCards() {
    const dashboardCards = document.querySelectorAll('.dashboard-card .card-title, .metric-card .card-title, .stat-card .card-title');
    
    dashboardCards.forEach(title => {
        if (title.querySelector('.contextual-help-icon')) return;
        
        const titleText = title.textContent.toLowerCase().trim();
        const helpConfig = getHelpConfigForText(titleText);
        
        if (helpConfig) {
            const helpButton = createHelpButton(helpConfig.module, helpConfig.section, 'ms-2', 'font-size: 0.8em;');
            title.appendChild(helpButton);
        }
    });
}

function getHelpConfigForText(text) {
    // Map common text patterns to help configurations
    const patterns = {
        // Admin patterns
        'user': { module: 'Admin', section: 'users' },
        'department': { module: 'Admin', section: 'departments' },
        'triage': { module: 'Admin', section: 'triage' },
        'workflow': { module: 'Admin', section: 'workflows' },
        'setting': { module: 'Admin', section: 'settings' },
        'configuration': { module: 'Admin', section: 'settings' },
        
        // Business patterns
        'business case': { module: 'Business', section: 'cases' },
        'epic': { module: 'Business', section: 'epics' },
        'story': { module: 'Business', section: 'epics' },
        'requirement': { module: 'Business', section: 'epics' },
        'approval': { module: 'Business', section: 'approval' },
        
        // Project patterns
        'project': { module: 'Projects', section: 'management' },
        'milestone': { module: 'Projects', section: 'milestones' },
        'task': { module: 'Projects', section: 'management' },
        'backlog': { module: 'Projects', section: 'management' },
        
        // Problem patterns
        'problem': { module: 'Problems', section: 'management' },
        'issue': { module: 'Problems', section: 'reporting' },
        'report': { module: 'Problems', section: 'reporting' },
        
        // Dashboard patterns
        'dashboard': { module: 'Admin', section: 'overview' },
        'overview': { module: 'Admin', section: 'overview' },
        'summary': { module: 'Admin', section: 'overview' },
        'metrics': { module: 'Admin', section: 'overview' },
        'analytics': { module: 'Admin', section: 'overview' }
    };
    
    // Find matching pattern
    for (const [pattern, config] of Object.entries(patterns)) {
        if (text.includes(pattern)) {
            return config;
        }
    }
    
    return null;
}

// Function to manually add help button to specific elements
function addHelpButtonToElement(selector, module, section) {
    const element = document.querySelector(selector);
    if (element && !element.querySelector('.contextual-help-icon')) {
        const helpButton = createHelpButton(module, section, 'ms-2');
        element.appendChild(helpButton);
    }
}

// Function to add help button with custom text
function addCustomHelpButton(selector, helpUrl, title = 'Get help for this section') {
    const element = document.querySelector(selector);
    if (element && !element.querySelector('.contextual-help-icon')) {
        const button = document.createElement('span');
        button.className = 'contextual-help-icon ms-2';
        button.setAttribute('data-help-url', helpUrl);
        button.style.cssText = 'cursor: pointer; color: var(--bs-info); margin-left: 0.5rem;';
        button.title = title;
        button.innerHTML = '❓';
        element.appendChild(button);
    }
}

// Export functions for manual use
window.HelpButtons = {
    addHelpButtonToElement,
    addCustomHelpButton,
    createHelpButton
};