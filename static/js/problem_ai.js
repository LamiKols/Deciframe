// AI Problem Classification JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const titleField = document.getElementById('title');
    const descriptionField = document.getElementById('description');
    const aiClassifyBtn = document.getElementById('aiClassifyBtn');
    const issueTypeSelect = document.getElementById('issueType');
    const classificationResult = document.getElementById('aiClassificationResult');
    const aiSuggestion = document.getElementById('aiSuggestion');
    const aiExplanation = document.getElementById('aiExplanation');
    const aiConfidence = document.getElementById('aiConfidence');
    
    // Auto-classification timer
    let autoClassifyTimer = null;
    
    // Enable AI Classify button when both title and description have content
    function checkFieldsForClassification() {
        const hasTitle = titleField && titleField.value.trim().length > 0;
        const hasDescription = descriptionField && descriptionField.value.trim().length > 0;
        
        if (aiClassifyBtn) {
            aiClassifyBtn.disabled = !(hasTitle && hasDescription);
        }
    }
    
    // Function to trigger auto-classification
    function triggerAutoClassification() {
        if (autoClassifyTimer) {
            clearTimeout(autoClassifyTimer);
        }
        
        autoClassifyTimer = setTimeout(() => {
            const title = titleField?.value?.trim();
            const description = descriptionField?.value?.trim();
            
            if (title && description && title.length > 10 && description.length > 20) {
                performAIClassification(title, description, true); // true = auto mode
            }
        }, 2000); // Wait 2 seconds after user stops typing
    }
    
    // Unified AI Classification function
    function performAIClassification(title, description, isAutoMode = false) {
        if (!title || !description) {
            if (!isAutoMode) {
                alert('Please enter both a title and description before using AI classification.');
            }
            return;
        }
        
        // Show loading state for manual classification
        if (!isAutoMode && aiClassifyBtn) {
            aiClassifyBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Classifying...';
            aiClassifyBtn.disabled = true;
        }
        
        // Make API call to AI classification endpoint
        fetch('/problems/api/ai/classify-problem', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                description: description
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('AI Classification Response:', data);
            
            if (!data || typeof data !== 'object') {
                throw new Error('Invalid response format');
            }
            
            if (data.error && !data.issue_type) {
                throw new Error(data.error);
            }
            
            // Ensure we have required fields
            const issueType = data.issue_type || 'PROCESS';
            const explanation = data.explanation || 'AI classification completed';
            const confidence = data.confidence || 0.5;
            const confidencePercentage = data.confidence_percentage || Math.round(confidence * 100);
            
            // Update the issue type dropdown
            if (issueTypeSelect) {
                issueTypeSelect.value = issueType;
            }
            
            // Show the AI suggestion
            if (aiSuggestion) {
                const modeText = isAutoMode ? '(Auto-suggested)' : '';
                aiSuggestion.textContent = `${issueType.charAt(0) + issueType.slice(1).toLowerCase()} Issue ${modeText}`;
                aiSuggestion.style.fontWeight = '500';
            }
            if (aiExplanation) {
                aiExplanation.textContent = explanation;
                aiExplanation.style.color = 'inherit';
            }
            if (aiConfidence) {
                aiConfidence.textContent = `Confidence: ${confidencePercentage}%`;
                aiConfidence.style.fontWeight = '500';
                aiConfidence.style.color = 'inherit';
            }
            
            // Show the result panel
            if (classificationResult) {
                classificationResult.classList.remove('d-none');
                
                // Add visual feedback for high confidence suggestions with proper styling
                if (confidence >= 0.8) {
                    classificationResult.className = 'alert alert-success';
                    classificationResult.style.cssText = 'color: #155724; background-color: #d4edda; border-color: #c3e6cb;';
                } else if (confidence >= 0.6) {
                    classificationResult.className = 'alert alert-info';
                    classificationResult.style.cssText = 'color: #0c5460; background-color: #d1ecf1; border-color: #bee5eb;';
                } else {
                    classificationResult.className = 'alert alert-warning';
                    classificationResult.style.cssText = 'color: #856404; background-color: #fff3cd; border-color: #ffeaa7;';
                }
            }
            
            // Show any errors as warnings
            if (data.error && classificationResult) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'small text-warning mt-1';
                errorDiv.textContent = data.error;
                classificationResult.appendChild(errorDiv);
            }
        })
        .catch(error => {
            console.error('AI Classification Error:', error);
            
            // Only show fallback for manual classification
            if (!isAutoMode) {
                // Show fallback classification
                if (issueTypeSelect) {
                    issueTypeSelect.value = 'PROCESS';
                }
                if (aiSuggestion) {
                    aiSuggestion.textContent = 'Process Issue (Fallback)';
                }
                if (aiExplanation) {
                    aiExplanation.textContent = 'AI classification temporarily unavailable. Using default classification.';
                }
                if (aiConfidence) {
                    aiConfidence.textContent = 'Confidence: 50%';
                }
                
                if (classificationResult) {
                    classificationResult.className = 'alert alert-warning';
                    classificationResult.classList.remove('d-none');
                }
            }
        })
        .finally(() => {
            // Reset button state for manual classification
            if (!isAutoMode && aiClassifyBtn) {
                aiClassifyBtn.innerHTML = '<i class="fas fa-robot me-1"></i>AI Classify';
                aiClassifyBtn.disabled = false;
                checkFieldsForClassification();
            }
        });
    }
    
    // Add event listeners to title and description fields
    if (titleField) {
        titleField.addEventListener('input', function() {
            checkFieldsForClassification();
            triggerAutoClassification();
        });
    }
    if (descriptionField) {
        descriptionField.addEventListener('input', function() {
            checkFieldsForClassification();
            triggerAutoClassification();
        });
    }
    
    // AI Classification button functionality
    if (aiClassifyBtn) {
        aiClassifyBtn.addEventListener('click', function() {
            const title = titleField.value.trim();
            const description = descriptionField.value.trim();
            performAIClassification(title, description, false);
        });
    }
    
    // Initial check
    checkFieldsForClassification();
});

