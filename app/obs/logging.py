"""
JSON logging with request ID middleware and user context
"""
import json
import logging
import uuid
from datetime import datetime
from flask import g, request, has_request_context
from flask_login import current_user


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request context if available
        if has_request_context():
            log_entry.update({
                'request_id': getattr(g, 'request_id', None),
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')[:200],
            })
            
            # Add user context if authenticated
            if hasattr(current_user, 'id') and current_user.is_authenticated:
                log_entry.update({
                    'user_id': current_user.id,
                    'user_email': getattr(current_user, 'email', None),
                    'user_role': getattr(current_user, 'role', None),
                    'organization_id': getattr(current_user, 'organization_id', None),
                })
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


def setup_json_logging(app):
    """Setup JSON logging for the application"""
    
    # Create JSON formatter
    json_formatter = JSONFormatter()
    
    # Configure root logger
    logging.getLogger().setLevel(logging.INFO)
    
    # Configure app logger
    if not app.logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(json_formatter)
        app.logger.addHandler(handler)
    
    app.logger.setLevel(logging.INFO)
    
    # Configure request ID middleware
    @app.before_request
    def before_request():
        g.request_id = str(uuid.uuid4())
        g.request_start_time = datetime.utcnow()
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'request_start_time'):
            duration = (datetime.utcnow() - g.request_start_time).total_seconds()
            app.logger.info(
                "Request completed",
                extra={
                    'status_code': response.status_code,
                    'response_size': len(response.get_data()),
                    'duration_seconds': duration,
                }
            )
        
        # Add request ID to response headers
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
            
        return response
    
    return app


def get_logger(name):
    """Get a logger with JSON formatting"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    return logger