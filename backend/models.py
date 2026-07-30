from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")

    incidents = db.relationship("Incident", backref="reported_by", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
        }


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    incidents = db.relationship("Incident", backref="category", lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Incident(db.Model):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="Open")
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    affected_systems = db.relationship(
        "AffectedSystem", backref="incident", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "date_reported": self.date_reported.isoformat(),
            "user_id": self.user_id,
            "reported_by": self.reported_by.username if self.reported_by else None,
            "category_id": self.category_id,
            "category": self.category.name if self.category else None,
            "affected_systems": [s.to_dict() for s in self.affected_systems],
        }


class AffectedSystem(db.Model):
    __tablename__ = "affected_systems"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False)
    system_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "system_name": self.system_name,
            "department": self.department,
        }
