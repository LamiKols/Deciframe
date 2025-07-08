# DeciFrame Dropdown Macros Guide

## Overview
This guide demonstrates how to use the reusable dropdown macros in DeciFrame for consistent styling and functionality across all templates.

## Location
All dropdown macros are located in: `templates/macros/forms.html`

## Available Macros

### 1. Basic Dropdown Macro
The foundation macro for creating custom dropdowns with consistent styling.

```jinja
{% from 'macros/forms.html' import dropdown %}

{{ dropdown('field_name', options, selected=None, placeholder='Select...', 
           class='form-select', id=None, required=False, multiple=False, onchange=None) }}
```

**Example:**
```jinja
{{ dropdown('category', [('tech', 'Technology'), ('sales', 'Sales')], 
           selected='tech', placeholder='Choose Category') }}
```

### 2. WTForms Integration Macro
Wraps WTForms fields with custom dropdown styling.

```jinja
{% from 'macros/forms.html' import wtf_dropdown %}

{{ wtf_dropdown(form.field_name, class="form-select") }}
```

**Example:**
```jinja
{{ wtf_dropdown(form.department, class="form-select" + (" is-invalid" if form.department.errors else "")) }}
```

### 3. Department Hierarchy Dropdown
Specialized dropdown for departments with hierarchical display.

```jinja
{% from 'macros/forms.html' import department_dropdown %}

{{ department_dropdown('parent_id', departments, selected=None, 
                       placeholder='— Top Level —', show_hierarchy=True) }}
```

**Example:**
```jinja
{{ department_dropdown('parent_department', departments, selected_dept_id, '— Select Department —') }}
```

### 4. User/Manager Dropdown
Dropdown for user selection with optional role display.

```jinja
{% from 'macros/forms.html' import user_dropdown %}

{{ user_dropdown('assigned_to', users, selected=None, placeholder='Select User', show_role=False) }}
```

**Example:**
```jinja
{{ user_dropdown('project_manager', managers, current_manager_id, 
                 placeholder='— Assign Manager —', show_role=True) }}
```

### 5. Priority Dropdown
Standard priority dropdown with High/Medium/Low options.

```jinja
{% from 'macros/forms.html' import priority_dropdown %}

{{ priority_dropdown('priority', selected='Medium') }}
```

### 6. Status Dropdown
Dynamic status dropdown with custom status options.

```jinja
{% from 'macros/forms.html' import status_dropdown %}

{{ status_dropdown('status', ['Open', 'In Progress', 'Completed'], selected='Open') }}
```

### 7. Role Dropdown
Dropdown for user roles with enum integration.

```jinja
{% from 'macros/forms.html' import role_dropdown %}

{{ role_dropdown('user_role', available_roles, selected_role) }}
```

## Usage Patterns

### Template Setup
Add the import statement at the top of your template:

```jinja
{% extends "base.html" %}
{% from 'macros/forms.html' import dropdown, wtf_dropdown, department_dropdown %}
```

### Form Integration
Replace existing select elements:

**Before:**
```html
<div class="custom-dropdown">
    <select name="department" class="form-select">
        <option value="">Select Department</option>
        {% for dept in departments %}
            <option value="{{ dept.id }}">{{ dept.name }}</option>
        {% endfor %}
    </select>
</div>
```

**After:**
```jinja
{{ department_dropdown('department', departments, placeholder='Select Department') }}
```

### WTForms Integration
Replace manual dropdown wrapping:

**Before:**
```html
<div class="custom-dropdown">
    {{ form.status(class="form-select") }}
</div>
```

**After:**
```jinja
{{ wtf_dropdown(form.status, class="form-select") }}
```

## Advanced Examples

### Multiple Selection with JavaScript
```jinja
{{ dropdown('skills', skill_options, multiple=True, 
           onchange='updateSkillCount(this)', id='skills-selector') }}
```

### Required Field with Validation
```jinja
{{ department_dropdown('required_dept', departments, required=True,
                       class="form-select" + (" is-invalid" if errors else "")) }}
```

### Conditional Options
```jinja
{% set manager_options = [(m.id, m.full_name) for m in managers if m.is_active] %}
{{ dropdown('manager_id', manager_options, placeholder='— Available Managers —') }}
```

## Benefits

1. **Consistency**: All dropdowns use the same custom styling
2. **Maintainability**: Changes to dropdown appearance happen in one place
3. **Reusability**: Specialized macros for common use cases
4. **Flexibility**: Support for all standard dropdown features
5. **Integration**: Seamless WTForms compatibility

## Demonstration
Visit `/demo/dropdowns` to see all macros in action with sample data.

## CSS Integration
All macros automatically use the custom dropdown styling from `static/dropdown.css` which provides:
- Dark theme compatibility (#2e2e48 background)
- Custom arrow styling with CSS pseudo-elements
- Smooth hover transitions (#3a3a5c hover states)
- Professional borders and spacing
- Consistent visual hierarchy

## Migration Guide
To migrate existing templates:

1. Add macro imports to template header
2. Replace `<div class="custom-dropdown">` wrappers with macro calls
3. Convert option lists to tuple format: `[(value, label), ...]`
4. Test functionality and styling

This system provides enterprise-grade dropdown consistency across the entire DeciFrame application.

## Migration Status: 100% Complete ✅

### ALL TEMPLATES SUCCESSFULLY MIGRATED
✅ **Core Templates**
- templates/macros/forms.html - Complete macro system with 7 specialized macros
- dept/templates/department_form.html - WTForms department_dropdown integration
- projects/templates/index.html - dropdown macro for filters

✅ **Business Case Templates**  
- business/templates/refine_stories_simple.html - status_dropdown macro

✅ **Problem Management Templates**
- problems/templates/problems.html - Status filter dropdown with dropdown macro
- problems/templates/problem_form.html - Priority dropdown with wtf_dropdown macro  

✅ **Admin Templates**
- admin/templates/retention.html - dropdown macro for table selection
- admin/templates/users.html - role_dropdown macro for user role filtering
- admin/templates/user_form.html - wtf_dropdown macro for role and department fields
- admin/templates/pending_users.html - department_dropdown macro for assignment
- templates/admin_dashboard_demo.html - All 5 filter dropdowns migrated to appropriate macros

### Complete Site-Wide Standardization Achieved
The entire DeciFrame application now uses the centralized dropdown macro system for:
- Consistent dark theme styling across all select elements
- Maintainable code with reusable macro components
- Professional appearance with smooth hover transitions
- Standardized error handling and validation states