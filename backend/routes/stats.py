from flask import Blueprint, jsonify
from sqlalchemy import func
from models import db, Incident, Category

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/incidents/stats", methods=["GET"])
def get_stats():
    by_category = (
        db.session.query(Category.name, func.count(Incident.id))
        .join(Incident, Incident.category_id == Category.id)
        .group_by(Category.name)
        .all()
    )
    by_severity = (
        db.session.query(Incident.severity, func.count(Incident.id))
        .group_by(Incident.severity)
        .all()
    )
    by_status = (
        db.session.query(Incident.status, func.count(Incident.id))
        .group_by(Incident.status)
        .all()
    )
    total = Incident.query.count()

    return jsonify({
        "total_incidents": total,
        "by_category": [{"category": c, "count": n} for c, n in by_category],
        "by_severity": [{"severity": s, "count": n} for s, n in by_severity],
        "by_status": [{"status": s, "count": n} for s, n in by_status],
    }), 200
