"""
Asynchronous Event Queue System for Workflow Processing
Provides background processing for workflow events to improve response times
"""

import queue
import threading
import logging
from typing import Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowEventQueue:
    """Thread-safe event queue for background workflow processing"""
    
    def __init__(self):
        self.event_queue = queue.Queue(maxsize=1000)  # Prevent memory issues
        self.worker_thread = None
        self.running = False
        self.processed_count = 0
        self.error_count = 0
        
    def start(self):
        """Start the background worker thread"""
        if self.running:
            logger.warning("🔄 Event queue already running")
            return
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("🚀 Workflow event queue started")
        
    def stop(self):
        """Stop the background worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        logger.info("🛑 Workflow event queue stopped")
        
    def enqueue_event(self, event_name: str, context: Dict[str, Any]) -> bool:
        """Add an event to the processing queue"""
        try:
            # Add timestamp for processing metrics
            event_data = {
                'name': event_name,
                'context': context,
                'timestamp': datetime.utcnow().isoformat(),
                'retry_count': 0
            }
            
            self.event_queue.put(event_data, block=False)
            logger.debug(f"📥 Queued event: {event_name}")
            return True
            
        except queue.Full:
            logger.error(f"❌ Event queue full, dropping event: {event_name}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to queue event {event_name}: {e}")
            return False
    
    def _worker_loop(self):
        """Background worker that processes queued events"""
        logger.info("🔄 Event queue worker started")
        
        while self.running:
            try:
                # Wait for events with timeout to allow clean shutdown
                event_data = self.event_queue.get(timeout=1.0)
                self._process_event(event_data)
                self.event_queue.task_done()
                
            except queue.Empty:
                continue  # Timeout, check if still running
            except Exception as e:
                logger.error(f"❌ Worker loop error: {e}")
                
        logger.info("🔄 Event queue worker stopped")
    
    def _process_event(self, event_data: Dict[str, Any]):
        """Process a single workflow event"""
        try:
            # Import inside Flask app context to avoid circular imports
            with self._get_app_context():
                from workflows.processor import dispatch_event
                
                event_name = event_data['name']
                context = event_data['context']
                
                logger.info(f"🔄 Processing event: {event_name}")
                dispatch_event(event_name, context)
                
                self.processed_count += 1
                logger.debug(f"✅ Event processed: {event_name}")
            
        except Exception as e:
            self.error_count += 1
            event_name = event_data.get('name', 'unknown')
            logger.error(f"❌ Failed to process event {event_name}: {e}")
            
            # Implement retry logic
            retry_count = event_data.get('retry_count', 0)
            if retry_count < 3:  # Max 3 retries
                event_data['retry_count'] = retry_count + 1
                logger.info(f"🔄 Retrying event {event_name} (attempt {retry_count + 1})")
                try:
                    self.event_queue.put(event_data, block=False)
                except queue.Full:
                    logger.error(f"❌ Queue full, cannot retry event {event_name}")
    
    def _get_app_context(self):
        """Get Flask application context for database operations"""
        try:
            from flask import current_app
            return current_app.app_context()
        except RuntimeError:
            # No app context available, create one
            try:
                from app import app
                return app.app_context()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to get app context: {e}")
                # Fallback - create a mock context that does nothing
                class MockContext:
                    def __enter__(self): return self
                    def __exit__(self, *args): pass
                return MockContext()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue processing statistics"""
        return {
            'running': self.running,
            'queue_size': self.event_queue.qsize(),
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'worker_alive': self.worker_thread.is_alive() if self.worker_thread else False
        }

# Global event queue instance
_event_queue = WorkflowEventQueue()

def start_event_queue():
    """Start the global event queue"""
    _event_queue.start()

def stop_event_queue():
    """Stop the global event queue"""
    _event_queue.stop()

def enqueue_workflow_event(event_name: str, context: Dict[str, Any]) -> bool:
    """Add a workflow event to the background processing queue"""
    return _event_queue.enqueue_event(event_name, context)

def get_queue_stats() -> Dict[str, Any]:
    """Get event queue statistics"""
    return _event_queue.get_stats()

# Auto-start the queue when module is imported
start_event_queue()