/**
 * AI Requirements Auto-Fill Functionality
 * Handles one-click population of requirements form fields
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Requirements auto-fill script loaded');
    
    const aiButton = document.getElementById('aiSuggestAnswersBtn');
    if (aiButton) {
        console.log('AI suggest answers button found, attaching handler');
        aiButton.onclick = async function() {
            try {
                await suggestRequirementsAnswers();
            } catch (error) {
                console.error('AI suggestion error:', error);
                alert('Failed to fetch AI suggestions. Please try again or fill out manually.');
            }
        };
    } else {
        console.log('AI suggest answers button not found');
    }
    
    // Add handler for Generate Epics & User Stories button
    const generateEpicsBtn = document.getElementById('generateEpicsBtn');
    if (generateEpicsBtn) {
        console.log('Generate Epics button found, attaching handler');
        generateEpicsBtn.onclick = async function() {
            try {
                await generateEpicsAndStories();
            } catch (error) {
                console.error('Epic generation error:', error);
                alert('Failed to generate epics and stories. Please try again.');
            }
        };
    } else {
        console.log('Generate Epics button not found');
    }
});

async function suggestRequirementsAnswers() {
    const aiButton = document.getElementById('aiSuggestAnswersBtn');
    const caseIdElement = document.querySelector('[data-case-id]');
    
    if (!caseIdElement) {
        console.error('Case ID not found');
        return;
    }
    
    const caseId = parseInt(caseIdElement.getAttribute('data-case-id'));
    
    // Show loading state
    const originalText = aiButton.innerHTML;
    aiButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> AI Drafting...';
    aiButton.disabled = true;
    
    try {
        const response = await fetch('/api/ai/suggest-requirements-answers', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ case_id: caseId })
        });
        
        if (!response.ok) {
            const payload = await response.json().catch(() => ({}));
            console.error("AI error:", payload.error || response.statusText);
            alert(payload.error || 'Failed to generate requirements answers.');
            aiButton.innerHTML = originalText;
            aiButton.disabled = false;
            return;
        }
        
        const result = await response.json();
        
        if (result.success && result.answers) {
            populateAnswers(result.answers);
            showSuccessMessage('AI Draft Complete! Review and modify the populated requirements below.');
        } else {
            console.log('API returned error:', result.error);
            throw new Error(result.error || 'Failed to generate AI suggestions');
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to generate AI suggestions. Please try again.');
    } finally {
        // Restore button state
        aiButton.innerHTML = originalText;
        aiButton.disabled = false;
    }
}

function populateAnswers(answers) {
    // Handle both array and object formats from backend
    if (Array.isArray(answers)) {
        // Array format - use index-based mapping
        answers.forEach((answer, index) => {
            const questionId = `q${index + 1}`;
            const element = document.getElementById(questionId);
            if (element) {
                element.value = answer;
                // Add visual indicator for AI-populated fields
                element.style.borderLeft = '3px solid #28a745';
                element.style.backgroundColor = 'rgba(40, 167, 69, 0.1)';
            }
        });
    } else {
        // Object format - use key-based mapping
        Object.keys(answers).forEach(questionId => {
            const element = document.getElementById(questionId);
            if (element && answers[questionId]) {
                element.value = answers[questionId];
                // Add visual indicator for AI-populated fields
                element.style.borderLeft = '3px solid #28a745';
                element.style.backgroundColor = 'rgba(40, 167, 69, 0.1)';
            }
        });
    }
    
    // Scroll to form for user review
    const form = document.getElementById('requirementsForm');
    if (form) {
        form.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function populateFallbackAnswers() {
    const fallbackAnswers = [
        "Core system functionality including automated workflow management, document processing, user portal access, data validation, approval workflows, compliance checking, comprehensive dashboards, and audit trail capabilities.",
        "Multi-tier access: System Administrators (full access), Department Managers (process management), Operations Staff (daily operations), Review Committee (evaluations), External Users (submissions/tracking). Role-based permissions aligned with organizational hierarchy.",
        "Enterprise ERP integration for budget validation, Active Directory authentication, email notifications, document management systems, workflow engines, business intelligence tools, and regulatory systems.",
        "Support 200+ concurrent users, handle 50MB uploads within 15 seconds, maintain 99% uptime, real-time notifications under 3 seconds, auto-scaling capabilities, and sub-2-second response times for standard operations.",
        "Executive dashboards with performance metrics, cost-benefit tracking, compliance reporting, timeline monitoring, and tamper-proof audit trails with comprehensive logging capabilities.",
        "Real-time validation with contextual errors, automated policy checking, duplicate prevention, file format validation, mandatory field enforcement, data integrity checks, graceful error recovery, and comprehensive logging.",
        "Mobile-responsive design, WCAG 2.1 AA compliance, intuitive role-based dashboards, multi-language support, modern branding, keyboard navigation, screen reader compatibility, and offline critical function capability.",
        "Multi-factor authentication, AES-256 encryption, role-based access controls, comprehensive audit logging, regulatory compliance, secure APIs, regular security assessments, and appropriate investment-level security measures."
    ];
    
    populateAnswers(fallbackAnswers);
}

function showSuccessMessage(message) {
    showAlert(message, 'success');
}

function showErrorMessage(message) {
    showAlert(message, 'warning');
}

async function generateEpicsAndStories() {
    const generateBtn = document.getElementById('generateEpicsBtn');
    const caseIdElement = document.querySelector('[data-case-id]');
    
    if (!caseIdElement) {
        console.error('Case ID not found');
        alert('Case ID not found. Please refresh the page and try again.');
        return;
    }
    
    const caseId = parseInt(caseIdElement.getAttribute('data-case-id'));
    
    // Collect answers from form as dictionary
    const answers = {};
    for (let i = 1; i <= 8; i++) {
        const element = document.getElementById(`q${i}`);
        if (element) {
            answers[`q${i}`] = element.value.trim();
        } else {
            answers[`q${i}`] = '';
        }
    }
    
    // Validate that at least some answers are provided
    const nonEmptyAnswers = Object.values(answers).filter(answer => answer.length > 0);
    if (nonEmptyAnswers.length === 0) {
        alert('Please provide answers to at least some of the requirements questions before generating epics.');
        return;
    }
    
    // Show loading state
    const originalText = generateBtn.innerHTML;
    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    generateBtn.disabled = true;
    
    try {
        const response = await fetch(`/api/ai/generate-requirements/${caseId}`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                answers: answers
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            showSuccessMessage('Epics and user stories generated successfully!');
            
            // Display the generated epics
            displayGeneratedEpics(data.epics);
            
            // Hide the form and show results
            const form = document.getElementById('requirementsForm');
            if (form) {
                form.style.display = 'none';
            }
            
            // Scroll to results
            const resultsDiv = document.getElementById('generationResults');
            if (resultsDiv) {
                resultsDiv.scrollIntoView({ behavior: 'smooth' });
            }
            
        } else {
            throw new Error(data.error || 'Unknown error occurred');
        }
        
    } catch (error) {
        console.error('Epic generation error:', error);
        showErrorMessage(`Failed to generate epics: ${error.message}`);
        
        // Reset button state
        generateBtn.innerHTML = originalText;
        generateBtn.disabled = false;
    }
}

function displayGeneratedEpics(epics) {
    const resultsDiv = document.getElementById('generationResults');
    if (!resultsDiv) return;
    
    let html = '<h4 class="text-light mb-3">Generated Requirements</h4>';
    
    epics.forEach((epic, index) => {
        html += `
            <div class="card mb-3 bg-dark border-success">
                <div class="card-header bg-success">
                    <h5 class="mb-0 text-dark">Epic ${index + 1}: ${epic.title}</h5>
                </div>
                <div class="card-body">
                    <p class="text-light">${epic.description}</p>
                    
                    ${epic.stories && epic.stories.length > 0 ? `
                        <h6 class="text-info mt-3">User Stories:</h6>
                        <ul class="list-group list-group-flush">
                            ${epic.stories.map(story => `
                                <li class="list-group-item bg-dark border-secondary text-light">
                                    <strong>${story.title}</strong><br>
                                    <small class="text-muted">${story.description}</small>
                                    ${story.acceptance_criteria ? `<br><small class="text-info">Criteria: ${story.acceptance_criteria}</small>` : ''}
                                </li>
                            `).join('')}
                        </ul>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    html += `
        <div class="mt-4 text-center">
            <button type="button" class="btn btn-success" onclick="goToBusinessCase()">
                <i class="fas fa-check"></i> Complete - View Updated Requirements
            </button>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function goToBusinessCase() {
    // Navigate to business case using correct URL pattern
    const caseIdElement = document.querySelector('[data-case-id]');
    if (caseIdElement) {
        const caseId = caseIdElement.getAttribute('data-case-id');
        // Correct URL pattern for business case view
        window.location.href = `/cases/${caseId}`;
    } else {
        // Fallback to business cases list
        window.location.href = '/cases';
    }
}

function showSuccessNotification(message) {
    showAlert(message, 'success');
}

function showAlert(message, type) {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.getElementById('step2') || document.body;
    container.insertBefore(alert, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function showSuccessNotification(message) {
    showAlert(message, 'success');
}