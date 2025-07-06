"""
Admin routes for monitoring workflow event queue
"""

from flask import Blueprint, render_template, jsonify
from auth.decorators import require_auth
from auth.utils import get_current_user
from workflows.event_queue import get_queue_stats

queue_admin = Blueprint('queue_admin', __name__)

@queue_admin.route('/admin/workflow-queue')
@require_auth
def queue_status():
    """Admin page for monitoring workflow queue status"""
    user = get_current_user()
    if user.role.value not in ['Admin', 'Director', 'CEO']:
        return "Access denied", 403
    
    return render_template('admin/workflow_queue.html', user=user)

@queue_admin.route('/api/admin/workflow-queue/stats')
@require_auth  
def queue_stats_api():
    """API endpoint for workflow queue statistics"""
    user = get_current_user()
    if user.role.value not in ['Admin', 'Director', 'CEO']:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        stats = get_queue_stats()
        return jsonify({
            'status': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500