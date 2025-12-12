
# app.py - FINAL ROBUST VERSION (With All Safety Checks)
import os
import json
import time
import random
import sys
from datetime import datetime
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_mail import Mail
from weasyprint import HTML, CSS
from redis import Redis
from rq import Queue
from sqlalchemy.exc import OperationalError 

load_dotenv()

# CRITICAL FIX 1: Safely initialize database with retries on startup
def initialize_db_with_retries(app, db, retries=5, delay=5):
    with app.app_context():
        for i in range(retries):
            try:
                # Test connection and create tables
                db.session.execute(db.text('SELECT 1')) 
                db.create_all()
                print("Database initialized successfully.")
                return True
            except OperationalError as e:
                print(f"Database connection attempt {i+1} failed: {e}")
                if i < retries - 1:
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print("Failed to initialize database after multiple retries. This is a fatal error.")
                    return False
            except Exception as e:
                print(f"Fatal error during DB initialization: {e}")
                return False
        return False

def create_app():
    app = Flask(__name__)

    # === CONFIG ===
    DB_URL = os.getenv("DATABASE_URL")
    if DB_URL and DB_URL.startswith("postgres://"):
        DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

    app.config.update({
        'SQLALCHEMY_DATABASE_URI': DB_URL or 'sqlite:///site.db',
        'SECRET_KEY': os.getenv('SECRET_KEY', 'super-secret-key-2025'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })
    
    # Email Configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    # Safe PORT handling
    try:
        port_val = os.getenv('MAIL_PORT')
        app.config['MAIL_PORT'] = int(port_val) if port_val else 587
    except ValueError:
        app.config['MAIL_PORT'] = 587
    
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')


    db = SQLAlchemy(app)
    bcrypt = Bcrypt(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    mail = Mail(app)

    # Redis/RQ Setup
    try:
        redis_conn = Redis.from_url(os.getenv('REDIS_URL') or 'redis://localhost:6379')
        redis_conn.ping()
        task_queue = Queue(connection=redis_conn)
        print("Redis Queue initialized successfully.")
    except Exception as e:
        print(f"Warning: Could not connect to Redis/initialize Queue: {e}")
        task_queue = None
    
    send_report_email = None
    run_scheduled_report = None


    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # === MODELS ===
    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password = db.Column(db.String(60), nullable=False)
        is_admin = db.Column(db.Boolean, default=False)
        reports = db.relationship('AuditReport', backref='owner', lazy=True)

    class AuditReport(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        website_url = db.Column(db.String(255), nullable=False)
        date_audited = db.Column(db.DateTime, default=datetime.utcnow)
        metrics_json = db.Column(db.Text, nullable=False)
        performance_score = db.Column(db.Integer, default=0)
        security_score = db.Column(db.Integer, default=0)
        accessibility_score = db.Column(db.Integer, default=0)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # === AUDIT CATEGORIES ===
    AUDIT_CATEGORIES = {
        "Technical SEO Audit": {"desc": "A technical assessment...", "items": ["Crawlability (robots.txt, sitemap, crawl errors)", "Indexability (noindex tags, canonicals, duplicate pages)", "Internal linking (broken links, orphan pages, link depth)", "Redirects (301/302, redirect loops, chains)", "URL structure and site architecture"]},
        "Performance & Core Web Vitals": {"desc": "Evaluates how fast...", "items": ["Core Web Vitals (LCP, INP/FID, CLS)", "Page speed & load time", "Server performance (TTFB)", "Image optimization (compression, WebP)", "CSS/JS optimization", "CDN, caching, lazy loading", "Mobile performance"]},
        "On-Page SEO Audit": {"desc": "Focuses on individual page...", "items": ["Meta tags", "Content quality", "Duplicate/thin content", "Image SEO", "Structured data", "Readability"]},
        "User Experience (UX) Audit": {"desc": "Analyzes how real users...", "items": ["Navigation usability", "Mobile experience", "Readability", "Conversion optimization", "Visual consistency"]},
        "Website Security Audit": {"desc": "Ensures your website is safe...", "items": ["HTTPS & SSL", "Mixed content", "Malware checks", "Plugin updates", "Firewall", "Backups"]},
        "Accessibility Audit (WCAG Standards)": {"desc": "Ensures people with disabilities...", "items": ["Color contrast", "ALT text", "Keyboard nav", "Screen reader", "ARIA labels", "Semantic HTML"]},
        "Content Audit": {"desc": "Reviews the entire content...", "items": ["Uniqueness", "Relevance", "Outdated content", "Engagement metrics", "Content gaps"]},
        "Off-Page SEO & Backlinks": {"desc": "Analyzes your site’s reputation...", "items": ["Backlink profile quality", "Toxic/spam link detection", "Local SEO signals", "NAP consistency", "Brand mentions"]},
        "Analytics & Tracking Audit": {"desc": "Checks if your website has accurate...", "items": ["Google Analytics / GA4 setup", "Goals, events, and conversions", "Heatmap & behavior tools", "Tag Manager correctness", "No duplicate tracking codes"]},
        "E-Commerce Audit (If applicable)": {"desc": "For online stores...", "items": ["Product page optimization", "Checkout flow usability", "Cart abandonment issues", "Payment gateway reliability", "Inventory & pricing visibility"]}
    }

    class AuditService:
        @staticmethod
        def run_audit(url):
            time.sleep(2)
            metrics = {}
            for cat, info in AUDIT_CATEGORIES.items():
                for item in info["items"]:
                    if any(k in item.lower() for k in ["lcp", "inp", "cls", "ttfb", "speed"]):
                        metrics[item] = f"{random.uniform(0.8, 4.5):.2f}s"
                    else:
                        metrics[item] = random.choices(["Excellent", "Good", "Fair", "Poor"], weights=[40, 30, 20, 10], k=1)[0]
            return {"metrics": metrics, "categories": AUDIT_CATEGORIES}

        @staticmethod
        def calculate_score(metrics):
            scores = {"performance": 0, "security": 0, "accessibility": 0, "tech_seo": 0, "ux": 0} 
            total = {"performance": 0, "security": 0, "accessibility": 0, "tech_seo": 0, "ux": 0}
            positive = {"performance": 0, "security": 0, "accessibility": 0, "tech_seo": 0, "ux": 0}
            
            score_map = {"Performance & Core Web Vitals": "performance", "Website Security Audit": "security", "Accessibility Audit (WCAG Standards)": "accessibility", "Technical SEO Audit": "tech_seo", "On-Page SEO Audit": "tech_seo", "Off-Page SEO & Backlinks": "tech_seo", "Analytics & Tracking Audit": "tech_seo", "User Experience (UX) Audit": "ux", "Content Audit": "ux", "E-Commerce Audit (If applicable)": "ux"}

            for cat_name, info in AUDIT_CATEGORIES.items():
                key = score_map.get(cat_name)
                if key:
                    total[key] += len(info["items"])
                    for item in info["items"]:
                        if metrics.get(item) in ["Excellent", "Good"]:
                            positive[key] += 1

            for k in scores:
                if total[k] > 0:
                    scores[k] = round((positive[k] / total[k]) * 100)

            return {**scores, "metrics": metrics, "categories": AUDIT_CATEGORIES}


    # === ROUTES ===
    @app.route("/")
    def index():
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            user = User.query.filter_by(email=request.form["email"]).first()
            if user and bcrypt.check_password_hash(user.password, request.form["password"]):
                login_user(user)
                return redirect(url_for("dashboard"))
            flash("Invalid login", "danger")
        return render_template("login.html")

    @app.route("/dashboard")
    @login_required
    def dashboard():
        reports = AuditReport.query.filter_by(user_id=current_user.id).order_by(AuditReport.date_audited.desc()).limit(10).all()
        return render_template("dashboard.html", reports=reports)

    @app.route("/run_audit", methods=["POST"])
    @login_required
    def run_audit():
        url = request.form.get("website_url", "").strip()
        if not url.startswith(("http://", "https://")):
            flash("Invalid URL", "danger")
            return redirect(url_for("dashboard"))

        result = AuditService.run_audit(url)
        scores = AuditService.calculate_score(result["metrics"])

        report = AuditReport(
            website_url=url,
            metrics_json=json.dumps(result),
            performance_score=scores["performance"],
            security_score=scores["security"],
            accessibility_score=scores["accessibility"],
            user_id=current_user.id
        )
        db.session.add(report)
        db.session.commit()
        
        if task_queue: 
            flash("Report saved, but email automation is disabled in this stable configuration.", "warning")
        
        return redirect(url_for("view_report", report_id=report.id))

    @app.route("/report/<int:report_id>")
    @login_required
    def view_report(report_id):
        report = AuditReport.query.get_or_404(report_id)
        if report.user_id != current_user.id:
            return redirect(url_for("dashboard"))
        data = json.loads(report.metrics_json)
        scores = AuditService.calculate_score(data["metrics"])
        return render_template("report_detail.html", report=report, data=data, scores=scores)

    @app.route("/report/pdf/<int:report_id>")
    @login_required
    def report_pdf(report_id):
        report = AuditReport.query.get_or_404(report_id)
        if report.user_id != current_user.id:
            return redirect(url_for("dashboard"))
        data = json.loads(report.metrics_json)
        scores = AuditService.calculate_score(data["metrics"])
        html = render_template("report_pdf.html", report=report, data=data, scores=scores)
        
        try:
            pdf = HTML(string=html).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 2cm; }')])
            response = make_response(pdf)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = "attachment; filename=FFTech_Audit.pdf"
            return response
        except Exception as e:
             flash(f"PDF generation failed. Check deployment logs for dependency errors.", "danger")
             return redirect(url_for("view_report", report_id=report_id))

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))
    
    @app.route("/schedule", methods=['POST'])
    @login_required
    def schedule_report():
        flash('Scheduling is disabled in this configuration.', 'warning')
        return redirect(url_for('dashboard'))

    @app.route("/admin")
    @login_required
    def admin_dashboard():
        if current_user.is_admin:
            flash('Admin dashboard functionality needs to be built.', 'info')
        return redirect(url_for('dashboard'))

    # === DATABASE & ADMIN SETUP ===
    if initialize_db_with_retries(app, db):
        with app.app_context():
            if not User.query.filter_by(email="roy.jamshaid@gmail.com").first():
                hashed = bcrypt.generate_password_hash("Jamshaid,1981").decode('utf-8')
                admin = User(email="roy.jamshaid@gmail.com", password=hashed, is_admin=True)
                db.session.add(admin)
                db.session.commit()
    else:
        print("FATAL ERROR: Application failed to connect/initialize database. Shutting down.")
        sys.exit(1)

    return app

application = create_app()

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
