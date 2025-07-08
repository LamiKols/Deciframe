
-- 🔒 CRITICAL SECURITY MIGRATION: Add organization_id to all business models
-- Run this SQL script to add missing organization_id columns

-- Add organization_id to models missing it
ALTER TABLE departments ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE business_case_comments ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE project_milestones ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE project_comments ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE notification_templates ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE notifications ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE report_templates ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE requirements_backups ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE report_runs ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE epics ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE epic_comments ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE epic_sync_logs ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE stories ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE solutions ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE prediction_feedback ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE ai_threshold_settings ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE workflow_templates ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE workflow_libraries ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE tasks ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE scheduled_tasks ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE workflow_executions ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE help_categories ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE help_articles ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE notification_settings ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE archived_problems ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE archived_business_cases ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE archived_projects ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);
ALTER TABLE triage_rules ADD COLUMN organization_id INTEGER NOT NULL DEFAULT 1 REFERENCES organizations(id);

-- Update organization_id based on user relationships
UPDATE departments SET organization_id = (SELECT organization_id FROM users WHERE users.dept_id = departments.id LIMIT 1) WHERE organization_id = 1;
UPDATE notification_templates SET organization_id = (SELECT organization_id FROM users WHERE users.id = notification_templates.created_by LIMIT 1) WHERE organization_id = 1;
UPDATE report_templates SET organization_id = (SELECT organization_id FROM users WHERE users.id = report_templates.created_by LIMIT 1) WHERE organization_id = 1;

-- Populate organization_id from related records
UPDATE business_case_comments SET organization_id = (SELECT organization_id FROM business_cases WHERE business_cases.id = business_case_comments.case_id);
UPDATE project_milestones SET organization_id = (SELECT organization_id FROM projects WHERE projects.id = project_milestones.project_id);
UPDATE project_comments SET organization_id = (SELECT organization_id FROM projects WHERE projects.id = project_comments.project_id);
UPDATE epics SET organization_id = (SELECT organization_id FROM business_cases WHERE business_cases.id = epics.case_id);
UPDATE epic_comments SET organization_id = (SELECT organization_id FROM epics WHERE epics.id = epic_comments.epic_id);
UPDATE epic_sync_logs SET organization_id = (SELECT organization_id FROM epics WHERE epics.id = epic_sync_logs.epic_id);
UPDATE stories SET organization_id = (SELECT organization_id FROM epics WHERE epics.id = stories.epic_id);

-- Create indexes for performance
CREATE INDEX idx_departments_org_id ON departments(organization_id);
CREATE INDEX idx_business_case_comments_org_id ON business_case_comments(organization_id);
CREATE INDEX idx_project_milestones_org_id ON project_milestones(organization_id);
CREATE INDEX idx_project_comments_org_id ON project_comments(organization_id);
CREATE INDEX idx_notification_templates_org_id ON notification_templates(organization_id);
CREATE INDEX idx_notifications_org_id ON notifications(organization_id);
CREATE INDEX idx_report_templates_org_id ON report_templates(organization_id);
CREATE INDEX idx_requirements_backups_org_id ON requirements_backups(organization_id);
CREATE INDEX idx_report_runs_org_id ON report_runs(organization_id);
CREATE INDEX idx_epics_org_id ON epics(organization_id);
CREATE INDEX idx_epic_comments_org_id ON epic_comments(organization_id);
CREATE INDEX idx_epic_sync_logs_org_id ON epic_sync_logs(organization_id);
CREATE INDEX idx_stories_org_id ON stories(organization_id);
CREATE INDEX idx_solutions_org_id ON solutions(organization_id);
CREATE INDEX idx_prediction_feedback_org_id ON prediction_feedback(organization_id);
CREATE INDEX idx_ai_threshold_settings_org_id ON ai_threshold_settings(organization_id);
CREATE INDEX idx_workflow_templates_org_id ON workflow_templates(organization_id);
CREATE INDEX idx_workflow_libraries_org_id ON workflow_libraries(organization_id);
CREATE INDEX idx_tasks_org_id ON tasks(organization_id);
CREATE INDEX idx_scheduled_tasks_org_id ON scheduled_tasks(organization_id);
CREATE INDEX idx_workflow_executions_org_id ON workflow_executions(organization_id);
CREATE INDEX idx_help_categories_org_id ON help_categories(organization_id);
CREATE INDEX idx_help_articles_org_id ON help_articles(organization_id);
CREATE INDEX idx_notification_settings_org_id ON notification_settings(organization_id);
CREATE INDEX idx_archived_problems_org_id ON archived_problems(organization_id);
CREATE INDEX idx_archived_business_cases_org_id ON archived_business_cases(organization_id);
CREATE INDEX idx_archived_projects_org_id ON archived_projects(organization_id);
CREATE INDEX idx_triage_rules_org_id ON triage_rules(organization_id);

-- Verify data integrity
SELECT 'departments' as table_name, COUNT(*) as total_records, COUNT(DISTINCT organization_id) as organizations FROM departments
UNION ALL
SELECT 'epics', COUNT(*), COUNT(DISTINCT organization_id) FROM epics
UNION ALL
SELECT 'stories', COUNT(*), COUNT(DISTINCT organization_id) FROM stories
UNION ALL
SELECT 'solutions', COUNT(*), COUNT(DISTINCT organization_id) FROM solutions;

COMMIT;
