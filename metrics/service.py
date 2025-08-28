import time
from collections import defaultdict
from typing import Any, Dict, Tuple, List
from cachetools import TTLCache
from sqlalchemy import text

# TTL cache for computed metrics (5 minutes)
cache = TTLCache(maxsize=256, ttl=300)

def _key(org_id: int) -> str:
    return f"metrics:org:{org_id}"

def compute_metrics(db, org_id: int) -> Dict[str, Any]:
    """
    Compute all executive metrics for an organization.
    Uses real models and efficient queries for production data.
    """
    try:
        # Problems funnel & throughput - using actual models
        problems_total = db.session.execute(
            text("SELECT COUNT(*) FROM problems WHERE organization_id=:org_id"), 
            {"org_id": org_id}
        ).scalar() or 0
        
        cases_total = db.session.execute(
            text("SELECT COUNT(*) FROM business_cases WHERE organization_id=:org_id"), 
            {"org_id": org_id}
        ).scalar() or 0
        
        approved_cases = db.session.execute(
            text("SELECT COUNT(*) FROM business_cases WHERE organization_id=:org_id AND status='approved'"), 
            {"org_id": org_id}
        ).scalar() or 0
        
        projects_total = db.session.execute(
            text("SELECT COUNT(*) FROM projects WHERE organization_id=:org_id"), 
            {"org_id": org_id}
        ).scalar() or 0
        
        projects_done = db.session.execute(
            text("SELECT COUNT(*) FROM projects WHERE organization_id=:org_id AND status='completed'"), 
            {"org_id": org_id}
        ).scalar() or 0

        # Lead-time calculation (days from creation to approval)
        lt_result = db.session.execute(
            text("""
                SELECT AVG(EXTRACT(EPOCH FROM (approved_at - created_at))/86400) 
                FROM business_cases 
                WHERE organization_id=:org_id AND approved_at IS NOT NULL
            """), 
            {"org_id": org_id}
        ).scalar()
        lead_time_days = round(float(lt_result), 1) if lt_result is not None else None

        # ROI calculations - using actual benefit tracking
        projected_benefit = db.session.execute(
            text("SELECT COALESCE(SUM(projected_benefit), 0) FROM business_cases WHERE organization_id=:org_id"), 
            {"org_id": org_id}
        ).scalar() or 0
        
        realized_benefit = db.session.execute(
            text("SELECT COALESCE(SUM(actual_benefit), 0) FROM projects WHERE organization_id=:org_id"), 
            {"org_id": org_id}
        ).scalar() or 0

        # Stalled items (no update in 14 days)
        stalled = db.session.execute(
            text("""
                SELECT COUNT(*) FROM projects 
                WHERE organization_id=:org_id 
                AND updated_at < NOW() - INTERVAL '14 days' 
                AND status NOT IN ('completed', 'cancelled')
            """), 
            {"org_id": org_id}
        ).scalar() or 0

        # Department breakdown
        dept_breakdown = db.session.execute(
            text("""
                SELECT d.name, COUNT(p.id) as problem_count
                FROM departments d
                LEFT JOIN problems p ON d.id = p.department_id AND p.organization_id = :org_id
                WHERE d.organization_id = :org_id
                GROUP BY d.id, d.name
                ORDER BY problem_count DESC
                LIMIT 5
            """), 
            {"org_id": org_id}
        ).fetchall()

        # Recent activity
        recent_problems = db.session.execute(
            text("""
                SELECT COUNT(*) FROM problems 
                WHERE organization_id=:org_id 
                AND created_at >= NOW() - INTERVAL '30 days'
            """), 
            {"org_id": org_id}
        ).scalar() or 0

        recent_cases = db.session.execute(
            text("""
                SELECT COUNT(*) FROM business_cases 
                WHERE organization_id=:org_id 
                AND created_at >= NOW() - INTERVAL '30 days'
            """), 
            {"org_id": org_id}
        ).scalar() or 0

        data = {
            "funnel": {
                "problems": problems_total,
                "cases": cases_total,
                "approved_cases": approved_cases,
                "projects": projects_total,
                "done": projects_done
            },
            "lead_time_days": lead_time_days,
            "roi": {
                "projected": float(projected_benefit),
                "realized": float(realized_benefit)
            },
            "stalled": stalled,
            "department_breakdown": [{"name": row[0], "count": row[1]} for row in dept_breakdown],
            "recent_activity": {
                "problems_30d": recent_problems,
                "cases_30d": recent_cases
            },
            "generated_at": int(time.time())
        }
        
        return data
        
    except Exception as e:
        # Return minimal safe data on error
        return {
            "funnel": {"problems": 0, "cases": 0, "approved_cases": 0, "projects": 0, "done": 0},
            "lead_time_days": None,
            "roi": {"projected": 0.0, "realized": 0.0},
            "stalled": 0,
            "department_breakdown": [],
            "recent_activity": {"problems_30d": 0, "cases_30d": 0},
            "generated_at": int(time.time()),
            "error": str(e)
        }

def get_metrics(db, org_id: int) -> Dict[str, Any]:
    """Get metrics with caching"""
    k = _key(org_id)
    if k in cache:
        return cache[k]
    data = compute_metrics(db, org_id)
    cache[k] = data
    return data

def invalidate_metrics(org_id: int):
    """Invalidate cached metrics for an organization"""
    cache.pop(_key(org_id), None)

def get_cache_info():
    """Get cache statistics for monitoring"""
    return {
        "size": len(cache),
        "maxsize": cache.maxsize,
        "ttl": cache.ttl,
        "hits": getattr(cache, 'hits', 0),
        "misses": getattr(cache, 'misses', 0)
    }