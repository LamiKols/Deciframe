/**
 * AI Summary Generator for Business Cases
 * Generates executive summaries based on business case data
 */

class AISummaryGenerator {
    constructor() {
        this.init();
    }

    init() {
        console.log('AI Summary Generator initialized');
        this.attachEventListeners();
    }

    attachEventListeners() {
        const summaryBtn = document.getElementById('aiSummaryBtn');
        if (summaryBtn) {
            summaryBtn.addEventListener('click', () => this.generateSummary());
        }
    }

    async generateSummary() {
        const btn = document.getElementById('aiSummaryBtn');
        const summaryField = document.getElementById('summary');
        
        if (!summaryField) {
            console.error('Summary field not found');
            return;
        }

        // Get business case data from form
        const businessCaseData = this.extractFormData();
        
        // Show loading state
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        btn.disabled = true;

        try {
            const response = await fetch('/api/ai/write-summary', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify(businessCaseData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.success && data.summary) {
                summaryField.value = data.summary;
                this.showAlert('Success! AI-generated summary has been added to the field.', 'success');
            } else {
                throw new Error(data.error || 'Failed to generate summary');
            }

        } catch (error) {
            console.error('AI Summary Error:', error);
            this.showAlert(`Error generating summary: ${error.message}`, 'error');
        } finally {
            // Restore button state
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }

    extractFormData() {
        // Get case ID from the button data attribute
        const btn = document.getElementById('aiSummaryBtn');
        const caseId = btn?.getAttribute('data-case-id');
        
        return {
            case_id: caseId
        };
    }

    showAlert(message, type) {
        // Create and show Bootstrap alert
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const iconClass = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle';
        
        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show mt-3" role="alert">
                <i class="fas ${iconClass}"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Insert alert above the summary field
        const summaryField = document.getElementById('summary');
        summaryField.parentNode.insertAdjacentHTML('beforebegin', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AISummaryGenerator();
});