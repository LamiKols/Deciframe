document.addEventListener('DOMContentLoaded', function() {
    const aiBtn = document.getElementById('aiWriteSummaryBtn');
    if (!aiBtn) {
        console.log('AI Write Summary button not found');
        return;
    }
    
    aiBtn.onclick = async () => {
        console.log('AI Write Summary button clicked');
        
        // Get case ID from window variable (if editing existing case)
        const caseId = window.caseId;
        
        // Extract form data for unsaved cases
        const formData = {
            title: document.getElementById('title')?.value || '',
            description: document.getElementById('description')?.value || '',
            cost_estimate: document.getElementById('cost_estimate')?.value || 0,
            benefit_estimate: document.getElementById('benefit_estimate')?.value || 0,
            solution_description: document.getElementById('solution_description')?.value || ''
        };
        
        // Add case_id if available (for saved cases)
        if (caseId && caseId !== 'null') {
            formData.case_id = parseInt(caseId);
        }
        
        // Show loading state
        const originalText = aiBtn.innerHTML;
        aiBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        aiBtn.disabled = true;
        
        try {
            const res = await fetch('/api/ai/write-summary', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify(formData)
            });
            
            if (!res.ok) {
                const payload = await res.json().catch(()=>({}));
                throw new Error(payload.error || res.statusText);
            }
            
            const {summary} = await res.json();
            const ta = document.getElementById('bcSummary');
            
            if (ta) {
                ta.value = summary;
                // Show success message
                const alert = document.createElement('div');
                alert.className = 'alert alert-success alert-dismissible fade show mt-2';
                alert.innerHTML = `
                    <i class="fas fa-check-circle"></i> AI summary generated successfully!
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                ta.parentNode.insertAdjacentElement('afterend', alert);
                
                // Auto dismiss after 3 seconds
                setTimeout(() => alert.remove(), 3000);
            } else {
                throw new Error('Summary field not found');
            }
            
        } catch (err) {
            console.error('AI write-summary error', err);
            alert('Failed to generate summary: ' + err.message);
        } finally {
            // Restore button state
            aiBtn.innerHTML = originalText;
            aiBtn.disabled = false;
        }
    };
});