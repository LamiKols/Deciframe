# Missing url_for() Endpoints — Route Doctor Report

| Template | Pos | Missing | Best Match | Confidence | Other Suggestions |
|---|---:|---|---|---:|---|
| `templates/notifications/index.html` | 611 | `notifications.index` | `solutions.index` | 70 | notifications_config.debug_data(64), notifications_config.edit_setting(61) |
| `templates/notifications/index.html` | 837 | `notifications.index` | `solutions.index` | 70 | notifications_config.debug_data(64), notifications_config.edit_setting(61) |
| `templates/notifications/index.html` | 1209 | `notifications.mark_all_read` | `notifications_config.test_escalation` | 57 | notifications_config.create_setting(54), notifications_config.reset_defaults(54) |
| `templates/notifications/index.html` | 4799 | `notifications.mark_read` | `notifications_config.create_setting` | 58 | notifications_config.reset_defaults(58), notifications_config.edit_setting(57) |
| `templates/notifications/index.html` | 6299 | `notifications.index` | `solutions.index` | 70 | notifications_config.debug_data(64), notifications_config.edit_setting(61) |
| `templates/notifications/index.html` | 6868 | `notifications.index` | `solutions.index` | 70 | notifications_config.debug_data(64), notifications_config.edit_setting(61) |
| `templates/notifications/index.html` | 7740 | `notifications.index` | `solutions.index` | 70 | notifications_config.debug_data(64), notifications_config.edit_setting(61) |
| `templates/admin/audit_trail.html` | 1411 | `admin_audit_trail` | `admin_audit_logs` | 78 | admin_edit_user(68), admin_delete_triage_rule(63) |
| `templates/admin/audit_trail.html` | 3791 | `admin_audit_trail` | `admin_audit_logs` | 78 | admin_edit_user(68), admin_delete_triage_rule(63) |
| `templates/admin/audit_trail.html` | 10934 | `admin.audit_trail` | `admin_audit_logs` | 72 | admin_edit_user(62), admin_delete_triage_rule(58) |
| `templates/admin/audit_trail.html` | 11603 | `admin.audit_trail` | `admin_audit_logs` | 72 | admin_edit_user(62), admin_delete_triage_rule(58) |
| `templates/admin/audit_trail.html` | 12714 | `admin.audit_trail` | `admin_audit_logs` | 72 | admin_edit_user(62), admin_delete_triage_rule(58) |
| `templates/admin/audit_trail.html` | 14089 | `admin.audit_trail` | `admin_audit_logs` | 72 | admin_edit_user(62), admin_delete_triage_rule(58) |
| `templates/admin/system_health.html` | 4705 | `admin_audit_trail` | `admin_audit_logs` | 78 | admin_edit_user(68), admin_delete_triage_rule(63) |
| `templates/admin/pending_users.html` | 2410 | `admin.assign_department` | `admin_help_center` | 55 | admin_delete_help_article(54), admin_import_result(52) |
| `templates/admin/preferences_demo.html` | 9349 | `admin.regional_settings` | `admin_organization_settings` | 76 | admin_settings(75), admin_delete_setting(69) |
| `templates/admin/triage_rules.html` | 7546 | `admin.test_rule` | `admin_test_triage_rule` | 75 | admin_triage_rules(72), admin_toggle_triage_rule(66) |
| `templates/admin/triage_rules.html` | 8200 | `admin.toggle_rule` | `admin_toggle_triage_rule` | 78 | admin_triage_rules(74), admin_toggle_user_status(68) |
| `templates/admin/triage_rules.html` | 8809 | `admin.delete_rule` | `admin_delete_triage_rule` | 78 | admin_delete_help_article(71), admin_delete_setting(70) |
| `templates/search/search.html` | 3864 | `problems.problem_detail` | `problems.classify_problem` | 66 | problems.edit(66), review.project_detail(63) |
| `templates/search/search.html` | 5484 | `projects.project_detail` | `projects.project_backlog` | 80 | review.project_detail(77), projects.new_project(74) |
| `templates/dashboards/manager.html` | 1723 | `problems.problem_detail` | `problems.classify_problem` | 66 | problems.edit(66), review.project_detail(63) |
| `templates/dashboards/director.html` | 10905 | `admin.admin_dashboard` | `admin_dashboard` | 83 | dashboards.admin_dashboard(76), platform_admin.dashboard(66) |
| `templates/dashboards/director.html` | 11889 | `admin.admin_dashboard` | `admin_dashboard` | 83 | dashboards.admin_dashboard(76), platform_admin.dashboard(66) |
| `templates/dashboards/pm.html` | 1765 | `projects.project_detail` | `projects.project_backlog` | 80 | review.project_detail(77), projects.new_project(74) |
| `templates/dashboards/pm.html` | 4852 | `projects.milestones_list` | `projects.new_milestone` | 78 | projects.edit_milestone(76), projects.delete_milestone(73) |
| `templates/dashboards/pm.html` | 8549 | `projects.project_detail` | `projects.project_backlog` | 80 | review.project_detail(77), projects.new_project(74) |

