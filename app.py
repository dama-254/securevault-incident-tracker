from flask import Flask, render_template
from flask_cors import CORS
from models import db, Category

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.sqlite"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"

    db.init_app(app)
    CORS(app, supports_credentials=True)

    from routes.auth import auth_bp
    from routes.incidents import incidents_bp
    from routes.stats import stats_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(incidents_bp)
    app.register_blueprint(stats_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/dashboard")
    def dashboard_page():
        return render_template("dashboard.html")

    with app.app_context():
        db.create_all()
        seed_categories()

    return app


def seed_categories():
    defaults = ["Phishing", "Malware", "DDoS", "Social Engineering", "Data Breach"]
    for name in defaults:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