// AI Refinement functionality (existing)
document.addEventListener('DOMContentLoaded', function() {
    const titleField = document.getElementById('title');
    const descriptionField = document.getElementById('description');
    const aiRefineBtn = document.getElementById('aiRefineBtn');
    const aiRefineModal = new bootstrap.Modal(document.getElementById('aiRefineModal'));
    const aiVariantsContainer = document.getElementById('aiVariants');

    if (aiRefineBtn) {
        aiRefineBtn.addEventListener('click', function() {
            const title = titleField.value.trim();
            const description = descriptionField.value.trim();

            if (!title || !description) {
                alert('Please enter both a title and description before using AI refinement.');
                return;
            }

            // Show loading state
            aiRefineBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Refining...';
            aiRefineBtn.disabled = true;
            aiVariantsContainer.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Generating refined variations...</div>';

            // Show modal immediately
            aiRefineModal.show();

            // Make API call with authentication
            fetch('/api/ai/refine-problem', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    problem_description: `${title}\n\n${description}`
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }

                // Populate variants
                aiVariantsContainer.innerHTML = '';
                data.variants.forEach((variant, index) => {
                    const variantHtml = `
                        <div class="card bg-secondary mb-3">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h6 class="mb-0">Refined Version ${index + 1}</h6>
                                <button class="btn btn-sm btn-primary" onclick="selectVariant(${index})">
                                    <i class="fas fa-check me-1"></i>Use This Version
                                </button>
                            </div>
                            <div class="card-body">
                                <h6 class="text-info">Title:</h6>
                                <p class="mb-2" data-title="${index}">${variant.title}</p>
                                <h6 class="text-info">Description:</h6>
                                <p class="mb-0" data-description="${index}">${variant.description}</p>
                            </div>
                        </div>
                    `;
                    aiVariantsContainer.innerHTML += variantHtml;
                });
            })
            .catch(error => {
                console.error('AI Refinement Error:', error);
                aiVariantsContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        AI refinement is temporarily unavailable. Please try again later.
                        <br><small class="text-muted">Error: ${error.message}</small>
                    </div>
                `;
            })
            .finally(() => {
                // Reset button state
                aiRefineBtn.innerHTML = '<i class="fas fa-magic me-1"></i>AI Refine';
                aiRefineBtn.disabled = false;
            });
        });
    }
});

// Global function to select variant
function selectVariant(index) {
    const titleElement = document.querySelector(`[data-title="${index}"]`);
    const descriptionElement = document.querySelector(`[data-description="${index}"]`);
    const titleField = document.getElementById('title');
    const descriptionField = document.getElementById('description');

    if (titleElement && descriptionElement && titleField && descriptionField) {
        titleField.value = titleElement.textContent;
        descriptionField.value = descriptionElement.textContent;
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('aiRefineModal'));
        modal.hide();
        
        // Trigger auto-classification after selecting variant
        const event = new Event('input');
        titleField.dispatchEvent(event);
        descriptionField.dispatchEvent(event);
    }
}