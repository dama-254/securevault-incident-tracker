# 🔐 SecureVault — Personal Cybersecurity Incident Tracker

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.1.3-green)
![SQLite](https://img.shields.io/badge/Database-SQLite-orange)
![Tests](https://img.shields.io/badge/Tests-20%20passing-brightgreen)

---

## 📌 Project Description

SecureVault is a full-stack web application that allows users to log, track, and analyze
personal cybersecurity incidents. Whether you are dealing with phishing emails, malware
attacks, suspicious logins, or data breaches — SecureVault gives you a centralized,
secure dashboard to manage it all.

The application is built with a Flask REST API backend, a SQLite database, and a clean
HTML/CSS/JavaScript frontend. Users must register and log in before they can access any
data. Each user can only see and manage their own incidents.

---

## 🎯 Key Features

- ✅ User registration and login with hashed passwords
- ✅ Session-based authentication (stays logged in on refresh)
- ✅ Full CRUD — Create, Read, Update, Delete incidents
- ✅ Incidents are private — users only see their own data
- ✅ Filter incidents by severity, status, and category
- ✅ Pagination on the incidents list (10 per page)
- ✅ Analytics page with charts (by category, severity, status)
- ✅ 20 automated tests covering all endpoints
- ✅ Seed file with sample data for all models

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask 3.1.3 |
| ORM | Flask-SQLAlchemy 3.1.1 |
| Database | SQLite |
| Authentication | Session-based (Werkzeug password hashing) |
| Frontend | HTML5, CSS3, Vanilla JavaScript (Fetch API) |
| Charts | Chart.js 4.4.0 |
| Testing | pytest 9.1.1 |
| Version Control | Git + GitHub |

---

## 📁 Project Structure

```
securevault-incident-tracker/
│
├── app.py                  # Flask application factory and page routes
├── models.py               # SQLAlchemy database models
├── seed.py                 # Seeds the database with sample data
├── test_app.py             # 20 automated pytest tests
├── requirements.txt        # Python dependencies
├── Pipfile                 # Pipenv dependencies
├── README.md               # This file
│
├── routes/
│   ├── __init__.py
│   ├── auth.py             # POST /register, POST /login, POST /logout, GET /me, GET /check_session
│   ├── incidents.py        # Full CRUD for incidents + pagination + GET /categories
│   └── stats.py            # GET /incidents/stats (analytics)
│
├── templates/
│   ├── index.html          # Landing page
│   ├── login.html          # Login and register page
│   ├── dashboard.html      # Main incidents dashboard with filters and pagination
│   ├── form.html           # Log new incident form
│   ├── detail.html         # Single incident detail page
│   └── analytics.html      # Charts and statistics page
│
└── static/
    ├── style.css           # All CSS styling
    └── app.js              # Shared JavaScript helpers and login logic
```

---

## 🗄 Database Models (ERD)

```
users
─────────────────────────────
id          INTEGER  PRIMARY KEY
username    TEXT     UNIQUE, NOT NULL
password_hash TEXT   NOT NULL
role        TEXT     DEFAULT 'user'
│
│ (one user → many incidents)
▼
incidents
─────────────────────────────
id              INTEGER  PRIMARY KEY
title           TEXT     NOT NULL
description     TEXT     NOT NULL
severity        TEXT     NOT NULL  (Low / Medium / High / Critical)
status          TEXT     DEFAULT 'Open'  (Open / In Progress / Resolved)
date_reported   DATETIME DEFAULT now
user_id         INTEGER  FOREIGN KEY → users.id
category_id     INTEGER  FOREIGN KEY → categories.id
│
│ (one incident → many affected systems)
▼
affected_systems
─────────────────────────────
id           INTEGER  PRIMARY KEY
incident_id  INTEGER  FOREIGN KEY → incidents.id
system_name  TEXT     NOT NULL
department   TEXT     NOT NULL

categories
─────────────────────────────
id    INTEGER  PRIMARY KEY
name  TEXT     UNIQUE, NOT NULL
```

---

## ⚙ Installation Instructions

### 1. Clone the repository
```bash
git clone https://github.com/dama-254/securevault-incident-tracker.git
cd securevault-incident-tracker
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

> On Windows use: `venv\Scripts\activate`

### 3. Install all dependencies
```bash
pip install -r requirements.txt
```

### 4. Seed the database with sample data
```bash
python3 seed.py
```

You should see:
```
Seeded successfully!
Users: 5, Categories: 6, Incidents: 8
```

### 5. Run the application
```bash
flask run
```

Or alternatively:
```bash
python3 app.py
```

The app will be running at: **http://localhost:5000**

---

## 🔑 Default Login Credentials (after seeding)

| Username | Password | Role |
|----------|----------|------|
| damaris | Admin1234 | admin |
| aj | Pass1234 | user |
| keiden | Pass1234 | user |
| brian | Pass1234 | user |
| enock | Pass1234 | user |

---

## 🧪 Running Tests

```bash
pytest -v
```

Expected output:
```
test_app.py::test_register_creates_user PASSED
test_app.py::test_register_duplicate_username_fails PASSED
test_app.py::test_login_with_correct_credentials PASSED
test_app.py::test_login_with_wrong_password_fails PASSED
test_app.py::test_logout PASSED
test_app.py::test_me_returns_current_user PASSED
test_app.py::test_me_returns_401_when_not_logged_in PASSED
test_app.py::test_check_session PASSED
test_app.py::test_check_session_returns_401_when_not_logged_in PASSED
test_app.py::test_categories_endpoint_returns_seeded_categories PASSED
test_app.py::test_incidents_requires_login PASSED
test_app.py::test_create_and_fetch_incident PASSED
test_app.py::test_get_all_incidents_with_pagination PASSED
test_app.py::test_update_incident_status PASSED
test_app.py::test_delete_incident PASSED
test_app.py::test_cannot_access_other_users_incident PASSED
test_app.py::test_cannot_delete_other_users_incident PASSED
test_app.py::test_stats_groups_by_category_severity_status PASSED
test_app.py::test_register_missing_fields PASSED
test_app.py::test_create_incident_missing_fields PASSED

20 passed
```

---

## 🌐 API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required | Success Code |
|--------|----------|-------------|---------------|-------------|
| POST | /register | Create a new user account | No | 201 |
| POST | /login | Log in and create a session | No | 200 |
| POST | /logout | Log out and destroy the session | No | 200 |
| GET | /me | Get the currently logged in user | Yes | 200 |
| GET | /check_session | Check if a session is active | Yes | 200 |

### Incidents

| Method | Endpoint | Description | Auth Required | Success Code |
|--------|----------|-------------|---------------|-------------|
| GET | /incidents | Get all your incidents (paginated) | Yes | 200 |
| POST | /incidents | Log a new incident | Yes | 201 |
| GET | /incidents/<id> | Get a single incident by ID | Yes | 200 |
| PATCH | /incidents/<id> | Update an incident | Yes | 200 |
| DELETE | /incidents/<id> | Delete an incident | Yes | 200 |
| GET | /incidents/stats | Get analytics data | Yes | 200 |

### Categories

| Method | Endpoint | Description | Auth Required | Success Code |
|--------|----------|-------------|---------------|-------------|
| GET | /categories | Get all incident categories | No | 200 |

---

## 📄 Request and Response Examples

### Register a new user
```
POST /register
Content-Type: application/json

{
  "username": "alice",
  "password": "SecurePass123"
}

Response 201:
{
  "id": 6,
  "username": "alice",
  "role": "user"
}
```

### Log in
```
POST /login
Content-Type: application/json

{
  "username": "alice",
  "password": "SecurePass123"
}

Response 200:
{
  "id": 6,
  "username": "alice",
  "role": "user"
}
```

### Create a new incident
```
POST /incidents
Content-Type: application/json

{
  "title": "Phishing Email Attempt",
  "description": "Received suspicious email asking for credentials.",
  "severity": "High",
  "category_id": 1,
  "affected_systems": [
    { "system_name": "Mail Server", "department": "IT" }
  ]
}

Response 201:
{
  "id": 1,
  "title": "Phishing Email Attempt",
  "severity": "High",
  "status": "Open",
  "category": "Phishing",
  "reported_by": "alice",
  "affected_systems": [
    { "id": 1, "system_name": "Mail Server", "department": "IT" }
  ]
}
```

### Get all incidents with pagination
```
GET /incidents?page=1&per_page=10&severity=High

Response 200:
{
  "incidents": [...],
  "page": 1,
  "per_page": 10,
  "total": 25,
  "pages": 3
}
```

### Get analytics stats
```
GET /incidents/stats

Response 200:
{
  "total_incidents": 8,
  "by_category": [
    { "category": "Phishing", "count": 3 },
    { "category": "Malware", "count": 2 }
  ],
  "by_severity": [
    { "severity": "Critical", "count": 3 },
    { "severity": "High", "count": 2 }
  ],
  "by_status": [
    { "status": "Open", "count": 4 },
    { "status": "Resolved", "count": 3 }
  ]
}
```

---

## 🔒 Security Features

- Passwords are hashed using Werkzeug's `generate_password_hash` — the original password is never stored
- Session-based authentication using Flask's signed cookie sessions
- Every protected route checks for a valid session before returning data
- Users can only view, update, or delete their own incidents (returns 403 if they try to access someone else's)
- Unauthorized requests return 401, forbidden requests return 403

---

## 📊 Frontend Pages

| URL | Page | Description |
|-----|------|-------------|
| / | Landing page | Welcome page with Get Started button |
| /login | Login/Register | Toggle between login and registration |
| /dashboard | Dashboard | All incidents with filters and pagination |
| /log-incident | Log Incident | Form to create a new incident |
| /incident/<id> | Incident Detail | Full view of one incident with advance/delete |
| /analytics | Analytics | Charts showing threat data by category, severity, status |

---

## 🌿 Git Branching Strategy

This project uses a structured branching model to keep everyone's work separate
and prevent conflicts. The main branch holds the final stable version of the
project and is never pushed to directly by team members.

```
main  (protected — final stable project, do not push here directly)
  │
  └── development  (integration branch — all team work gets reviewed here first)
        │
        ├── damaris   (Damaris's personal working branch)
        ├── person2   (AJ's personal working branch)
        ├── person3   (Keiden's personal working branch)
        ├── person4   (Brian's personal working branch)
        └── person5   (Enock's personal working branch)
```

### How it works

1. Each team member works only on their own personal branch
2. When their work is complete they push to their own branch
3. All personal branches are reviewed and merged into development
4. Only once development is tested and stable does it get pushed to main
5. Nobody pushes directly to main at any point

### Daily workflow for each team member

```bash
# Make sure you are on your own branch before starting
git checkout damaris        # use your own branch name

# Do your work, then save it
git add .
git commit -m "feat: describe what you did"
git push origin damaris     # push to YOUR branch only
```

### Branch ownership

| Branch | Owner | Files |
|--------|-------|-------|
| main | Protected — final project only | Full project |
| development | Integration branch — reviewed merges only | Full project |
| damaris | Damaris | models.py, app.py, seed.py |
| person2 (AJ) | AJ | routes/auth.py, templates/login.html |
| person3 (Keiden) | Keiden | routes/incidents.py, templates/form.html, templates/detail.html |
| person4 (Brian) | Brian | routes/stats.py, templates/analytics.html |
| person5 (Enock) | Enock | static/app.js, static/style.css, templates/dashboard.html |

### Commit message format

Always write commit messages in this format so the history stays clean:

```
feat: add login route
fix: patch status update bug
test: add pytest for DELETE route
docs: update README with ERD
style: clean up dashboard CSS
```

---

## 👥 Team Contributions

| Team Member | Branch | Files Owned |
|-------------|--------|-------------|
| Damaris | damaris | models.py, app.py, seed.py |
| AJ | person2 | routes/auth.py, templates/login.html |
| Keiden | person3 | routes/incidents.py, templates/form.html, templates/detail.html |
| Brian | person4 | routes/stats.py, templates/analytics.html |
| Enock | person5 | static/app.js, static/style.css, templates/dashboard.html |

---

## 🐛 Common Issues

**Port already in use:**
```bash
flask run --port 5001
```

**Database needs resetting:**
```bash
python3 seed.py
```

**Module not found errors:**
```bash
pip install -r requirements.txt
```

**Virtual environment not activated:**
```bash
source venv/bin/activate
```

**Accidentally on wrong branch:**
```bash
git branch          # check which branch you are on
git checkout damaris  # switch to your own branch
```

---

## 📜 License

This project was built as a Moringa School Full Stack Capstone Project.

---

*Built with 🔐 by the SecureVault Team — Moringa School 2026*
