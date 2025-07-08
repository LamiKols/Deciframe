"""
ML Model Training Scheduler for DeciFrame
Automatically retrains ML models on a weekly schedule using APScheduler
"""

import os
import sys
import logging
import threading
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.train_models import MLModelTrainer

logger = logging.getLogger(__name__)

class MLScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.trainer = MLModelTrainer()
        self.running = False
        
    def start(self):
        """Start the ML training scheduler"""
        if not self.running:
            # Schedule weekly retraining on Sundays at 2 AM
            self.scheduler.add_job(
                func=self.retrain_models,
                trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
                id='weekly_model_training',
                name='Weekly ML Model Retraining',
                replace_existing=True
            )
            
            # Schedule monthly comprehensive retraining
            self.scheduler.add_job(
                func=self.comprehensive_retrain,
                trigger=CronTrigger(day=1, hour=3, minute=0),
                id='monthly_comprehensive_training',
                name='Monthly Comprehensive ML Training',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.running = True
            logger.info("🤖 ML training scheduler started")
            
    def stop(self):
        """Stop the ML training scheduler"""
        if self.running:
            self.scheduler.shutdown()
            self.running = False
            logger.info("🤖 ML training scheduler stopped")
    
    def retrain_models(self):
        """Execute weekly model retraining"""
        logger.info("🔄 Starting scheduled ML model retraining...")
        
        def training_thread():
            try:
                success = self.trainer.train_all_models()
                if success:
                    logger.info("✅ Scheduled ML model retraining completed successfully")
                else:
                    logger.error("❌ Scheduled ML model retraining failed")
            except Exception as e:
                logger.error(f"❌ Error in scheduled ML training: {str(e)}")
        
        # Run training in separate thread to avoid blocking scheduler
        thread = threading.Thread(target=training_thread, daemon=True)
        thread.start()
    
    def comprehensive_retrain(self):
        """Execute monthly comprehensive retraining with additional validation"""
        logger.info("🔄 Starting comprehensive ML model retraining...")
        
        def comprehensive_training_thread():
            try:
                # First backup existing models
                self._backup_existing_models()
                
                # Train new models
                success = self.trainer.train_all_models()
                
                if success:
                    logger.info("✅ Comprehensive ML model retraining completed successfully")
                    # Clean up old backups (keep last 3 months)
                    self._cleanup_old_backups()
                else:
                    logger.error("❌ Comprehensive ML model retraining failed")
                    # Restore from backup if needed
                    self._restore_from_backup()
                    
            except Exception as e:
                logger.error(f"❌ Error in comprehensive ML training: {str(e)}")
                self._restore_from_backup()
        
        thread = threading.Thread(target=comprehensive_training_thread, daemon=True)
        thread.start()
    
    def manual_retrain(self):
        """Manually trigger model retraining"""
        logger.info("🔄 Starting manual ML model retraining...")
        
        try:
            success = self.trainer.train_all_models()
            if success:
                logger.info("✅ Manual ML model retraining completed successfully")
                return {"success": True, "message": "Models retrained successfully"}
            else:
                logger.error("❌ Manual ML model retraining failed")
                return {"success": False, "error": "Training failed"}
        except Exception as e:
            logger.error(f"❌ Error in manual ML training: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _backup_existing_models(self):
        """Backup existing models before retraining"""
        models_dir = self.trainer.models_dir
        backup_dir = os.path.join(models_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'models_backup_{timestamp}')
        os.makedirs(backup_path, exist_ok=True)
        
        # Copy existing model files
        import shutil
        model_files = [
            'success_model.pkl', 'success_scaler.pkl', 'success_features.pkl',
            'cycle_time_model.pkl', 'cycle_time_scaler.pkl', 'cycle_time_features.pkl',
            'anomaly_model.pkl', 'anomaly_scaler.pkl', 'anomaly_features.pkl',
            'training_metadata.pkl'
        ]
        
        for filename in model_files:
            src_path = os.path.join(models_dir, filename)
            if os.path.exists(src_path):
                dst_path = os.path.join(backup_path, filename)
                shutil.copy2(src_path, dst_path)
        
        logger.info(f"🗂️ Models backed up to {backup_path}")
    
    def _restore_from_backup(self):
        """Restore models from most recent backup"""
        backup_dir = os.path.join(self.trainer.models_dir, 'backups')
        if not os.path.exists(backup_dir):
            logger.warning("⚠️ No backup directory found for model restoration")
            return
        
        # Find most recent backup
        backups = [d for d in os.listdir(backup_dir) if d.startswith('models_backup_')]
        if not backups:
            logger.warning("⚠️ No model backups found for restoration")
            return
        
        latest_backup = sorted(backups)[-1]
        backup_path = os.path.join(backup_dir, latest_backup)
        
        # Restore model files
        import shutil
        model_files = [
            'success_model.pkl', 'success_scaler.pkl', 'success_features.pkl',
            'cycle_time_model.pkl', 'cycle_time_scaler.pkl', 'cycle_time_features.pkl',
            'anomaly_model.pkl', 'anomaly_scaler.pkl', 'anomaly_features.pkl',
            'training_metadata.pkl'
        ]
        
        for filename in model_files:
            backup_file = os.path.join(backup_path, filename)
            if os.path.exists(backup_file):
                dst_path = os.path.join(self.trainer.models_dir, filename)
                shutil.copy2(backup_file, dst_path)
        
        logger.info(f"🔄 Models restored from backup: {latest_backup}")
    
    def _cleanup_old_backups(self):
        """Clean up old model backups (keep last 3 months)"""
        backup_dir = os.path.join(self.trainer.models_dir, 'backups')
        if not os.path.exists(backup_dir):
            return
        
        import shutil
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        for backup_name in os.listdir(backup_dir):
            if backup_name.startswith('models_backup_'):
                try:
                    # Extract timestamp from backup name
                    timestamp_str = backup_name.replace('models_backup_', '')
                    backup_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    
                    if backup_date < cutoff_date:
                        backup_path = os.path.join(backup_dir, backup_name)
                        shutil.rmtree(backup_path)
                        logger.info(f"🗑️ Cleaned up old backup: {backup_name}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error cleaning up backup {backup_name}: {str(e)}")
    
    def get_status(self):
        """Get scheduler status information"""
        jobs = []
        if self.running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
        
        return {
            'running': self.running,
            'jobs': jobs,
            'models_directory': self.trainer.models_dir
        }

# Global scheduler instance
ml_scheduler = MLScheduler()

def init_ml_scheduler():
    """Initialize and start the ML training scheduler"""
    try:
        ml_scheduler.start()
        return True
    except Exception as e:
        logger.error(f"Failed to start ML scheduler: {str(e)}")
        return False

def stop_ml_scheduler():
    """Stop the ML training scheduler"""
    try:
        ml_scheduler.stop()
        return True
    except Exception as e:
        logger.error(f"Failed to stop ML scheduler: {str(e)}")
        return False

def manual_retrain_models():
    """Manually trigger model retraining"""
    return ml_scheduler.manual_retrain()

def get_scheduler_status():
    """Get ML scheduler status"""
    return ml_scheduler.get_status()