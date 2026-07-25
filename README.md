# SecureVault — Personal Cybersecurity Incident Tracker
# SecureVault — Personal Cybersecurity Incident Tracker

## Project Description
SecureVault is a secure Flask REST API backend for tracking cybersecurity incidents.

## Installation
1. git clone https://github.com/dama-254/securevault-incident-tracker.git
2. cd securevault-incident-tracker
3. python3 -m venv venv
4. source venv/bin/activate
5. pip install -r requirements.txt
6. python3 seed.py
7. flask run

## Running Tests
pytest -v

## API Endpoints
- POST /register
- POST /login
- POST /logout
- GET /me
- GET /check_session
- GET /incidents
- POST /incidents
- GET /incidents/<id>
- PATCH /incidents/<id>
- DELETE /incidents/<id>
- GET /incidents/stats
- GET /categories

## Pagination
GET /incidents?page=1&per_page=10

## Default Users
- damaris / Admin1234
- bashir / Pass1234
- brian / Pass1234
- enock / Pass1234
- keiden / Pass1234

