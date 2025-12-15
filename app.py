# app.py — SitePulse Professional Audit Platform (Production Ready)

import os
import json
import time
import random
from datetime import datetime
from dotenv import load_dotenv

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, make_response
)
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import (
    LoginManager, UserMixin, login_user,
    current_user, logout_user, login_required
)
from flask_mail import Mail
from weasyprint import HTML, CSS
from redis import Redis
from rq import Queue
from sqlalchemy.exc import OperationalError

# -------------------------------------------------
# ENV & EXTENSIONS
# -------------------------------------------------
load_dotenv()

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()

# -------------------------------------------------
# DATABASE SAFE INIT (NON-BLOCKING)
# -------------------------------------------------
def initialize_db_with_retries(retries=5, delay=4):
    for attempt in range(retries):
        try:
            db.session.execute(db.text("SELECT 1"))
            db.create_all()
            print("✅ Database ready")
            return
        except OperationalError as e:
            print(f"DB attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    print("❌ Database initialization failed")

# -------------------------------------------------
# APP FACTORY
# -------------------------------------------------
def create_app():
    app = Flask(__name__)

    # ---------------- CONFIG ----------------
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "sitepulse-secret"),
        SQLALCHEMY_DATABASE_URI=db_url or "sqlite:///site.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_USE_TLS=os.getenv("MAIL_USE_TLS", "true").lower() == "true",
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER"),
    )

    # ---------------- INIT EXTENSIONS ----------------
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = "login"

    # ---------------- REDIS (OPTIONAL) ----------------
    try:
        redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        redis_conn.ping()
        task_queue = Queue(connection=redis_conn)
        print("✅ Redis enabled")
    except Exception:
        task_queue = None
        print("⚠ Redis disabled")

    # -------------------------------------------------
    # MODELS
    # -------------------------------------------------
    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password = db.Column(db.String(128), nullable=False)
        is_admin = db.Column(db.Boolean, default=False)
        reports = db.relationship("AuditReport", backref="owner", lazy=True)

    class AuditReport(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        website_url = db.Column(db.String(255), nullable=False)
        date_audited = db.Column(db.DateTime, default=datetime.utcnow)
        metrics_json = db.Column(db.Text, nullable=False)
        performance_score = db.Column(db.Integer, default=0)
        security_score = db.Column(db.Integer, default=0)
        accessibility_score = db.Column(db.Integer, default=0)
        user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # -------------------------------------------------
    # AUDIT DEFINITIONS (PROFESSIONAL)
    # -------------------------------------------------
    AUDIT_CATEGORIES = {
        "Technical SEO Audit": {
            "items": [
                "Robots.txt & sitemap",
                "Indexability & canonicals",
                "Internal linking structure",
                "Redirect chains",
                "URL architecture",
            ]
        },
        "Performance & Core Web Vitals": {
            "items": [
                "Largest Contentful Paint (LCP)",
                "Interaction to Next Paint (INP)",
                "Cumulative Layout Shift (CLS)",
                "Time to First Byte (TTFB)",
                "Mobile performance",
            ]
        },
        "On-Page SEO Audit": {
            "items": [
                "Meta titles & descriptions",
                "Content quality",
                "Duplicate content",
                "Structured data",
                "Readability",
            ]
        },
        "UX Audit": {
            "items": [
                "Navigation clarity",
                "Mobile usability",
                "Visual hierarchy",
                "Conversion flow",
            ]
        },
        "Security Audit": {
            "items": [
                "HTTPS / SSL",
                "Mixed content",
                "Malware risks",
                "Firewall & updates",
            ]
        },
        "Accessibility Audit": {
            "items": [
                "WCAG contrast ratios",
                "ALT text",
                "Keyboard navigation",
                "ARIA roles",
            ]
        },
        "Content Audit": {
            "items": [
                "Content freshness",
                "Engagement signals",
                "Topical relevance",
            ]
        },
        "Backlink & Authority Audit": {
            "items": [
                "Backlink quality",
                "Toxic links",
                "Brand mentions",
            ]
        },
        "Analytics & Tracking": {
            "items": [
                "GA4 installation",
                "Event tracking",
                "Tag Manager setup",
            ]
        },
        "E-Commerce Audit": {
            "items": [
                "Product SEO",
                "Checkout flow",
                "Payment reliability",
            ]
        },
    }

    # -------------------------------------------------
    # AUDIT ENGINE (SIMULATION / PLACEHOLDER)
    # -------------------------------------------------
    class AuditService:
        @staticmethod
        def run(url):
            metrics = {}
            for cat in AUDIT_CATEGORIES.values():
                for item in cat["items"]:
                    metrics[item] = random.choice(
                        ["Excellent", "Good", "Fair", "Poor"]
                    )
            return metrics

        @staticmethod
        def score(metrics):
            positive = sum(1 for v in metrics.values() if v in ("Excellent", "Good"))
            total = len(metrics)
            score = round((positive / total) * 100) if total else 0
            return score

    # -------------------------------------------------
    # ROUTES
    # -------------------------------------------------
    @app.route("/")
    def health():
        return "OK", 200

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            user = User.query.filter_by(email=request.form["email"]).first()
            if user and bcrypt.check_password_hash(user.password, request.form["password"]):
                login_user(user)
                return redirect(url_for("dashboard"))
            flash("Invalid credentials", "danger")
        return render_template("login.html")

    @app.route("/dashboard")
    @login_required
    def dashboard():
        reports = AuditReport.query.filter_by(
            user_id=current_user.id
        ).order_by(AuditReport.date_audited.desc()).all()
        return render_template("dashboard.html", reports=reports)

    @app.route("/run_audit", methods=["POST"])
    @login_required
    def run_audit():
        url = request.form.get("website_url")
        if not url.startswith(("http://", "https://")):
            flash("Invalid URL", "danger")
            return redirect(url_for("dashboard"))

        metrics = AuditService.run(url)
        score = AuditService.score(metrics)

        report = AuditReport(
            website_url=url,
            metrics_json=json.dumps(metrics),
            performance_score=score,
            security_score=score,
            accessibility_score=score,
            user_id=current_user.id,
        )
        db.session.add(report)
        db.session.commit()

        return redirect(url_for("view_report", report_id=report.id))

    @app.route("/report/<int:report_id>")
    @login_required
    def view_report(report_id):
        report = AuditReport.query.get_or_404(report_id)
        data = json.loads(report.metrics_json)
        return render_template("report_detail.html", report=report, data=data)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    # -------------------------------------------------
    # LAZY DB INIT (SAFE FOR CLOUD)
    # -------------------------------------------------
    @app.before_first_request
    def setup():
        initialize_db_with_retries()
        if not User.query.filter_by(email="roy.jamshaid@gmail.com").first():
            admin = User(
                email="roy.jamshaid@gmail.com",
                password=bcrypt.generate_password_hash("Jamshaid,1981").decode(),
                is_admin=True,
            )
            db.session.add(admin)
            db.session.commit()

    return app


# -------------------------------------------------
# GUNICORN ENTRYPOINT
# -------------------------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
