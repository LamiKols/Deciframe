"""
Monitoring Configuration Module
Centralized configuration for all monitoring systems
"""

import os
from typing import Dict, Any, Optional

class MonitoringConfig:
    """Configuration class for monitoring systems"""
    
    def __init__(self):
        self.sentry_dsn = os.getenv('SENTRY_DSN')
        self.sentry_environment = os.getenv('SENTRY_ENVIRONMENT', 'production')
        self.sentry_traces_sample_rate = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1'))
        
        # Health check configuration
        self.health_check_timeout = int(os.getenv('HEALTH_CHECK_TIMEOUT', '30'))
        self.health_check_database_enabled = os.getenv('HEALTH_CHECK_DATABASE', 'true').lower() == 'true'
        
        # Prometheus configuration
        self.prometheus_enabled = os.getenv('PROMETHEUS_ENABLED', 'true').lower() == 'true'
        self.prometheus_path = os.getenv('PROMETHEUS_PATH', '/metrics')
        
        # Alerting thresholds
        self.alert_thresholds = {
            'response_time_ms': int(os.getenv('ALERT_RESPONSE_TIME_MS', '5000')),
            'error_rate_percent': float(os.getenv('ALERT_ERROR_RATE_PERCENT', '5.0')),
            'memory_usage_percent': int(os.getenv('ALERT_MEMORY_USAGE_PERCENT', '85')),
            'disk_usage_percent': int(os.getenv('ALERT_DISK_USAGE_PERCENT', '90'))
        }
    
    @property
    def is_sentry_enabled(self) -> bool:
        """Check if Sentry error tracking is enabled"""
        return bool(self.sentry_dsn)
    
    @property
    def monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status"""
        return {
            'sentry': {
                'enabled': self.is_sentry_enabled,
                'environment': self.sentry_environment,
                'traces_sample_rate': self.sentry_traces_sample_rate
            },
            'health_checks': {
                'enabled': True,
                'database_check': self.health_check_database_enabled,
                'timeout_seconds': self.health_check_timeout
            },
            'prometheus': {
                'enabled': self.prometheus_enabled,
                'metrics_path': self.prometheus_path
            },
            'alert_thresholds': self.alert_thresholds
        }
    
    def get_sentry_config(self) -> Optional[Dict[str, Any]]:
        """Get Sentry SDK configuration"""
        if not self.is_sentry_enabled:
            return None
        
        return {
            'dsn': self.sentry_dsn,
            'environment': self.sentry_environment,
            'traces_sample_rate': self.sentry_traces_sample_rate,
            'send_default_pii': False,
            'attach_stacktrace': True,
            'before_send': self._sentry_before_send
        }
    
    def _sentry_before_send(self, event, hint):
        """Filter sensitive data before sending to Sentry"""
        # Remove sensitive headers and data
        if 'request' in event:
            headers = event['request'].get('headers', {})
            sensitive_headers = ['authorization', 'cookie', 'x-api-key']
            for header in sensitive_headers:
                if header in headers:
                    headers[header] = '[Filtered]'
        
        return event

# Global monitoring configuration instance
monitoring_config = MonitoringConfig()