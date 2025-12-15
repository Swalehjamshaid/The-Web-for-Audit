import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pdfkit

# =======================
# Environment Variables
# =======================
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret123")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "roy.jamshaid@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Jamshaid,1981")
PDFKIT_CMD = os.getenv("PDFKIT_WKHTMLTOPDF_CMD", "/usr/local/bin/wkhtmltopdf")

# =======================
# Flask App Setup
# =======================
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# =======================
# PDFKit Config
# =======================
pdf_config = pdfkit.configuration(wkhtmltopdf=PDFKIT_CMD)

# =======================
# Models
# =======================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100))
    company = db.Column(db.String(100))
    role = db.Column(db.String(50), default="client")  # client, auditor, admin
    is_active = db.Column(db.Boolean, default=True)

    @property
    def is_admin(self):
        return self.role == "admin"

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_url = db.Column(db.String(255), nullable=False)
    date_audited = db.Column(db.DateTime, default=datetime.utcnow)
    performance_score = db.Column(db.Integer, default=0)
    security_score = db.Column(db.Integer, default=0)
    accessibility_score = db.Column(db.Integer, default=0)
    data_json = db.Column(db.JSON)  # Store detailed audit results

# =======================
# Login Manager
# =======================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =======================
# Routes
# =======================

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template("dashboard.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    reports = Report.query.order_by(Report.date_audited.desc()).all()
    return render_template("dashboard.html", reports=reports)

@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))
    users = User.query.all()
    total_audits = Report.query.count()
    return render_template("admin_dashboard.html", users=users, total_audits=total_audits)

@app.route("/run_audit", methods=["POST"])
@login_required
def run_audit():
    website_url = request.form["website_url"]
    # Dummy audit scores (replace with real audit logic)
    report = Report(
        website_url=website_url,
        performance_score=80,
        security_score=75,
        accessibility_score=85,
        data_json={
            "categories": {
                "Performance": {"desc": "Website speed & load time", "items": ["Load Time", "Page Size"]},
                "Security": {"desc": "Security headers & vulnerabilities", "items": ["SSL", "XSS", "Content Security Policy"]},
                "Accessibility": {"desc": "Accessibility standards", "items": ["Alt Tags", "ARIA", "Contrast"]}
            },
            "metrics": {
                "Load Time": "Good",
                "Page Size": "Fair",
                "SSL": "Excellent",
                "XSS": "Good",
                "Content Security Policy": "Fair",
                "Alt Tags": "Excellent",
                "ARIA": "Good",
                "Contrast": "Good"
            }
        }
    )
    db.session.add(report)
    db.session.commit()
    flash(f"Audit completed for {website_url}", "success")
    return redirect(url_for("dashboard"))

@app.route("/report/<int:report_id>")
@login_required
def view_report(report_id):
    report = Report.query.get_or_404(report_id)
    scores = {
        "performance": report.performance_score,
        "security": report.security_score,
        "accessibility": report.accessibility_score
    }
    return render_template("report_detail.html", report=report, scores=scores, data=report.data_json)

@app.route("/report/<int:report_id>/pdf")
@login_required
def report_pdf(report_id):
    report = Report.query.get_or_404(report_id)
    scores = {
        "performance": report.performance_score,
        "security": report.security_score,
        "accessibility": report.accessibility_score
    }
    html = render_template("report_pdf.html", report=report, scores=scores, data=report.data_json)
    pdf_file = f"report_{report.id}.pdf"
    pdfkit.from_string(html, pdf_file, configuration=pdf_config)
    return send_file(pdf_file, as_attachment=True)

# =======================
# Admin Creation (on first run)
# =======================
@app.before_first_request
def create_admin():
    db.create_all()
    admin = User.query.filter_by(email=ADMIN_EMAIL).first()
    if not admin:
        new_admin = User(
            email=ADMIN_EMAIL,
            password=generate_password_hash(ADMIN_PASSWORD, method='sha256'),
            role="admin",
            name="Admin"
        )
        db.session.add(new_admin)
        db.session.commit()
        print(f"Admin created: {ADMIN_EMAIL}")

# =======================
# Run App
# =======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
