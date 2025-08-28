from flask import Blueprint, jsonify, render_template, Response, request
from flask_login import login_required, current_user
import io
import csv
import time
from collections import defaultdict
from typing import Any, Dict
from cachetools import TTLCache
from sqlalchemy import text
from app import db

# Create blueprints
metrics_bp = Blueprint("metrics", __name__, url_prefix="/api/metrics")
exec_dash_bp = Blueprint("exec_dash", __name__, url_prefix="/dashboard")

# TTL cache for computed metrics (5 minutes)
cache = TTLCache(maxsize=256, ttl=300)

def _key(org_id: int) -> str:
    return f"metrics:org:{org_id}"

def require_executive_access():
    """Decorator for executive-level access"""
    if not current_user.is_authenticated:
        return jsonify({"error": "Authentication required"}), 401
    
    if current_user.role not in ['admin', 'ceo', 'director']:
        return jsonify({"error": "Executive access required"}), 403
    
    return None

def compute_metrics(db, org_id: int) -> Dict[str, Any]:
    """Compute all executive metrics for an organization."""
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

# API Routes
@metrics_bp.route("/portfolio", methods=["GET"])
@login_required
def portfolio_metrics():
    """Get portfolio funnel and performance metrics"""
    access_check = require_executive_access()
    if access_check:
        return access_check
    
    org_id = current_user.organization_id
    data = get_metrics(db, org_id)
    
    return jsonify({
        "funnel": data["funnel"],
        "lead_time_days": data["lead_time_days"],
        "stalled": data["stalled"],
        "recent_activity": data["recent_activity"],
        "generated_at": data["generated_at"],
    }), 200

@metrics_bp.route("/roi", methods=["GET"])
@login_required
def roi_metrics():
    """Get ROI and financial metrics"""
    access_check = require_executive_access()
    if access_check:
        return access_check
    
    org_id = current_user.organization_id
    data = get_metrics(db, org_id)
    
    roi_data = data["roi"].copy()
    if roi_data["projected"] > 0:
        roi_data["realization_rate"] = round((roi_data["realized"] / roi_data["projected"]) * 100, 1)
    else:
        roi_data["realization_rate"] = 0
    
    return jsonify(roi_data), 200

@metrics_bp.route("/summary", methods=["GET"])
@login_required
def weekly_summary():
    """Generate AI-powered weekly executive summary"""
    access_check = require_executive_access()
    if access_check:
        return access_check
    
    org_id = current_user.organization_id
    data = get_metrics(db, org_id)
    
    # Generate summary based on metrics
    funnel = data["funnel"]
    roi = data["roi"]
    
    # Calculate conversion rates
    problem_to_case_rate = (funnel["cases"] / funnel["problems"] * 100) if funnel["problems"] > 0 else 0
    approval_rate = (funnel["approved_cases"] / funnel["cases"] * 100) if funnel["cases"] > 0 else 0
    completion_rate = (funnel["done"] / funnel["projects"] * 100) if funnel["projects"] > 0 else 0
    
    # Generate executive summary
    summary = f"""EXECUTIVE WEEKLY SUMMARY - ORGANIZATION {org_id}

PORTFOLIO OVERVIEW:
• {funnel['problems']} total problems in pipeline
• {funnel['cases']} business cases developed ({problem_to_case_rate:.1f}% conversion)
• {funnel['approved_cases']} cases approved ({approval_rate:.1f}% approval rate)
• {funnel['projects']} active projects with {funnel['done']} completed ({completion_rate:.1f}% completion)

PERFORMANCE METRICS:
• Average lead time: {data['lead_time_days'] or 'N/A'} days from case creation to approval
• {data['stalled']} items stalled (no updates >14 days)
• Recent activity: {data['recent_activity']['problems_30d']} new problems, {data['recent_activity']['cases_30d']} new cases (30 days)

FINANCIAL IMPACT:
• Projected benefits: £{roi['projected']:,.0f}
• Realized benefits: £{roi['realized']:,.0f}
• Realization rate: {(roi['realized']/roi['projected']*100) if roi['projected'] > 0 else 0:.1f}%

TOP DEPARTMENTS BY ACTIVITY:
{chr(10).join([f"• {dept['name']}: {dept['count']} problems" for dept in data['department_breakdown'][:3]])}

RECOMMENDATIONS:
{"• Focus on stalled items to improve throughput" if data['stalled'] > 5 else "• Portfolio flowing well"}
{"• Review approval process efficiency" if approval_rate < 50 else "• Strong approval pipeline"}
{"• Investigate project completion bottlenecks" if completion_rate < 70 else "• Good project execution"}

Generated: {data['generated_at']}"""

    return jsonify({
        "summary": summary,
        "metrics_snapshot": {
            "problem_to_case_rate": round(problem_to_case_rate, 1),
            "approval_rate": round(approval_rate, 1),
            "completion_rate": round(completion_rate, 1)
        },
        "generated_at": data["generated_at"]
    }), 200

# Dashboard Routes
@exec_dash_bp.route("/executive", methods=["GET"])
@login_required
def executive_dashboard():
    """Executive dashboard with role-based access control"""
    
    # Check role access
    if current_user.role not in ['admin', 'ceo', 'director']:
        from flask import abort
        abort(403, "Executive access required")
    
    org_id = current_user.organization_id
    
    return render_template(
        "dashboards/executive_dashboard.html", 
        org_id=org_id,
        user_role=current_user.role,
        organization_name=getattr(current_user.organization, 'name', f'Organization {org_id}')
    )