"""
Monitoring Dashboard Module
Provides real-time monitoring insights and system health visualization
"""

import psutil
import time
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import text, func
from extensions import db
from models import AuditLog, User, Problem, BusinessCase, Project
from monitoring.config import monitoring_config

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

@monitoring_bp.route('/dashboard')
def dashboard():
    """Monitoring dashboard with real-time system metrics"""
    system_stats = get_system_stats()
    database_stats = get_database_stats()
    application_stats = get_application_stats()
    
    return render_template('monitoring/dashboard.html', 
                         system_stats=system_stats,
                         database_stats=database_stats,
                         application_stats=application_stats,
                         monitoring_config=monitoring_config.monitoring_status)

@monitoring_bp.route('/api/system-stats')
def api_system_stats():
    """API endpoint for real-time system statistics"""
    return jsonify(get_system_stats())

@monitoring_bp.route('/api/alerts')
def api_alerts():
    """API endpoint for system alerts and notifications"""
    alerts = check_system_alerts()
    return jsonify({'alerts': alerts, 'count': len(alerts)})

def get_system_stats():
    """Get comprehensive system performance statistics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu': {
                'usage_percent': cpu_percent,
                'count': psutil.cpu_count(),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            },
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'usage_percent': memory.percent,
                'available_gb': round(memory.available / (1024**3), 2)
            },
            'disk': {
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'usage_percent': round((disk.used / disk.total) * 100, 1),
                'free_gb': round(disk.free / (1024**3), 2)
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_database_stats():
    """Get database performance and usage statistics"""
    try:
        # Database connection test
        db_status = db.session.execute(text('SELECT 1')).scalar()
        
        # Table statistics
        tables_stats = []
        for model_class in [User, Problem, BusinessCase, Project, AuditLog]:
            count = db.session.query(func.count(model_class.id)).scalar()
            tables_stats.append({
                'table': model_class.__tablename__,
                'count': count
            })
        
        # Recent activity (last 24 hours)
        yesterday = datetime.now() - timedelta(hours=24)
        recent_audit_logs = db.session.query(func.count(AuditLog.id)).filter(
            AuditLog.timestamp >= yesterday
        ).scalar()
        
        return {
            'status': 'connected' if db_status == 1 else 'error',
            'tables': tables_stats,
            'recent_activity': {
                'audit_logs_24h': recent_audit_logs
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_application_stats():
    """Get application-specific performance metrics"""
    try:
        # User activity statistics
        total_users = db.session.query(func.count(User.id)).scalar()
        active_users_today = db.session.query(func.count(User.id)).filter(
            User.last_login >= datetime.now().date()
        ).scalar() if hasattr(User, 'last_login') else 0
        
        # Content statistics
        open_problems = db.session.query(func.count(Problem.id)).filter(
            Problem.status.in_(['Open', 'In_Progress'])
        ).scalar()
        
        pending_cases = db.session.query(func.count(BusinessCase.id)).filter(
            BusinessCase.status == 'Pending'
        ).scalar()
        
        active_projects = db.session.query(func.count(Project.id)).filter(
            Project.status.in_(['Open', 'In_Progress'])
        ).scalar()
        
        return {
            'users': {
                'total': total_users,
                'active_today': active_users_today
            },
            'content': {
                'open_problems': open_problems,
                'pending_cases': pending_cases,
                'active_projects': active_projects
            },
            'monitoring': monitoring_config.monitoring_status,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def check_system_alerts():
    """Check system thresholds and generate alerts"""
    alerts = []
    thresholds = monitoring_config.alert_thresholds
    
    try:
        # Check system metrics
        system_stats = get_system_stats()
        
        if 'cpu' in system_stats and system_stats['cpu']['usage_percent'] > 90:
            alerts.append({
                'level': 'critical',
                'type': 'cpu',
                'message': f"High CPU usage: {system_stats['cpu']['usage_percent']}%",
                'timestamp': datetime.now().isoformat()
            })
        
        if 'memory' in system_stats and system_stats['memory']['usage_percent'] > thresholds['memory_usage_percent']:
            alerts.append({
                'level': 'warning',
                'type': 'memory',
                'message': f"High memory usage: {system_stats['memory']['usage_percent']}%",
                'timestamp': datetime.now().isoformat()
            })
        
        if 'disk' in system_stats and system_stats['disk']['usage_percent'] > thresholds['disk_usage_percent']:
            alerts.append({
                'level': 'warning',
                'type': 'disk',
                'message': f"High disk usage: {system_stats['disk']['usage_percent']}%",
                'timestamp': datetime.now().isoformat()
            })
        
        # Check database connectivity
        database_stats = get_database_stats()
        if database_stats['status'] != 'connected':
            alerts.append({
                'level': 'critical',
                'type': 'database',
                'message': 'Database connection failed',
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        alerts.append({
            'level': 'error',
            'type': 'monitoring',
            'message': f'Monitoring system error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })
    
    return alerts