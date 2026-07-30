from functools import wraps

from flask import Blueprint, jsonify, request, session

from models import AffectedSystem, Category, Incident, db

incidents_bp = Blueprint("incidents", __name__)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "authentication required"}), 401
        return f(*args, **kwargs)

    return wrapper


@incidents_bp.route("/categories", methods=["GET"])
def get_categories():
    categories = Category.query.order_by(Category.name).all()
    return jsonify([c.to_dict() for c in categories]), 200


@incidents_bp.route("/incidents", methods=["GET"])
@login_required
def get_incidents():
    user_id = session.get("user_id")
    severity = request.args.get("severity")
    status = request.args.get("status")
    category_id = request.args.get("category_id")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    query = Incident.query.filter_by(user_id=user_id)
    if severity:
        query = query.filter_by(severity=severity)
    if status:
        query = query.filter_by(status=status)
    if category_id:
        query = query.filter_by(category_id=category_id)

    query = query.order_by(Incident.date_reported.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        {
            "incidents": [i.to_dict() for i in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
    ), 200


@incidents_bp.route("/incidents/<int:incident_id>", methods=["GET"])
@login_required
def get_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    if incident.user_id != session.get("user_id"):
        return jsonify({"error": "unauthorized"}), 403
    return jsonify(incident.to_dict()), 200


@incidents_bp.route("/incidents", methods=["POST"])
@login_required
def create_incident():
    data = request.get_json(silent=True) or {}
    required = ["title", "description", "severity", "category_id"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"missing fields: {missing}"}), 400

    incident = Incident(
        title=data["title"],
        description=data["description"],
        severity=data["severity"],
        status=data.get("status", "Open"),
        user_id=session["user_id"],
        category_id=data["category_id"],
    )
    db.session.add(incident)
    db.session.flush()

    for sys_data in data.get("affected_systems", []):
        db.session.add(
            AffectedSystem(
                incident_id=incident.id,
                system_name=sys_data.get("system_name", ""),
                department=sys_data.get("department", ""),
            )
        )

    db.session.commit()
    return jsonify(incident.to_dict()), 201


@incidents_bp.route("/incidents/<int:incident_id>", methods=["PATCH"])
@login_required
def update_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    if incident.user_id != session.get("user_id"):
        return jsonify({"error": "unauthorized"}), 403
    data = request.get_json(silent=True) or {}
    for field in ["title", "description", "severity", "status", "category_id"]:
        if field in data:
            setattr(incident, field, data[field])
    db.session.commit()
    return jsonify(incident.to_dict()), 200


@incidents_bp.route("/incidents/<int:incident_id>", methods=["DELETE"])
@login_required
def delete_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    if incident.user_id != session.get("user_id"):
        return jsonify({"error": "unauthorized"}), 403
    db.session.delete(incident)
    db.session.commit()
    return jsonify({"message": "incident deleted"}), 200
