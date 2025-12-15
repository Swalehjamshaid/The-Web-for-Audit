from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime
import pdfkit
from apscheduler.schedulers.background import BackgroundScheduler
import plotly
import plotly.graph_objs as go
import json
import os
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

scheduler = BackgroundScheduler()
scheduler.start()

# ===================== Models =====================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(150))
    company = db.Column(db.String(150))
    role = db.Column(db.String(50), default="client")  # admin, auditor, client
    is_active = db.Column(db.Boolean, default=True)
    reports = db.relationship("AuditReport", backref="user", lazy=True)

    @property
    def is_admin(self):
        return self.role == "admin"

class AuditReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    website_url = db.Column(db.String(255))
    date_audited = db.Column(db.DateTime, default=datetime.utcnow)
    performance_score = db.Column(db.Float, default=0)
    security_score = db.Column(db.Float, default=0)
    accessibility_score = db.Column(db.Float, default=0)
    metrics_data = db.Column(db.JSON)  # 45+ metrics stored as JSON

# ===================== User Loader =====================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===================== Routes =====================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and bcrypt.check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid email or password", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    reports = AuditReport.query.filter_by(user_id=current_user.id).order_by(AuditReport.date_audited.desc()).all()
    return render_template("dashboard.html", reports=reports)

@app.route("/admin_dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Access denied", "danger")
        return redirect(url_for("dashboard"))
    users = User.query.all()
    total_audits = AuditReport.query.count()
    return render_template("admin_dashboard.html", users=users, total_audits=total_audits)

@app.route("/run_audit", methods=["POST"])
@login_required
def run_audit():
    url = request.form["website_url"]
    # Simulated audit logic with random metrics
    import random
    metrics = {f"Metric_{i}": random.choice(["Excellent","Good","Fair","Poor"]) for i in range(1,46)}
    report = AuditReport(
        user_id=current_user.id,
        website_url=url,
        performance_score=random.randint(60, 100),
        security_score=random.randint(60, 100),
        accessibility_score=random.randint(60, 100),
        metrics_data=metrics
    )
    db.session.add(report)
    db.session.commit()
    flash(f"Audit completed for {url}", "success")
    return redirect(url_for("dashboard"))

@app.route("/view_report/<int:report_id>")
@login_required
def view_report(report_id):
    report = AuditReport.query.get_or_404(report_id)
    scores = {
        "performance": report.performance_score,
        "security": report.security_score,
        "accessibility": report.accessibility_score
    }
    data = report.metrics_data
    return render_template("report_detail.html", report=report, scores=scores, data={"categories":{"All Metrics":{"desc":"Full audit metrics","items":list(data.keys())}}, "metrics":data})

@app.route("/report_pdf/<int:report_id>")
@login_required
def report_pdf(report_id):
    report = AuditReport.query.get_or_404(report_id)
    scores = {
        "performance": report.performance_score,
        "security": report.security_score,
        "accessibility": report.accessibility_score
    }
    data = report.metrics_data
    rendered = render_template("report_pdf.html", report=report, scores=scores, data={"categories":{"All Metrics":{"desc":"Full audit metrics","items":list(data.keys())}}, "metrics":data})
    pdf = pdfkit.from_string(rendered, False)
    return pdf, 200, {
        "Content-Type": "application/pdf",
        "Content-Disposition": f"inline; filename={report.website_url}.pdf"
    }

# ===================== Scheduled Audit Example =====================
def scheduled_audit(user_id, url):
    user = User.query.get(user_id)
    if not user:
        return
    import random
    metrics = {f"Metric_{i}": random.choice(["Excellent","Good","Fair","Poor"]) for i in range(1,46)}
    report = AuditReport(
        user_id=user.id,
        website_url=url,
        performance_score=random.randint(60, 100),
        security_score=random.randint(60, 100),
        accessibility_score=random.randint(60, 100),
        metrics_data=metrics
    )
    db.session.add(report)
    db.session.commit()

# Example: schedule audit daily at 12 PM (for testing)
# scheduler.add_job(scheduled_audit, 'cron', hour=12, args=[1,'https://example.com'])

# ===================== Create Admin User if not exists =====================
@app.before_first_request
def create_tables():
    db.create_all()
    admin_email = "roy.jamshaid@gmail.com"
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        hashed_pw = bcrypt.generate_password_hash("Jamshaid,1981").decode("utf-8")
        admin = User(email=admin_email, password=hashed_pw, name="Roy Jamshaid", role="admin")
        db.session.add(admin)
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
