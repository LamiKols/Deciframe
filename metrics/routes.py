from flask import jsonify, request, Response
from flask_login import login_required, current_user
from . import metrics_bp
from .service import get_metrics, invalidate_metrics, get_cache_info
from app.flags import is_enabled
from app import db
import csv
import io

def require_executive_access():
    """Decorator for executive-level access"""
    if not current_user.is_authenticated:
        return jsonify({"error": "Authentication required"}), 401
    
    if current_user.role not in ['admin', 'ceo', 'director']:
        return jsonify({"error": "Executive access required"}), 403
    
    return None

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

@metrics_bp.route("/departments", methods=["GET"])
@login_required
def department_metrics():
    """Get department breakdown metrics"""
    access_check = require_executive_access()
    if access_check:
        return access_check
    
    org_id = current_user.organization_id
    data = get_metrics(db, org_id)
    
    return jsonify({
        "breakdown": data["department_breakdown"],
        "generated_at": data["generated_at"]
    }), 200

@metrics_bp.route("/csv", methods=["GET"])
@login_required
def export_csv():
    """Export executive metrics as CSV for board packs"""
    access_check = require_executive_access()
    if access_check:
        return access_check
    
    org_id = current_user.organization_id
    data = get_metrics(db, org_id)
    
    # Create CSV in memory
    buf = io.StringIO()
    writer = csv.writer(buf)
    
    # Headers
    writer.writerow(["Category", "Metric", "Value", "Generated At"])
    
    # Funnel metrics
    funnel = data["funnel"]
    writer.writerow(["Funnel", "Problems", funnel["problems"], data["generated_at"]])
    writer.writerow(["Funnel", "Business Cases", funnel["cases"], data["generated_at"]])
    writer.writerow(["Funnel", "Approved Cases", funnel["approved_cases"], data["generated_at"]])
    writer.writerow(["Funnel", "Projects", funnel["projects"], data["generated_at"]])
    writer.writerow(["Funnel", "Completed Projects", funnel["done"], data["generated_at"]])
    
    # Performance metrics
    writer.writerow(["Performance", "Lead Time (days)", data["lead_time_days"] or "N/A", data["generated_at"]])
    writer.writerow(["Performance", "Stalled Items", data["stalled"], data["generated_at"]])
    
    # ROI metrics
    roi = data["roi"]
    writer.writerow(["Financial", "Projected Benefit", f"£{roi['projected']:,.2f}", data["generated_at"]])
    writer.writerow(["Financial", "Realized Benefit", f"£{roi['realized']:,.2f}", data["generated_at"]])
    
    # Recent activity
    recent = data["recent_activity"]
    writer.writerow(["Activity", "Problems (30d)", recent["problems_30d"], data["generated_at"]])
    writer.writerow(["Activity", "Cases (30d)", recent["cases_30d"], data["generated_at"]])
    
    # Department breakdown
    for dept in data["department_breakdown"]:
        writer.writerow(["Departments", f"{dept['name']} Problems", dept["count"], data["generated_at"]])
    
    output = buf.getvalue()
    
    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=executive_metrics_org_{org_id}.csv"
        }
    )

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

@metrics_bp.route("/cache/info", methods=["GET"])
@login_required
def cache_info():
    """Get cache statistics for monitoring"""
    access_check = require_executive_access()
    if access_check:
        return access_check
    
    return jsonify(get_cache_info()), 200

@metrics_bp.route("/cache/invalidate", methods=["POST"])
@login_required
def invalidate_cache():
    """Invalidate metrics cache for current organization"""
    access_check = require_executive_access()
    if access_check:
        return access_check
    
    org_id = current_user.organization_id
    invalidate_metrics(org_id)
    
    return jsonify({"message": f"Cache invalidated for organization {org_id}"}), 200