---

## Patch Snippets
**templates/notifications/index.html** — replace `notifications.index` → `solutions.index` (confidence 70)

```jinja
{{ url_for('solutions.index') }}
```

**templates/notifications/index.html** — replace `notifications.index` → `solutions.index` (confidence 70)

```jinja
{{ url_for('solutions.index') }}
```

**templates/notifications/index.html** — replace `notifications.mark_all_read` → `notifications_config.test_escalation` (confidence 57)

```jinja
{{ url_for('notifications_config.test_escalation') }}
```

**templates/notifications/index.html** — replace `notifications.mark_read` → `notifications_config.create_setting` (confidence 58)

```jinja
{{ url_for('notifications_config.create_setting') }}
```

**templates/notifications/index.html** — replace `notifications.index` → `solutions.index` (confidence 70)

```jinja
{{ url_for('solutions.index') }}
```

**templates/notifications/index.html** — replace `notifications.index` → `solutions.index` (confidence 70)

```jinja
{{ url_for('solutions.index') }}
```

**templates/notifications/index.html** — replace `notifications.index` → `solutions.index` (confidence 70)

```jinja
{{ url_for('solutions.index') }}
```

**templates/admin/audit_trail.html** — replace `admin_audit_trail` → `admin_audit_logs` (confidence 78)

```jinja
{{ url_for('admin_audit_logs') }}
```

**templates/admin/audit_trail.html** — replace `admin_audit_trail` → `admin_audit_logs` (confidence 78)

```jinja
{{ url_for('admin_audit_logs') }}
```

**templates/admin/audit_trail.html** — replace `admin.audit_trail` → `admin_audit_logs` (confidence 72)

```jinja
{{ url_for('admin_audit_logs') }}
```

**templates/admin/audit_trail.html** — replace `admin.audit_trail` → `admin_audit_logs` (confidence 72)

```jinja
{{ url_for('admin_audit_logs') }}
```

**templates/admin/audit_trail.html** — replace `admin.audit_trail` → `admin_audit_logs` (confidence 72)

```jinja
{{ url_for('admin_audit_logs') }}
```

**templates/admin/audit_trail.html** — replace `admin.audit_trail` → `admin_audit_logs` (confidence 72)

```jinja
{{ url_for('admin_audit_logs') }}
```

**templates/admin/system_health.html** — replace `admin_audit_trail` → `admin_audit_logs` (confidence 78)

```jinja
{{ url_for('admin_audit_logs') }}
```

**templates/admin/pending_users.html** — replace `admin.assign_department` → `admin_help_center` (confidence 55)

```jinja
{{ url_for('admin_help_center') }}
```

**templates/admin/preferences_demo.html** — replace `admin.regional_settings` → `admin_organization_settings` (confidence 76)

```jinja
{{ url_for('admin_organization_settings') }}
```

**templates/admin/triage_rules.html** — replace `admin.test_rule` → `admin_test_triage_rule` (confidence 75)

```jinja
{{ url_for('admin_test_triage_rule') }}
```

**templates/admin/triage_rules.html** — replace `admin.toggle_rule` → `admin_toggle_triage_rule` (confidence 78)

```jinja
{{ url_for('admin_toggle_triage_rule') }}
```

**templates/admin/triage_rules.html** — replace `admin.delete_rule` → `admin_delete_triage_rule` (confidence 78)

```jinja
{{ url_for('admin_delete_triage_rule') }}
```

**templates/search/search.html** — replace `problems.problem_detail` → `problems.classify_problem` (confidence 66)

```jinja
{{ url_for('problems.classify_problem') }}
```

**templates/search/search.html** — replace `projects.project_detail` → `projects.project_backlog` (confidence 80)

```jinja
{{ url_for('projects.project_backlog') }}
```

**templates/dashboards/manager.html** — replace `problems.problem_detail` → `problems.classify_problem` (confidence 66)

```jinja
{{ url_for('problems.classify_problem') }}
```

**templates/dashboards/director.html** — replace `admin.admin_dashboard` → `admin_dashboard` (confidence 83)

```jinja
{{ url_for('admin_dashboard') }}
```

**templates/dashboards/director.html** — replace `admin.admin_dashboard` → `admin_dashboard` (confidence 83)

```jinja
{{ url_for('admin_dashboard') }}
```

**templates/dashboards/pm.html** — replace `projects.project_detail` → `projects.project_backlog` (confidence 80)

```jinja
{{ url_for('projects.project_backlog') }}
```

**templates/dashboards/pm.html** — replace `projects.milestones_list` → `projects.new_milestone` (confidence 78)

```jinja
{{ url_for('projects.new_milestone') }}
```

**templates/dashboards/pm.html** — replace `projects.project_detail` → `projects.project_backlog` (confidence 80)

```jinja
{{ url_for('projects.project_backlog') }}
```

