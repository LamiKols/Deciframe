function toggleNode(button) {
  const subtree = button.parentElement.parentElement.querySelector('.dept-subtree');
  if (!subtree) return;

  if (subtree.classList.contains('hidden')) {
    subtree.classList.remove('hidden');
    button.textContent = "▼";
  } else {
    subtree.classList.add('hidden');
    button.textContent = "▶";
  }
}

function initializeDepartmentTree() {
    // Add smooth animations for department nodes
    const deptNodes = document.querySelectorAll('.dept-node');
    
    deptNodes.forEach((node, index) => {
        // Stagger animation delays for a cascading effect
        node.style.animationDelay = `${index * 0.1}s`;
        
        // Add hover effects for better interactivity
        const deptItem = node.querySelector('.dept-item');
        if (deptItem) {
            deptItem.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
            });
            
            deptItem.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        }
    });
    
    // Add confirmation dialogs for delete actions
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const deptName = this.closest('.dept-item').querySelector('.dept-name').textContent;
            if (!confirm(`Are you sure you want to delete "${deptName}"? This action cannot be undone.`)) {
                e.preventDefault();
            }
        });
    });
    
    // Add keyboard navigation support
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // Clear any active states or modals
            document.querySelectorAll('.dept-item').forEach(item => {
                item.style.transform = 'translateY(0)';
            });
        }
    });
}

// Function to expand/collapse department nodes (for future expansion functionality)
function toggleDepartmentNode(nodeId) {
    const node = document.querySelector(`[data-dept-id="${nodeId}"]`);
    if (node) {
        const children = node.querySelector('.dept-children');
        if (children) {
            children.style.display = children.style.display === 'none' ? 'block' : 'none';
        }
    }
}

// Function to highlight a specific department (for search functionality)
function highlightDepartment(deptId) {
    const node = document.querySelector(`[data-dept-id="${deptId}"]`);
    if (node) {
        const deptItem = node.querySelector('.dept-item');
        deptItem.style.backgroundColor = '#fffacd';
        deptItem.style.border = '2px solid #ffd700';
        
        // Scroll to the highlighted department
        node.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Remove highlight after 3 seconds
        setTimeout(() => {
            deptItem.style.backgroundColor = '';
            deptItem.style.border = '';
        }, 3000);
    }
}

// Function to add visual feedback for form submissions
function showLoadingState(button) {
    const originalText = button.textContent;
    button.textContent = 'Loading...';
    button.disabled = true;
    
    // Re-enable after 2 seconds (or when form actually submits)
    setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false;
    }, 2000);
}

// Add loading states to buttons
document.addEventListener('DOMContentLoaded', function() {
    const actionButtons = document.querySelectorAll('.edit-btn, .delete-btn, .new-btn');
    
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.classList.contains('delete-btn')) {
                showLoadingState(this);
            }
        });
    });
});

// Function to create a new department node dynamically (for AJAX functionality)
function createDepartmentNode(dept) {
    return `
        <li class="dept-node" data-dept-id="${dept.id}">
            <div class="dept-item">
                <div class="dept-content">
                    <span class="dept-name">${dept.name}</span>
                    <span class="dept-level">Level ${dept.level}</span>
                </div>
                <div class="dept-actions">
                    <a href="/departments/${dept.id}/edit" class="edit-btn">✏️ Edit</a>
                    <button onclick="deleteDepartment(${dept.id})" class="delete-btn">🗑️ Delete</button>
                </div>
            </div>
            <ul class="dept-children"></ul>
        </li>
    `;
}

// Function to handle department deletion via AJAX (for future enhancement)
function deleteDepartment(deptId) {
    const node = document.querySelector(`[data-dept-id="${deptId}"]`);
    const deptName = node.querySelector('.dept-name').textContent;
    
    if (confirm(`Are you sure you want to delete "${deptName}"?`)) {
        // Add visual feedback
        node.style.opacity = '0.5';
        node.style.pointerEvents = 'none';
        
        // Here you would make an AJAX call to delete the department
        // For now, we'll simulate the deletion
        setTimeout(() => {
            node.remove();
        }, 500);
    }
}

// Function to filter departments by name (for search functionality)
function filterDepartments(searchTerm) {
    const deptNodes = document.querySelectorAll('.dept-node');
    
    deptNodes.forEach(node => {
        const deptName = node.querySelector('.dept-name').textContent.toLowerCase();
        const matches = deptName.includes(searchTerm.toLowerCase());
        
        node.style.display = matches || searchTerm === '' ? 'block' : 'none';
    });
}

// Add search functionality if search input exists
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('#dept-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterDepartments(this.value);
        });
    }
});

// Export functions for use in other scripts
window.departmentTree = {
    toggleNode: toggleDepartmentNode,
    highlight: highlightDepartment,
    filter: filterDepartments,
    delete: deleteDepartment
};