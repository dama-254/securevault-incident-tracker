import os
import requests
from flask import Blueprint, request, jsonify, session
from functools import wraps
from models import db, Incident

threat_bp = Blueprint("threat", __name__)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "authentication required"}), 401
        return f(*args, **kwargs)
    return wrapper


# ── 1. CHECK IP ADDRESS WITH ABUSEIPDB ──────────────────────────────
@threat_bp.route("/check-ip", methods=["POST"])
@login_required
def check_ip():
    data = request.get_json()
    ip = data.get("ip_address")

    if not ip:
        return jsonify({"error": "ip_address is required"}), 400

    api_key = os.getenv("ABUSEIPDB_KEY")
    if not api_key:
        return jsonify({"error": "AbuseIPDB API key not configured"}), 500

    response = requests.get(
        "https://api.abuseipdb.com/api/v2/check",
        headers={"Key": api_key, "Accept": "application/json"},
        params={"ipAddress": ip, "maxAgeInDays": 90}
    )

    if response.status_code != 200:
        return jsonify({"error": "Failed to check IP"}), 500

    result = response.json()["data"]

    return jsonify({
        "ip": ip,
        "abuse_score": result["abuseConfidenceScore"],
        "total_reports": result["totalReports"],
        "country": result["countryCode"],
        "isp": result["isp"],
        "last_reported": result["lastReportedAt"],
        "is_dangerous": result["abuseConfidenceScore"] > 50
    }), 200


# ── 2. CHECK URL WITH VIRUSTOTAL ────────────────────────────────────
@threat_bp.route("/check-url", methods=["POST"])
@login_required
def check_url():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "url is required"}), 400

    api_key = os.getenv("VIRUSTOTAL_KEY")
    if not api_key:
        return jsonify({"error": "VirusTotal API key not configured"}), 500

    # Step 1 — Submit URL for scanning
    scan_response = requests.post(
        "https://www.virustotal.com/api/v3/urls",
        headers={"x-apikey": api_key},
        data={"url": url}
    )

    if scan_response.status_code != 200:
        return jsonify({"error": "Failed to scan URL"}), 500

    scan_id = scan_response.json()["data"]["id"]

    # Step 2 — Get the scan results
    result_response = requests.get(
        f"https://www.virustotal.com/api/v3/analyses/{scan_id}",
        headers={"x-apikey": api_key}
    )

    if result_response.status_code != 200:
        return jsonify({"error": "Failed to get scan results"}), 500

    stats = result_response.json()["data"]["attributes"]["stats"]

    return jsonify({
        "url": url,
        "malicious": stats.get("malicious", 0),
        "suspicious": stats.get("suspicious", 0),
        "harmless": stats.get("harmless", 0),
        "undetected": stats.get("undetected", 0),
        "is_dangerous": stats.get("malicious", 0) > 3
    }), 200


# ── 3. SEND SLACK ALERT ─────────────────────────────────────────────
@threat_bp.route("/alert-slack", methods=["POST"])
@login_required
def alert_slack():
    data = request.get_json()
    incident_id = data.get("incident_id")

    if not incident_id:
        return jsonify({"error": "incident_id is required"}), 400

    webhook_url = os.getenv("SLACK_WEBHOOK")
    if not webhook_url:
        return jsonify({"error": "Slack webhook not configured"}), 500

    incident = Incident.query.get_or_404(incident_id)

    message = {
        "text": (
            f"🚨 *SECUREVAULT ALERT*\n"
            f"*Incident:* {incident.title}\n"
            f"*Severity:* {incident.severity}\n"
            f"*Status:* {incident.status}\n"
            f"*Description:* {incident.description[:200]}\n"
            f"*Reported by:* {incident.reported_by.username}"
        )
    }

    response = requests.post(webhook_url, json=message)

    if response.status_code != 200:
        return jsonify({"error": "Failed to send Slack alert"}), 500

    return jsonify({"message": "Slack alert sent successfully"}), 200
