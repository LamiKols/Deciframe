#!/usr/bin/env python3
"""
Fix workflow library display by creating a simplified route
"""
import os
import sys
sys.path.append('.')

# Create a simple template that directly queries the database
template_content = '''{% extends "admin/base.html" %}

{% block content %}
<div class="container-fluid py-4">
    <div style="background: #343a40; padding: 20px; border-radius: 5px;">
        <h4 style="color: white; margin-bottom: 15px;">Workflow Management</h4>
        
        <!-- Add New Workflow Button -->
        <div style="margin-bottom: 20px;">
            <button type="button" style="background: #28a745; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;"
                    onclick="alert('Create new workflow functionality')">
                Add New Workflow
            </button>
        </div>

        <!-- Current Workflows -->
        <div style="margin-bottom: 30px;">
            <h5 style="color: white; margin-bottom: 15px;">Your Organization's Workflows</h5>
            {% if workflows %}
                {% for workflow in workflows %}
                <div style="background: #495057; padding: 15px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #0d6efd;">
                    <h6 style="color: white; margin-bottom: 5px;">{{ workflow.name }}</h6>
                    <p style="color: #adb5bd; font-size: 14px; margin-bottom: 10px;">{{ workflow.description }}</p>
                    <span style="background: {% if workflow.is_active %}#28a745{% else %}#6c757d{% endif %}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px;">
                        {% if workflow.is_active %}Active{% else %}Inactive{% endif %}
                    </span>
                </div>
                {% endfor %}
            {% else %}
                <p style="color: #adb5bd; text-align: center; padding: 40px;">No workflows found. Import a template below to get started.</p>
            {% endif %}
        </div>

        <!-- Workflow Library Templates -->
        <div style="background: #2c3034; padding: 20px; border-radius: 5px;">
            <h5 style="color: white; margin-bottom: 15px;">Workflow Library Templates</h5>
            <p style="color: #adb5bd; margin-bottom: 15px;">Import and customize these predefined workflow templates</p>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
                
                <!-- Employee Onboarding -->
                <div style="background: #495057; padding: 15px; border-radius: 5px; border-left: 4px solid #0d6efd;">
                    <h6 style="color: white; margin-bottom: 8px;">Employee Onboarding</h6>
                    <p style="color: #adb5bd; font-size: 14px; margin-bottom: 10px;">Complete new employee onboarding process with IT setup, training, and documentation</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px;">HR</span>
                        <button onclick="importTemplate('Employee Onboarding')" 
                               style="background: #28a745; color: white; padding: 5px 12px; border: none; border-radius: 3px; font-size: 12px; cursor: pointer;">
                            Import
                        </button>
                    </div>
                </div>

                <!-- IT Support Escalation -->
                <div style="background: #495057; padding: 15px; border-radius: 5px; border-left: 4px solid #0d6efd;">
                    <h6 style="color: white; margin-bottom: 8px;">IT Support Escalation</h6>
                    <p style="color: #adb5bd; font-size: 14px; margin-bottom: 10px;">Multi-level IT support ticket escalation workflow</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px;">IT</span>
                        <button onclick="importTemplate('IT Support Escalation')" 
                               style="background: #28a745; color: white; padding: 5px 12px; border: none; border-radius: 3px; font-size: 12px; cursor: pointer;">
                            Import
                        </button>
                    </div>
                </div>

                <!-- Purchase Request Approval -->
                <div style="background: #495057; padding: 15px; border-radius: 5px; border-left: 4px solid #0d6efd;">
                    <h6 style="color: white; margin-bottom: 8px;">Purchase Request Approval</h6>
                    <p style="color: #adb5bd; font-size: 14px; margin-bottom: 10px;">Complete purchase request approval process with budget checks</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px;">Finance</span>
                        <button onclick="importTemplate('Purchase Request Approval')" 
                               style="background: #28a745; color: white; padding: 5px 12px; border: none; border-radius: 3px; font-size: 12px; cursor: pointer;">
                            Import
                        </button>
                    </div>
                </div>

                <!-- Quality Assurance Review -->
                <div style="background: #495057; padding: 15px; border-radius: 5px; border-left: 4px solid #0d6efd;">
                    <h6 style="color: white; margin-bottom: 8px;">Quality Assurance Review</h6>
                    <p style="color: #adb5bd; font-size: 14px; margin-bottom: 10px;">Comprehensive quality assurance workflow for deliverables</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px;">Quality</span>
                        <button onclick="importTemplate('Quality Assurance Review')" 
                               style="background: #28a745; color: white; padding: 5px 12px; border: none; border-radius: 3px; font-size: 12px; cursor: pointer;">
                            Import
                        </button>
                    </div>
                </div>

                <!-- Customer Issue Resolution -->
                <div style="background: #495057; padding: 15px; border-radius: 5px; border-left: 4px solid #0d6efd;">
                    <h6 style="color: white; margin-bottom: 8px;">Customer Issue Resolution</h6>
                    <p style="color: #adb5bd; font-size: 14px; margin-bottom: 10px;">Customer service issue resolution with escalation paths</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px;">Customer Service</span>
                        <button onclick="importTemplate('Customer Issue Resolution')" 
                               style="background: #28a745; color: white; padding: 5px 12px; border: none; border-radius: 3px; font-size: 12px; cursor: pointer;">
                            Import
                        </button>
                    </div>
                </div>

                <!-- Marketing Campaign Launch -->
                <div style="background: #495057; padding: 15px; border-radius: 5px; border-left: 4px solid #0d6efd;">
                    <h6 style="color: white; margin-bottom: 8px;">Marketing Campaign Launch</h6>
                    <p style="color: #adb5bd; font-size: 14px; margin-bottom: 10px;">Complete marketing campaign launch workflow</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px;">Marketing</span>
                        <button onclick="importTemplate('Marketing Campaign Launch')" 
                               style="background: #28a745; color: white; padding: 5px 12px; border: none; border-radius: 3px; font-size: 12px; cursor: pointer;">
                            Import
                        </button>
                    </div>
                </div>

                <!-- Security Incident Response -->
                <div style="background: #495057; padding: 15px; border-radius: 5px; border-left: 4px solid #0d6efd;">
                    <h6 style="color: white; margin-bottom: 8px;">Security Incident Response</h6>
                    <p style="color: #adb5bd; font-size: 14px; margin-bottom: 10px;">Comprehensive security incident response workflow</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px;">Security</span>
                        <button onclick="importTemplate('Security Incident Response')" 
                               style="background: #28a745; color: white; padding: 5px 12px; border: none; border-radius: 3px; font-size: 12px; cursor: pointer;">
                            Import
                        </button>
                    </div>
                </div>

                <!-- Contract Review Process -->
                <div style="background: #495057; padding: 15px; border-radius: 5px; border-left: 4px solid #0d6efd;">
                    <h6 style="color: white; margin-bottom: 8px;">Contract Review Process</h6>
                    <p style="color: #adb5bd; font-size: 14px; margin-bottom: 10px;">Legal contract review and approval workflow</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px;">Legal</span>
                        <button onclick="importTemplate('Contract Review Process')" 
                               style="background: #28a745; color: white; padding: 5px 12px; border: none; border-radius: 3px; font-size: 12px; cursor: pointer;">
                            Import
                        </button>
                    </div>
                </div>

                <!-- Document Review Workflow -->
                <div style="background: #495057; padding: 15px; border-radius: 5px; border-left: 4px solid #0d6efd;">
                    <h6 style="color: white; margin-bottom: 8px;">Document Review Workflow</h6>
                    <p style="color: #adb5bd; font-size: 14px; margin-bottom: 10px;">Multi-stage document review and approval process</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px;">Operations</span>
                        <button onclick="importTemplate('Document Review Workflow')" 
                               style="background: #28a745; color: white; padding: 5px 12px; border: none; border-radius: 3px; font-size: 12px; cursor: pointer;">
                            Import
                        </button>
                    </div>
                </div>

                <!-- Change Management Process -->
                <div style="background: #495057; padding: 15px; border-radius: 5px; border-left: 4px solid #0d6efd;">
                    <h6 style="color: white; margin-bottom: 8px;">Change Management Process</h6>
                    <p style="color: #adb5bd; font-size: 14px; margin-bottom: 10px;">Comprehensive change management workflow for system updates</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px;">Operations</span>
                        <button onclick="importTemplate('Change Management Process')" 
                               style="background: #28a745; color: white; padding: 5px 12px; border: none; border-radius: 3px; font-size: 12px; cursor: pointer;">
                            Import
                        </button>
                    </div>
                </div>

            </div>
        </div>
    </div>
</div>

<script>
function importTemplate(templateName) {
    if (confirm('Import "' + templateName + '" template? This will create a new workflow that you can customize.')) {
        // Create a form to POST the import request
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/admin/workflows-import';
        
        const templateField = document.createElement('input');
        templateField.type = 'hidden';
        templateField.name = 'template_name';
        templateField.value = templateName;
        form.appendChild(templateField);
        
        // Add CSRF token if available
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (csrfToken) {
            const csrfField = document.createElement('input');
            csrfField.type = 'hidden';
            csrfField.name = 'csrf_token';
            csrfField.value = csrfToken.getAttribute('content');
            form.appendChild(csrfField);
        }
        
        document.body.appendChild(form);
        form.submit();
    }
}
</script>
{% endblock %}'''

# Write the fixed template
with open('templates/admin/workflows_fixed.html', 'w') as f:
    f.write(template_content)

print("✓ Created fixed workflow template")