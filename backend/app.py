from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from models import db, Category
import os

def create_app():
    app = Flask(__name__,
        static_folder="../frontend",
        static_url_path=""
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.sqlite"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = True

    db.init_app(app)
    CORS(app, supports_credentials=True, origins=[
        "https://securevault-incident-tracker-1.onrender.com",
        "https://securevault-app-six.vercel.app",
        "http://127.0.0.1:3000",
        "http://localhost:3000"
    ])

    from routes.auth import auth_bp
    from routes.incidents import incidents_bp
    from routes.stats import stats_bp
    from routes.threat_intel import threat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(incidents_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(threat_bp)

    @app.route("/")
    def index():
        return send_from_directory("../frontend", "index.html")

    @app.route("/login")
    def login_page():
        return send_from_directory("../frontend", "login.html")

    @app.route("/dashboard")
    def dashboard_page():
        return send_from_directory("../frontend", "dashboard.html")

    with app.app_context():
        db.create_all()
        from seed import seed_data
        seed_data()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
