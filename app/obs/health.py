"""
Health monitoring and metrics endpoints
"""
import time
from datetime import datetime
from flask import Blueprint, jsonify, Response, g
from models import db
from sqlalchemy import text
import psutil


# Metrics storage - in production, use Redis or proper metrics backend
metrics_storage = {
    'requests_total': {},
    'request_durations': [],
    'db_connections': 0,
    'errors_total': {},
}

health_bp = Blueprint('health', __name__, url_prefix='/health')


def record_request_metric(route, method, status_code, duration):
    """Record request metrics"""
    key = f"{route}:{method}:{status_code}"
    metrics_storage['requests_total'][key] = metrics_storage['requests_total'].get(key, 0) + 1
    metrics_storage['request_durations'].append(duration)
    
    # Keep only last 1000 durations for histogram
    if len(metrics_storage['request_durations']) > 1000:
        metrics_storage['request_durations'] = metrics_storage['request_durations'][-1000:]


def record_error_metric(error_type):
    """Record error metrics"""
    metrics_storage['errors_total'][error_type] = metrics_storage['errors_total'].get(error_type, 0) + 1


@health_bp.route('/', methods=['GET'])
def health_check():
    """Liveness and readiness check"""
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }
    
    overall_healthy = True
    
    # Database connectivity check
    try:
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        health_status['checks']['database'] = {
            'status': 'healthy',
            'response_time_ms': None
        }
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_healthy = False
    
    # Memory check
    try:
        memory = psutil.virtual_memory()
        memory_usage_percent = memory.percent
        health_status['checks']['memory'] = {
            'status': 'healthy' if memory_usage_percent < 90 else 'degraded',
            'usage_percent': memory_usage_percent,
            'available_mb': memory.available // 1024 // 1024
        }
        if memory_usage_percent >= 95:
            overall_healthy = False
    except Exception as e:
        health_status['checks']['memory'] = {
            'status': 'unknown',
            'error': str(e)
        }
    
    # Disk space check
    try:
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        health_status['checks']['disk'] = {
            'status': 'healthy' if disk_usage_percent < 85 else 'degraded',
            'usage_percent': round(disk_usage_percent, 2),
            'available_gb': round(disk.free / 1024 / 1024 / 1024, 2)
        }
        if disk_usage_percent >= 95:
            overall_healthy = False
    except Exception as e:
        health_status['checks']['disk'] = {
            'status': 'unknown',
            'error': str(e)
        }
    
    # Overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
    elif any(check.get('status') == 'degraded' for check in health_status['checks'].values()):
        health_status['status'] = 'degraded'
    
    status_code = 200 if overall_healthy else 503
    return jsonify(health_status), status_code


@health_bp.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus-compatible metrics endpoint"""
    
    lines = []
    
    # Help and type declarations
    lines.extend([
        '# HELP http_requests_total Total number of HTTP requests',
        '# TYPE http_requests_total counter',
    ])
    
    # Request counter metrics
    for key, count in metrics_storage['requests_total'].items():
        route, method, status = key.split(':', 2)
        lines.append(f'http_requests_total{{route="{route}",method="{method}",status="{status}"}} {count}')
    
    lines.extend([
        '',
        '# HELP http_request_duration_seconds HTTP request duration histogram',
        '# TYPE http_request_duration_seconds histogram',
    ])
    
    # Request duration histogram
    durations = metrics_storage['request_durations']
    if durations:
        buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        bucket_counts = {bucket: 0 for bucket in buckets}
        
        for duration in durations:
            for bucket in buckets:
                if duration <= bucket:
                    bucket_counts[bucket] += 1
        
        for bucket, count in bucket_counts.items():
            lines.append(f'http_request_duration_seconds_bucket{{le="{bucket}"}} {count}')
        
        lines.append(f'http_request_duration_seconds_bucket{{le="+Inf"}} {len(durations)}')
        lines.append(f'http_request_duration_seconds_sum {sum(durations)}')
        lines.append(f'http_request_duration_seconds_count {len(durations)}')
    
    lines.extend([
        '',
        '# HELP application_errors_total Total number of application errors',
        '# TYPE application_errors_total counter',
    ])
    
    # Error metrics
    for error_type, count in metrics_storage['errors_total'].items():
        lines.append(f'application_errors_total{{type="{error_type}"}} {count}')
    
    # System metrics
    lines.extend([
        '',
        '# HELP system_memory_usage_percent Memory usage percentage',
        '# TYPE system_memory_usage_percent gauge',
    ])
    
    try:
        memory = psutil.virtual_memory()
        lines.append(f'system_memory_usage_percent {memory.percent}')
    except:
        pass
    
    lines.extend([
        '',
        '# HELP system_cpu_usage_percent CPU usage percentage',
        '# TYPE system_cpu_usage_percent gauge',
    ])
    
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        lines.append(f'system_cpu_usage_percent {cpu_percent}')
    except:
        pass
    
    return Response('\n'.join(lines) + '\n', mimetype='text/plain')


def setup_metrics_middleware(app):
    """Setup metrics collection middleware"""
    
    @app.before_request
    def before_request_metrics():
        g.start_time = time.time()
    
    @app.after_request
    def after_request_metrics(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            route = request.endpoint or request.path
            record_request_metric(route, request.method, response.status_code, duration)
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        record_error_metric(type(e).__name__)
        # Re-raise the exception to let Flask handle it normally
        raise e
    
    return app