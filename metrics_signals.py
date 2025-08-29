"""
SQLAlchemy event hooks that invalidate the executive metrics cache when key models change.
"""
from sqlalchemy import event
from executive_metrics import invalidate_metrics, get_org_id_from_instance

def register_metrics_signals():
    """Register SQLAlchemy event listeners for cache invalidation"""
    try:
        # Import models - try different paths for flexibility
        from models import Problem, BusinessCase, Project
        
        def _invalidate_for(mapper, connection, target):
            org_id = get_org_id_from_instance(target)
            if org_id:
                invalidate_metrics(org_id)
                print(f"🔄 Metrics cache invalidated for org {org_id}")

        # Register listeners for all relevant models
        for model in (Problem, BusinessCase, Project):
            event.listen(model, "after_insert", _invalidate_for)
            event.listen(model, "after_update", _invalidate_for)
            event.listen(model, "after_delete", _invalidate_for)
        
        print("✓ Metrics cache invalidation signals registered")
        return True
        
    except ImportError as e:
        print(f"⚠️ Could not register metrics signals: {e}")
        return False