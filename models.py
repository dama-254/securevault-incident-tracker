from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class Query:
    def __init__(self, model_cls):
        self.model_cls = model_cls
        self._filters: List[Dict[str, Any]] = []
        self._order_by: Optional[Any] = None

    def filter_by(self, **kwargs):
        self._filters.append(kwargs)
        return self

    def order_by(self, *args):
        self._order_by = args
        return self

    def all(self):
        items = [obj for obj in self.model_cls.records if self._matches(obj)]
        if self._order_by:
            items = sorted(items, key=lambda obj: self._sort_value(obj))
        return items

    def paginate(self, page=1, per_page=10, error_out=False):
        items = self.all()
        start = (page - 1) * per_page
        end = start + per_page
        return Pagination(items[start:end], page, per_page, len(items))

    def get_or_404(self, item_id):
        for obj in self.model_cls.records:
            if getattr(obj, "id", None) == item_id:
                return obj
        raise LookupError(f"{self.model_cls.__name__} {item_id} not found")

    def _matches(self, obj):
        return all(getattr(obj, key, None) == value for key, value in self._filters[-1].items()) if self._filters else True

    def _sort_value(self, obj):
        for field in self._order_by:
            if field.__name__ == "date_reported":
                return getattr(obj, "date_reported", datetime.now(timezone.utc))
        return getattr(obj, self._order_by[0].__name__, None)


class Pagination:
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = max(1, (total + per_page - 1) // per_page) if total else 0


class QueryManager:
    def __get__(self, instance, owner):
        return Query(owner)


class BaseModel:
    records: List["BaseModel"] = []
    query = QueryManager()

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        return {key: value for key, value in self.__dict__.items() if not key.startswith("_")}


class _Session:
    def add(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = self._next_id(obj.__class__)
        if obj not in obj.__class__.records:
            obj.__class__.records.append(obj)

    def delete(self, obj):
        if obj in obj.__class__.records:
            obj.__class__.records.remove(obj)

    def flush(self):
        return None

    def commit(self):
        return None

    def _next_id(self, cls):
        existing = [getattr(item, "id", 0) for item in cls.records]
        return max(existing, default=0) + 1


class DB:
    def __init__(self):
        self.session = _Session()


db = DB()


class Category(BaseModel):
    records: List[BaseModel] = []

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)


class AffectedSystem(BaseModel):
    records: List[BaseModel] = []

    def __init__(self, incident_id: int, system_name: str, department: str, **kwargs):
        super().__init__(incident_id=incident_id, system_name=system_name, department=department, **kwargs)


class Incident(BaseModel):
    records: List[BaseModel] = []

    def __init__(self, title: str, description: str, severity: str, status: str, user_id: int, category_id: int, **kwargs):
        super().__init__(
            title=title,
            description=description,
            severity=severity,
            status=status,
            user_id=user_id,
            category_id=category_id,
            date_reported=kwargs.get("date_reported", datetime.now(timezone.utc)),
            affected_systems=kwargs.get("affected_systems", []),
            **kwargs,
        )

    def to_dict(self):
        category = Category.query.get_or_404(self.category_id) if self.category_id is not None else None
        affected_systems = [sys.to_dict() for sys in AffectedSystem.records if getattr(sys, "incident_id", None) == self.id]
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "category": category.name if category else None,
            "reported_by": f"User {self.user_id}",
            "date_reported": self.date_reported.isoformat() if hasattr(self.date_reported, "isoformat") else self.date_reported,
            "affected_systems": affected_systems,
        }
