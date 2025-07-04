"""
Report Scheduler for DeciFrame
Handles automated scheduling and execution of report generation
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import List
from extensions import db
from models import ReportTemplate, ReportFrequencyEnum
from reports.service import ReportService

class ReportScheduler:
    def __init__(self):
        self.report_service = ReportService()
        self.running = False
        self.scheduler_thread = None
        
    def start(self):
        """Start the report scheduler"""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            logging.info("📊 Report scheduler started")
    
    def stop(self):
        """Stop the report scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logging.info("📊 Report scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check for due reports every minute
                if current_time.second == 0:  # Run at the top of each minute
                    self._check_and_run_due_reports(current_time)
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logging.error(f"Error in report scheduler: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying on error
    
    def _check_and_run_due_reports(self, current_time: datetime):
        """Check for reports that are due to run"""
        
        # Daily reports - run at 7 AM
        if current_time.hour == 7 and current_time.minute == 0:
            self._run_daily_reports()
        
        # Weekly reports - run on Monday at 7 AM
        if (current_time.weekday() == 0 and  # Monday
            current_time.hour == 7 and 
            current_time.minute == 0):
            self._run_weekly_reports()
        
        # Monthly reports - run on 1st of month at 7 AM
        if (current_time.day == 1 and 
            current_time.hour == 7 and 
            current_time.minute == 0):
            self._run_monthly_reports()
    
    def _run_daily_reports(self):
        """Execute all daily reports"""
        daily_templates = ReportTemplate.query.filter_by(
            frequency=ReportFrequencyEnum.Daily,
            active=True
        ).all()
        
        for template in daily_templates:
            if self._should_run_report(template, ReportFrequencyEnum.Daily):
                self._execute_report_async(template)
    
    def _run_weekly_reports(self):
        """Execute all weekly reports"""
        weekly_templates = ReportTemplate.query.filter_by(
            frequency=ReportFrequencyEnum.Weekly,
            active=True
        ).all()
        
        for template in weekly_templates:
            if self._should_run_report(template, ReportFrequencyEnum.Weekly):
                self._execute_report_async(template)
    
    def _run_monthly_reports(self):
        """Execute all monthly reports"""
        monthly_templates = ReportTemplate.query.filter_by(
            frequency=ReportFrequencyEnum.Monthly,
            active=True
        ).all()
        
        for template in monthly_templates:
            if self._should_run_report(template, ReportFrequencyEnum.Monthly):
                self._execute_report_async(template)
    
    def _should_run_report(self, template: ReportTemplate, frequency: ReportFrequencyEnum) -> bool:
        """Check if a report should run based on last execution time"""
        if not template.last_run_at:
            return True
        
        now = datetime.now()
        time_since_last_run = now - template.last_run_at
        
        if frequency == ReportFrequencyEnum.Daily:
            return time_since_last_run >= timedelta(hours=23)  # Allow slight variance
        elif frequency == ReportFrequencyEnum.Weekly:
            return time_since_last_run >= timedelta(days=6, hours=23)
        elif frequency == ReportFrequencyEnum.Monthly:
            return time_since_last_run >= timedelta(days=29, hours=23)
        
        return False
    
    def _execute_report_async(self, template: ReportTemplate):
        """Execute report generation in a separate thread"""
        def run_report():
            try:
                logging.info(f"📊 Running scheduled report: {template.name}")
                result = self.report_service.generate_report(template.id)
                
                if result['success']:
                    logging.info(f"✅ Report '{template.name}' completed successfully. "
                               f"Emails sent: {result.get('emails_sent', 0)}")
                else:
                    logging.error(f"❌ Report '{template.name}' failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logging.error(f"❌ Exception running report '{template.name}': {str(e)}")
        
        # Run in separate thread to avoid blocking scheduler
        report_thread = threading.Thread(target=run_report, daemon=True)
        report_thread.start()
    
    def run_report_now(self, template_id: int) -> dict:
        """Manually trigger a report run immediately"""
        try:
            template = ReportTemplate.query.get(template_id)
            if not template:
                return {"success": False, "error": "Template not found"}
            
            if not template.active:
                return {"success": False, "error": "Template is inactive"}
            
            logging.info(f"📊 Manual report execution: {template.name}")
            result = self.report_service.generate_report(template_id, manual_run=True)
            
            return result
            
        except Exception as e:
            logging.error(f"Error in manual report execution: {str(e)}")
            return {"success": False, "error": str(e)}

# Global scheduler instance
report_scheduler = ReportScheduler()

def init_report_scheduler():
    """Initialize and start the report scheduler"""
    try:
        report_scheduler.start()
        return True
    except Exception as e:
        logging.error(f"Failed to start report scheduler: {str(e)}")
        return False

def stop_report_scheduler():
    """Stop the report scheduler"""
    try:
        report_scheduler.stop()
        return True
    except Exception as e:
        logging.error(f"Failed to stop report scheduler: {str(e)}")
        return False