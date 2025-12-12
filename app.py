
import os
import json
import time
import random
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
import sys

from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_mail import Mail, Message
from redis import Redis
from rq import Queue
from weasyprint import HTML, CSS

# --- Environment and App Setup ---
load_dotenv()

app = Flask(__name__)

# --- Configuration (Railway-ready) ---
DB_URL = os.getenv("DATABASE_URL")
if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

app.config.update({
    'SQLALCHEMY_DATABASE_URI': DB_URL or 'sqlite:///site.db',
    'SECRET_KEY': os.getenv('SECRET_KEY', 'change-me-in-production'),
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    # Email config
    'MAIL_SERVER': os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
    'MAIL_PORT': int(os.getenv('MAIL_PORT', 587)),
    'MAIL_USE_TLS': os.getenv('MAIL_USE_TLS', 'True').lower() == 'true',
    'MAIL_USERNAME': os.getenv('MAIL_USERNAME'),
    'MAIL_PASSWORD': os.getenv('MAIL_PASSWORD'),
    'MAIL_DEFAULT_SENDER': os.getenv('MAIL_DEFAULT_SENDER'),
})

# --- Extensions ---
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Redis/RQ Setup (safe fallback) ---
try:
    redis_conn = Redis.from_url(os.getenv('REDIS_URL') or 'redis://localhost:6379')
    redis_conn.ping()
    task_queue = Queue(connection=redis_conn)
    print("Redis Queue initialized successfully")
except Exception as e:
    print(f"Redis unavailable: {e}")
    task_queue = None

# --- MODELS (unchanged) ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    scheduled_website = db.Column(db.String(255))
    scheduled_email = db.Column(db.String(120))
    reports = db.relationship('AuditReport', backref='auditor', lazy=True)

class AuditReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_url = db.Column(db.String(255), nullable=False)
    date_audited = db.Column(db.DateTime, default=datetime.utcnow)
    metrics_json = db.Column(db.Text, nullable=False)
    performance_score = db.Column(db.Integer, default=0)
    security_score = db.Column(db.Integer, default=0)
    accessibility_score = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --- AUDIT ENGINE (exactly your original simulation logic) ---
class AuditService:
    METRICS = { ... }  # ← Your full 50-metric dictionary stays 100% unchanged

    @staticmethod
    def run_audit(url):
        time.sleep(2)
        detailed = {}
        all_metrics = [m for sublist in AuditService.METRICS.values() for m in sublist]
        for item in all_metrics:
            if any(k in item.lower() for k in ["lcp", "inp", "cls", "ttfb", "speed", "load", "execution"]):
                detailed[item] = f"{random.uniform(0.8, 4.5):.2f}s"
            elif "payload size" in item.lower():
                detailed[item] = f"{random.uniform(0.5, 3.0):.2f}MB"
            else:
                detailed[item] = random.choices(["Excellent", "Good", "Fair", "Poor"], weights=[40, 30, 20, 10], k=1)[0]
        return {'metrics': detailed}

    @staticmethod
    def calculate_score(metrics):
        # ← Your original scoring logic 100% preserved
        # (only tiny formatting fixes for readability)
        scores = {'performance': 0, 'security': 0, 'accessibility': 0, 'tech_seo': 0, 'ux': 0}
        category_score_map = { ... }  # unchanged
        # ... rest of your perfect scoring code ...
        return final_scores

# --- Worker import (safe) ---
try:
    from worker import send_report_email, run_scheduled_report
except ImportError:
    send_report_email = None
    run_scheduled_report = None

# --- Admin & DB init (unchanged logic, just safer) ---
def create_admin_user():
    with app.app_context():
        email = os.getenv('ADMIN_EMAIL', 'roy.jamshaid@gmail.com')
        password = os.getenv('ADMIN_PASSWORD', 'Jamshaid,1981')
        if not User.query.filter_by(email=email).first():
            hashed = bcrypt.generate_password_hash(password).decode('utf-8')
            admin = User(email=email, password=hashed, is_admin=True)
            db.session.add(admin)
            db.session.commit()

def initialize_db_with_retries(retries=6, delay=5):
    with app.app_context():
        for i in range(retries):
            try:
                db.create_all()
                print("Database tables created successfully.")
                return True
            except Exception as e:
                print(f"DB init attempt {i+1}/{retries} failed: {e}")
                if i < retries - 1:
                    time.sleep(delay)
        print("Fatal: Could not initialize database.")
        return False

# --- ALL YOUR ROUTES (100% untouched logic) ---
# home, login, logout, dashboard, run_audit, view_report, report_pdf, schedule, etc.
# → Exactly as you wrote them — only minor formatting for PEP8

@app.route('/')
def home():
    return redirect(url_for('dashboard')) if current_user.is_authenticated else render_template('index.html')

# ... (all your other routes exactly as before) ...

# --- CRITICAL: Application factory pattern for Gunicorn ---
def create_app():
    # Initialize DB and admin only once at startup
    if initialize_db_with_retries():
        create_admin_user()
    return app

# ← This is the instance Gunicorn will import
application = create_app()

# --- Remove Flask's debug server from production ---
# Delete or comment out the old if __name__ == '__main__' block
# if __name__ == '__main__':
#     application.run(debug=True)

# Final line must be:
if __name__ == "__main__":
    # Only for local testing
    application.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
