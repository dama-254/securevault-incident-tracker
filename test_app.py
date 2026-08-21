import pytest
from app import create_app
from models import db


@pytest.fixture
def client():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key",
    })
    with app.app_context():
        db.drop_all()
        db.create_all()
        from models import Category
        for name in ["Phishing", "Malware", "DDoS", "Social Engineering", "Data Breach"]:
            db.session.add(Category(name=name))
        db.session.commit()

    with app.test_client() as client:
        yield client


def register_and_login(client, username="test_user", password="TestPass123"):
    client.post("/register", json={"username": username, "password": password})
    return client.post("/login", json={"username": username, "password": password})


# ─── AUTH TESTS ────────────────────────────────────────────────────────────────

def test_register_creates_user(client):
    res = client.post("/register", json={"username": "alice", "password": "Pass1234"})
    assert res.status_code == 201
    assert res.get_json()["username"] == "alice"


def test_register_duplicate_username_fails(client):
    client.post("/register", json={"username": "bob", "password": "Pass1234"})
    res = client.post("/register", json={"username": "bob", "password": "Other123"})
    assert res.status_code == 409


def test_login_with_correct_credentials(client):
    client.post("/register", json={"username": "carol", "password": "Pass1234"})
    res = client.post("/login", json={"username": "carol", "password": "Pass1234"})
    assert res.status_code == 200


def test_login_with_wrong_password_fails(client):
    client.post("/register", json={"username": "dave", "password": "Pass1234"})
    res = client.post("/login", json={"username": "dave", "password": "WrongPass"})
    assert res.status_code == 401


def test_logout(client):
    register_and_login(client)
    res = client.post("/logout")
    assert res.status_code == 200


def test_me_returns_current_user(client):
    register_and_login(client, username="meuser")
    res = client.get("/me")
    assert res.status_code == 200
    assert res.get_json()["username"] == "meuser"


def test_me_returns_401_when_not_logged_in(client):
    res = client.get("/me")
    assert res.status_code == 401


def test_check_session(client):
    register_and_login(client, username="sessionuser")
    res = client.get("/check_session")
    assert res.status_code == 200
    assert res.get_json()["username"] == "sessionuser"


def test_check_session_returns_401_when_not_logged_in(client):
    res = client.get("/check_session")
    assert res.status_code == 401


# ─── CATEGORIES TESTS ─────────────────────────────────────────────────────────

def test_categories_endpoint_returns_seeded_categories(client):
    res = client.get("/categories")
    names = [c["name"] for c in res.get_json()]
    assert "Phishing" in names
    assert len(names) == 5


# ─── INCIDENTS TESTS ──────────────────────────────────────────────────────────

def test_incidents_requires_login(client):
    res = client.get("/incidents")
    assert res.status_code == 401


def test_create_and_fetch_incident(client):
    register_and_login(client)
    res = client.post("/incidents", json={
        "title": "Test phishing email",
        "description": "A suspicious email was reported by an employee.",
        "severity": "High",
        "category_id": 1,
        "affected_systems": [{"system_name": "Laptop-01", "department": "IT"}],
    })
    assert res.status_code == 201
    incident_id = res.get_json()["id"]

    res = client.get(f"/incidents/{incident_id}")
    data = res.get_json()
    assert data["title"] == "Test phishing email"
    assert data["category"] == "Phishing"
    assert data["reported_by"] == "test_user"
    assert len(data["affected_systems"]) == 1


def test_get_all_incidents_with_pagination(client):
    register_and_login(client)
    for i in range(3):
        client.post("/incidents", json={
            "title": f"Incident {i}",
            "description": f"Description for incident {i}",
            "severity": "Low",
            "category_id": 1,
        })
    res = client.get("/incidents?page=1&per_page=2")
    assert res.status_code == 200
    data = res.get_json()
    assert "incidents" in data
    assert "total" in data
    assert "pages" in data
    assert "current_page" in data
    assert data["total"] == 3
    assert len(data["incidents"]) == 2
    assert data["pages"] == 2


def test_update_incident_status(client):
    register_and_login(client)
    res = client.post("/incidents", json={
        "title": "Malware alert",
        "description": "Malware detected on a workstation.",
        "severity": "Critical",
        "category_id": 2,
    })
    incident_id = res.get_json()["id"]

    res = client.patch(f"/incidents/{incident_id}", json={"status": "Resolved"})
    assert res.status_code == 200
    assert res.get_json()["status"] == "Resolved"


def test_delete_incident(client):
    register_and_login(client)
    res = client.post("/incidents", json={
        "title": "DDoS attempt",
        "description": "Traffic spike detected on staging server.",
        "severity": "Medium",
        "category_id": 3,
    })
    incident_id = res.get_json()["id"]

    res = client.delete(f"/incidents/{incident_id}")
    assert res.status_code == 200

    res = client.get(f"/incidents/{incident_id}")
    assert res.status_code == 404


def test_cannot_access_other_users_incident(client):
    register_and_login(client, username="user_one", password="Pass1234")
    res = client.post("/incidents", json={
        "title": "User One Incident",
        "description": "This belongs to user one only.",
        "severity": "Low",
        "category_id": 1,
    })
    incident_id = res.get_json()["id"]
    client.post("/logout")

    register_and_login(client, username="user_two", password="Pass1234")
    res = client.get(f"/incidents/{incident_id}")
    assert res.status_code == 403


def test_cannot_delete_other_users_incident(client):
    register_and_login(client, username="owner", password="Pass1234")
    res = client.post("/incidents", json={
        "title": "Owner Incident",
        "description": "Only the owner should delete this.",
        "severity": "Medium",
        "category_id": 2,
    })
    incident_id = res.get_json()["id"]
    client.post("/logout")

    register_and_login(client, username="intruder", password="Pass1234")
    res = client.delete(f"/incidents/{incident_id}")
    assert res.status_code == 403


# ─── STATS TESTS ──────────────────────────────────────────────────────────────

def test_stats_groups_by_category_severity_status(client):
    register_and_login(client)
    client.post("/incidents", json={
        "title": "Incident A", "description": "Details of incident A here.",
        "severity": "High", "category_id": 1,
    })
    client.post("/incidents", json={
        "title": "Incident B", "description": "Details of incident B here.",
        "severity": "High", "category_id": 1,
    })

    res = client.get("/incidents/stats")
    data = res.get_json()
    assert data["total_incidents"] == 2
    assert any(c["category"] == "Phishing" and c["count"] == 2 for c in data["by_category"])
    assert any(s["severity"] == "High" and s["count"] == 2 for s in data["by_severity"])


def test_register_missing_fields(client):
    res = client.post("/register", json={"username": "nopass"})
    assert res.status_code == 400


def test_create_incident_missing_fields(client):
    register_and_login(client)
    res = client.post("/incidents", json={"title": "Incomplete"})
    assert res.status_code == 400
