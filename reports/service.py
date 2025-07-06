"""
Report Generation Service for DeciFrame
Handles automated report generation, PDF conversion, and email distribution
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from jinja2 import Template
import weasyprint
from flask import current_app, url_for
from app import db
from models import ReportTemplate, ReportRun, User, RoleEnum
from notifications.service import NotificationService

class ReportService:
    def __init__(self):
        self.notification_service = NotificationService()
        self.base_url = "http://0.0.0.0:5000"
        
    def generate_report(self, template_id: int, manual_run: bool = False) -> Dict[str, Any]:
        """Generate a report from a template"""
        template = ReportTemplate.query.get(template_id)
        if not template or not template.active:
            return {"success": False, "error": "Template not found or inactive"}
        
        # Create report run record
        run = ReportRun()
        run.template_id = template_id
        run.status = 'running'
        db.session.add(run)
        db.session.commit()
        
        try:
            # Gather dashboard data
            dashboard_data = self._collect_dashboard_data(template)
            
            # Generate HTML report
            html_content = self._render_html_report(template, dashboard_data)
            
            # Convert to PDF
            pdf_path = self._generate_pdf(template, html_content, run.id)
            
            # Send emails
            emails_sent = self._send_report_emails(template, pdf_path)
            
            # Update run record
            run.status = 'completed'
            run.pdf_path = pdf_path
            run.emails_sent = emails_sent
            run.completed_at = datetime.utcnow()
            
            # Update template last run time
            template.last_run_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                "success": True,
                "run_id": run.id,
                "pdf_path": pdf_path,
                "emails_sent": emails_sent
            }
            
        except Exception as e:
            logging.error(f"Report generation failed: {str(e)}")
            run.status = 'failed'
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            db.session.commit()
            
            return {"success": False, "error": str(e)}
    
    def _collect_dashboard_data(self, template: ReportTemplate) -> Dict[str, Any]:
        """Collect data from dashboard API endpoints"""
        data = {}
        
        # Parse filters if any
        filters = {}
        if template.filters:
            try:
                filters = json.loads(template.filters)
            except:
                pass
        
        # Build filter query string
        filter_params = self._build_filter_params(filters)
        
        # Core dashboard endpoints
        endpoints = {
            'problems_trend': f'/admin/api/dashboard/problems-trend{filter_params}',
            'case_conversion': f'/admin/api/dashboard/case-conversion{filter_params}',
            'project_metrics': f'/admin/api/dashboard/project-metrics{filter_params}',
            'status_breakdown': f'/admin/api/dashboard/status-breakdown{filter_params}',
            'department_heatmap': f'/admin/api/dashboard/department-heatmap{filter_params}',
            'time_to_value': f'/admin/api/dashboard/time-to-value{filter_params}',
            'risks_issues': f'/admin/api/dashboard/risks-issues{filter_params}',
            'roi_waterfall': f'/admin/api/dashboard/roi-waterfall{filter_params}',
            'problem_clusters': f'/admin/api/dashboard/problem-clusters{filter_params}',
            'milestone_burndown': f'/admin/api/dashboard/milestone-burndown{filter_params}',
            'resource_utilization': f'/admin/api/dashboard/resource-utilization{filter_params}'
        }
        
        # Fetch data from each endpoint
        for key, endpoint in endpoints.items():
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                if response.status_code == 200:
                    data[key] = response.json()
                else:
                    logging.warning(f"Failed to fetch {key}: {response.status_code}")
                    data[key] = {}
            except Exception as e:
                logging.error(f"Error fetching {key}: {str(e)}")
                data[key] = {}
        
        # Add summary metrics
        data['summary'] = self._calculate_summary_metrics(data)
        data['generated_at'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        data['template'] = {
            'name': template.name,
            'description': template.description,
            'type': template.template_type.value
        }
        
        return data
    
    def _build_filter_params(self, filters: Dict[str, Any]) -> str:
        """Build query string from filters"""
        if not filters:
            return ""
        
        params = []
        for key, value in filters.items():
            if value:
                if isinstance(value, list):
                    params.append(f"{key}={','.join(map(str, value))}")
                else:
                    params.append(f"{key}={value}")
        
        return f"?{'&'.join(params)}" if params else ""
    
    def _calculate_summary_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate high-level summary metrics"""
        summary = {
            'total_problems': 0,
            'total_cases': 0,
            'total_projects': 0,
            'avg_roi': 0,
            'high_risk_projects': 0,
            'overdue_milestones': 0
        }
        
        # Extract metrics from collected data
        try:
            # Problems count
            if 'problems_trend' in data and 'data' in data['problems_trend']:
                summary['total_problems'] = sum(data['problems_trend']['data'])
            
            # Status breakdown totals
            if 'status_breakdown' in data:
                for item in data['status_breakdown']:
                    summary['total_cases'] += item.get('cases', 0)
                    summary['total_projects'] += item.get('projects', 0)
            
            # ROI calculation
            if 'roi_waterfall' in data and data['roi_waterfall']:
                roi_values = [item.get('net_benefit', 0) for item in data['roi_waterfall']]
                if roi_values:
                    summary['avg_roi'] = sum(roi_values) / len(roi_values)
            
            # Risk assessment
            if 'risks_issues' in data:
                summary['high_risk_projects'] = len([
                    p for p in data['risks_issues'] 
                    if p.get('risk_level', '').lower() == 'high'
                ])
            
            # Milestone tracking
            if 'milestone_burndown' in data and 'overdue' in data['milestone_burndown']:
                summary['overdue_milestones'] = data['milestone_burndown']['overdue']
                
        except Exception as e:
            logging.error(f"Error calculating summary metrics: {str(e)}")
        
        return summary
    
    def _render_html_report(self, template: ReportTemplate, data: Dict[str, Any]) -> str:
        """Render HTML report using Jinja2 template"""
        
        # Choose template based on report type
        if template.template_type.value == 'Dashboard Summary':
            template_content = self._get_dashboard_summary_template()
        elif template.template_type.value == 'Trend Report':
            template_content = self._get_trend_report_template()
        elif template.template_type.value == 'Risk Report':
            template_content = self._get_risk_report_template()
        else:
            template_content = self._get_custom_report_template()
        
        # Render with Jinja2
        jinja_template = Template(template_content)
        html_content = jinja_template.render(
            data=data,
            template=template,
            generated_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        
        return html_content
    
    def _generate_pdf(self, template: ReportTemplate, html_content: str, run_id: int) -> str:
        """Convert HTML to PDF using WeasyPrint"""
        
        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(os.getcwd(), 'static', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"report_{template.id}_{run_id}_{timestamp}.pdf"
        pdf_path = os.path.join(reports_dir, filename)
        
        # CSS for PDF styling
        css_content = """
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { border-bottom: 2px solid #0d6efd; padding-bottom: 20px; margin-bottom: 30px; }
        .metric-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .chart-section { margin: 20px 0; page-break-inside: avoid; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f8f9fa; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
        """
        
        # Generate PDF
        try:
            weasyprint.HTML(string=html_content).write_pdf(
                pdf_path,
                stylesheets=[weasyprint.CSS(string=css_content)]
            )
            return pdf_path
        except Exception as e:
            logging.error(f"PDF generation failed: {str(e)}")
            raise
    
    def _send_report_emails(self, template: ReportTemplate, pdf_path: str) -> int:
        """Send report via email to mailing list"""
        if not template.mailing_list or not pdf_path:
            return 0
        
        try:
            # Parse mailing list
            mailing_list = json.loads(template.mailing_list)
            
            # Get email addresses
            recipients = []
            for recipient in mailing_list:
                if isinstance(recipient, int):
                    # User ID
                    user = User.query.get(recipient)
                    if user and user.email:
                        recipients.append(user.email)
                elif isinstance(recipient, str):
                    # Role or email
                    if '@' in recipient:
                        recipients.append(recipient)
                    else:
                        # Role-based recipients
                        try:
                            role = RoleEnum(recipient)
                            users = User.query.filter_by(role=role).all()
                            recipients.extend([u.email for u in users if u.email])
                        except:
                            pass
            
            # Send emails with PDF attachment
            emails_sent = 0
            for email in set(recipients):  # Remove duplicates
                try:
                    success = self.notification_service._send_email_with_attachment(
                        to_email=email,
                        subject=f"DeciFrame Report: {template.name}",
                        body=f"""
                        <h2>DeciFrame Automated Report</h2>
                        <p><strong>Report:</strong> {template.name}</p>
                        <p><strong>Type:</strong> {template.template_type.value}</p>
                        <p><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                        <p>Please find the detailed report attached as a PDF.</p>
                        <p>This is an automated message from DeciFrame.</p>
                        """,
                        attachment_path=pdf_path,
                        attachment_name=f"{template.name.replace(' ', '_')}_report.pdf"
                    )
                    if success:
                        emails_sent += 1
                except Exception as e:
                    logging.error(f"Failed to send email to {email}: {str(e)}")
            
            return emails_sent
            
        except Exception as e:
            logging.error(f"Email distribution failed: {str(e)}")
            return 0
    
    def preview_report(self, template_id: int) -> str:
        """Generate HTML preview of report without saving"""
        template = ReportTemplate.query.get(template_id)
        if not template:
            return "<html><body><h1>Template not found</h1></body></html>"
        
        try:
            dashboard_data = self._collect_dashboard_data(template)
            html_content = self._render_html_report(template, dashboard_data)
            return html_content
        except Exception as e:
            return f"<html><body><h1>Error generating preview</h1><p>{str(e)}</p></body></html>"
    
    def _get_dashboard_summary_template(self) -> str:
        """HTML template for dashboard summary reports"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>{{ template.name }} - Dashboard Summary</title>
    <meta charset="utf-8">
</head>
<body>
    <div class="header">
        <h1>{{ template.name }}</h1>
        <p><strong>Report Type:</strong> {{ template.template_type.value }}</p>
        <p><strong>Generated:</strong> {{ generated_at }}</p>
        {% if template.description %}
        <p><strong>Description:</strong> {{ template.description }}</p>
        {% endif %}
    </div>
    
    <div class="summary-section">
        <h2>Executive Summary</h2>
        <div class="metric-card">
            <h3>Key Metrics</h3>
            <table>
                <tr><td><strong>Total Problems:</strong></td><td>{{ data.summary.total_problems }}</td></tr>
                <tr><td><strong>Total Business Cases:</strong></td><td>{{ data.summary.total_cases }}</td></tr>
                <tr><td><strong>Total Projects:</strong></td><td>{{ data.summary.total_projects }}</td></tr>
                <tr><td><strong>Average ROI:</strong></td><td>{{ "%.1f"|format(data.summary.avg_roi) }}%</td></tr>
                <tr><td><strong>High Risk Projects:</strong></td><td>{{ data.summary.high_risk_projects }}</td></tr>
                <tr><td><strong>Overdue Milestones:</strong></td><td>{{ data.summary.overdue_milestones }}</td></tr>
            </table>
        </div>
    </div>
    
    <div class="chart-section">
        <h2>Trends & Analysis</h2>
        
        <h3>Problem Creation Trends</h3>
        <div class="metric-card">
            {% if data.problems_trend.labels %}
            <p><strong>Recent Activity:</strong> {{ data.problems_trend.data|sum }} problems reported in the last 90 days</p>
            <p><strong>Peak Period:</strong> {{ data.problems_trend.labels[data.problems_trend.data.index(data.problems_trend.data|max)] if data.problems_trend.data else 'N/A' }}</p>
            {% else %}
            <p>No problem trend data available</p>
            {% endif %}
        </div>
        
        <h3>Project Performance</h3>
        <div class="metric-card">
            {% if data.project_metrics %}
            <p><strong>On-Time Projects:</strong> {{ data.project_metrics.get('on_time', 0) }}%</p>
            <p><strong>Delayed Projects:</strong> {{ data.project_metrics.get('delayed', 0) }}%</p>
            {% else %}
            <p>No project metrics available</p>
            {% endif %}
        </div>
        
        <h3>Resource Utilization</h3>
        <div class="metric-card">
            {% if data.resource_utilization %}
            <p><strong>BA/PM Utilization:</strong> {{ data.resource_utilization.get('utilization', 0) }}%</p>
            <p><strong>Capacity Status:</strong> {{ 'Over-utilized' if data.resource_utilization.get('utilization', 0) > 90 else 'Normal' if data.resource_utilization.get('utilization', 0) > 70 else 'Under-utilized' }}</p>
            {% else %}
            <p>No resource utilization data available</p>
            {% endif %}
        </div>
    </div>
    
    <div class="footer">
        <p>This report was automatically generated by DeciFrame on {{ generated_at }}</p>
        <p>For questions about this report, please contact your system administrator.</p>
    </div>
</body>
</html>
        """
    
    def _get_trend_report_template(self) -> str:
        """HTML template for trend analysis reports"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>{{ template.name }} - Trend Analysis</title>
    <meta charset="utf-8">
</head>
<body>
    <div class="header">
        <h1>{{ template.name }}</h1>
        <p><strong>Report Type:</strong> Trend Analysis</p>
        <p><strong>Generated:</strong> {{ generated_at }}</p>
    </div>
    
    <div class="trends-section">
        <h2>Problem & Case Conversion Trends</h2>
        <div class="metric-card">
            {% if data.case_conversion.labels %}
            <h3>Monthly Conversion Analysis</h3>
            <table>
                <tr><th>Month</th><th>Problems</th><th>Cases</th><th>Conversion Rate</th></tr>
                {% for i in range(data.case_conversion.labels|length) %}
                <tr>
                    <td>{{ data.case_conversion.labels[i] }}</td>
                    <td>{{ data.case_conversion.problems[i] if i < data.case_conversion.problems|length else 0 }}</td>
                    <td>{{ data.case_conversion.cases[i] if i < data.case_conversion.cases|length else 0 }}</td>
                    <td>{{ "%.1f"|format((data.case_conversion.cases[i] / data.case_conversion.problems[i] * 100) if i < data.case_conversion.problems|length and data.case_conversion.problems[i] > 0 else 0) }}%</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p>No conversion trend data available</p>
            {% endif %}
        </div>
        
        <h2>Department Performance Trends</h2>
        <div class="metric-card">
            {% if data.department_heatmap %}
            <table>
                <tr><th>Department</th><th>Problems</th><th>Cases</th><th>Projects</th><th>ROI</th></tr>
                {% for dept in data.department_heatmap %}
                <tr>
                    <td>{{ dept.department }}</td>
                    <td>{{ dept.problems }}</td>
                    <td>{{ dept.cases }}</td>
                    <td>{{ dept.projects }}</td>
                    <td>{{ "%.1f"|format(dept.roi) }}%</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p>No department performance data available</p>
            {% endif %}
        </div>
    </div>
    
    <div class="footer">
        <p>This trend analysis was automatically generated by DeciFrame on {{ generated_at }}</p>
    </div>
</body>
</html>
        """
    
    def _get_risk_report_template(self) -> str:
        """HTML template for risk assessment reports"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>{{ template.name }} - Risk Assessment</title>
    <meta charset="utf-8">
</head>
<body>
    <div class="header">
        <h1>{{ template.name }}</h1>
        <p><strong>Report Type:</strong> Risk Assessment</p>
        <p><strong>Generated:</strong> {{ generated_at }}</p>
    </div>
    
    <div class="risk-section">
        <h2>Project Risk Analysis</h2>
        <div class="metric-card">
            {% if data.risks_issues %}
            <table>
                <tr><th>Project</th><th>Risk Level</th><th>Issues Count</th><th>Status</th></tr>
                {% for project in data.risks_issues %}
                <tr>
                    <td>{{ project.name }}</td>
                    <td style="color: {{ 'red' if project.risk_level == 'High' else 'orange' if project.risk_level == 'Medium' else 'green' }}">
                        {{ project.risk_level }}
                    </td>
                    <td>{{ project.issues_count }}</td>
                    <td>{{ project.status }}</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p>No risk data available</p>
            {% endif %}
        </div>
        
        <h2>Milestone Risk Assessment</h2>
        <div class="metric-card">
            {% if data.milestone_burndown %}
            <p><strong>Overdue Milestones:</strong> {{ data.milestone_burndown.get('overdue', 0) }}</p>
            <p><strong>Due This Week:</strong> {{ data.milestone_burndown.get('due_soon', 0) }}</p>
            <p><strong>Burn Rate:</strong> {{ data.milestone_burndown.get('burn_rate', 'N/A') }}</p>
            {% else %}
            <p>No milestone data available</p>
            {% endif %}
        </div>
        
        <h2>Resource Constraints</h2>
        <div class="metric-card">
            {% if data.resource_utilization %}
            <p><strong>Current Utilization:</strong> {{ data.resource_utilization.get('utilization', 0) }}%</p>
            {% if data.resource_utilization.get('utilization', 0) > 90 %}
            <p style="color: red;"><strong>WARNING:</strong> Resource over-utilization detected</p>
            {% endif %}
            {% else %}
            <p>No resource utilization data available</p>
            {% endif %}
        </div>
    </div>
    
    <div class="footer">
        <p>This risk assessment was automatically generated by DeciFrame on {{ generated_at }}</p>
    </div>
</body>
</html>
        """
    
    def _get_custom_report_template(self) -> str:
        """HTML template for custom reports"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>{{ template.name }} - Custom Report</title>
    <meta charset="utf-8">
</head>
<body>
    <div class="header">
        <h1>{{ template.name }}</h1>
        <p><strong>Report Type:</strong> Custom</p>
        <p><strong>Generated:</strong> {{ generated_at }}</p>
    </div>
    
    <div class="content-section">
        <h2>Comprehensive Data Analysis</h2>
        
        {% if data.summary %}
        <div class="metric-card">
            <h3>Summary Metrics</h3>
            <table>
                {% for key, value in data.summary.items() %}
                <tr><td><strong>{{ key.replace('_', ' ').title() }}:</strong></td><td>{{ value }}</td></tr>
                {% endfor %}
            </table>
        </div>
        {% endif %}
        
        {% for section_name, section_data in data.items() %}
        {% if section_name not in ['summary', 'generated_at', 'template'] and section_data %}
        <div class="metric-card">
            <h3>{{ section_name.replace('_', ' ').title() }}</h3>
            {% if section_data is mapping %}
                <table>
                {% for key, value in section_data.items() %}
                    <tr><td><strong>{{ key }}:</strong></td><td>{{ value }}</td></tr>
                {% endfor %}
                </table>
            {% elif section_data is iterable and section_data is not string %}
                <p>Data points: {{ section_data|length }}</p>
            {% else %}
                <p>{{ section_data }}</p>
            {% endif %}
        </div>
        {% endif %}
        {% endfor %}
    </div>
    
    <div class="footer">
        <p>This custom report was automatically generated by DeciFrame on {{ generated_at }}</p>
    </div>
</body>
</html>
        """