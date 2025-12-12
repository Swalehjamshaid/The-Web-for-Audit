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

# --- Configuration (Railway Integration) ---
DB_URL = os.getenv("DATABASE_URL")
if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL or 'sqlite:///site.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me-in-production')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')

# CRITICAL FIX 1: Safely handle MAIL_PORT integer conversion
try:
    port_val = os.getenv('MAIL_PORT')
    if port_val:
        app.config['MAIL_PORT'] = int(port_val)
    else:
        app.config['MAIL_PORT'] = 587
except ValueError:
    app.config['MAIL_PORT'] = 587
    print("Warning: MAIL_PORT environment variable value is invalid. Defaulting to 587.")

app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# --- Extensions ---
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Redis/RQ Setup (Railway Integration) ---
try:
    redis_conn = Redis.from_url(os.getenv('REDIS_URL') or os.getenv('REDIS_RAILWAY', 'redis://localhost:6379'))
    redis_conn.ping() 
    task_queue = Queue(connection=redis_conn)
    print("Redis Queue initialized successfully in app.py")
except Exception as e:
    print(f"Warning: Could not connect to Redis/initialize Queue: {e}")
    task_queue = None

# --- MODELS ---
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

# --- AUDIT ENGINE (Simulated) with 10 COMPREHENSIVE CATEGORIES (Total 50 Metrics) ---
class AuditService:
    METRICS = {
        "1. Technical SEO Audit (7 checks)": [
            "Crawlability (robots.txt, sitemap)", "Indexability (noindex, canonicals)", "Broken Links Status", 
            "Redirect Chains/Loops", "URL Structure Optimization", "Orphan Pages Check", "Crawl Errors (4xx/5xx)"
        ],
        "2. Performance & Core Web Vitals (8 checks)": [
            "Largest Contentful Paint (LCP)", "Interaction to Next Paint (INP)", "Cumulative Layout Shift (CLS)", 
            "Server Response Time (TTFB)", "Image Optimization Status", "CSS/JS Minification Status", 
            "Browser Caching Policy", "Mobile Page Speed"
        ],
        "3. On-Page SEO Audit (6 checks)": [
            "Unique Title Tags", "Unique Meta Descriptions", "H1/H2 Structure", 
            "Content Keyword Relevance", "Image ALT Text Coverage", "Structured Data Markup"
        ],
        "4. User Experience (UX) Audit (5 checks)": [
            "Navigation Usability (Menus)", "Readability Score", "Mobile Responsiveness (Viewport)", 
            "Call-to-Action (CTA) Clarity", "Visual Consistency"
        ],
        "5. Website Security Audit (6 checks)": [
            "HTTPS & SSL Certificate Validity", "HSTS Header Implementation", "Content Security Policy (CSP)",
            "Server Patch Level", "Dependency Security (OWASP)", "Malware/Vulnerability Check"
        ],
        "6. Accessibility Audit (WCAG Standards) (5 checks)": [
            "Color Contrast Ratio", "Keyboard Navigation Compliance", "Screen Reader Compatibility", 
            "ARIA Labels Presence", "Semantic HTML Structure"
        ],
        "7. Content Audit (4 checks)": [
            "Content Uniqueness and Depth", "Relevance to User Intent", "Outdated Content Identification", 
            "Content Gaps Identified"
        ],
        "8. Off-Page SEO & Backlinks (4 checks)": [
            "Backlink Profile Quality Score", "Toxic Link Detection", "Local SEO Signals (NAP)", 
            "Brand Mentions/Review Activity"
        ],
        "9. Analytics & Tracking Audit (3 checks)": [
            "GA4/Analytics Setup Verification", "Goals and Events Tracking", "Tag Manager Configuration"
        ],
        "10. E-Commerce Audit (Optional) (2 checks)": [
            "Product Page Optimization", "Checkout Flow Usability"
        ]
    }

    @staticmethod
    def run_audit(url):
        time.sleep(2) # Simulate audit time
        detailed = {}
        all_metrics = [metric for sublist in AuditService.METRICS.values() for metric in sublist]
        
        for item in all_metrics:
            # Simulation for performance/size metrics
            if any(k in item.lower() for k in ["lcp", "inp", "cls", "ttfb", "speed", "load", "execution"]):
                detailed[item] = f"{random.uniform(0.8, 4.5):.2f}s"
            elif "payload size" in item.lower():
                detailed[item] = f"{random.uniform(0.5, 3.0):.2f}MB"
            else:
                # Biased random choice for status results
                detailed[item] = random.choices(["Excellent", "Good", "Fair", "Poor"], weights=[40, 30, 20, 10], k=1)[0]
        
        return { 'metrics': detailed }

    @staticmethod
    def calculate_score(metrics):
        # Define the 5 final scores to display
        scores = {'performance': 0, 'security': 0, 'accessibility': 0, 'tech_seo': 0, 'ux': 0}
        category_score_map = {
            "1. Technical SEO Audit (7 checks)": "tech_seo",
            "2. Performance & Core Web Vitals (8 checks)": "performance",
            "3. On-Page SEO Audit (6 checks)": "tech_seo", 
            "4. User Experience (UX) Audit (5 checks)": "ux",
            "5. Website Security Audit (6 checks)": "security",
            "6. Accessibility Audit (WCAG Standards) (5 checks)": "accessibility",
            "7. Content Audit (4 checks)": "ux", 
            "8. Off-Page SEO & Backlinks (4 checks)": "tech_seo", 
            "9. Analytics & Tracking Audit (3 checks)": "tech_seo", 
            "10. E-Commerce Audit (Optional) (2 checks)": "ux" 
        }

        total_counts = {'performance': 0, 'security': 0, 'accessibility': 0, 'tech_seo': 0, 'ux': 0}
        positive_counts = {'performance': 0, 'security': 0, 'accessibility': 0, 'tech_seo': 0, 'ux': 0}

        for category, items in AuditService.METRICS.items():
            score_key = category_score_map.get(category)
            if score_key:
                total_counts[score_key] += len(items)
                
                for metric_name in items:
                    result = metrics.get(metric_name)
                    if result in ["Excellent", "Good"]:
                        positive_counts[score_key] += 1
        
        # Finalize scores calculation
        for key in scores.keys():
            if total_counts[key] > 0:
                scores[key] = round((positive_counts[key] / total_counts[key]) * 100)
        
        # Map the calculated scores back to the structure expected by the DB (performance, security, accessibility)
        final_scores = {
            'performance': scores['performance'],
            'security': scores['security'],
            'accessibility': scores['accessibility'],
            'metrics': metrics,
            'all_scores': scores # Pass all 5 detailed scores to the template
        }
        return final_scores


# --- Task Integration (CRITICAL: Changed 'tasks' to 'worker') ---
# NOTE: The worker functions are NOT available in this deployment (Procfile is single-line)
try:
    from worker import send_report_email, run_scheduled_report
except ImportError:
    send_report_email = None
    run_scheduled_report = None


# --- Admin User Creation (Unchanged) ---
def create_admin_user():
    with app.app_context():
        # NOTE: db.create_all() is handled by initialize_db_with_retries
        email = os.getenv('ADMIN_EMAIL', 'roy.jamshaid@gmail.com')
        password = os.getenv('ADMIN_PASSWORD', 'Jamshaid,1981')
        if not User.query.filter_by(email=email).first():
            hashed = bcrypt.generate_password_hash(password).decode('utf-8')
            admin = User(email=email, password=hashed, is_admin=True)
            db.session.add(admin)
            db.session.commit()

# CRITICAL FIX 2: Safely initialize database with retries on startup
def initialize_db_with_retries(retries=5, delay=5):
    with app.app_context():
        for i in range(retries):
            try:
                db.create_all()
                print("Database initialized successfully.")
                return True
            except Exception as e:
                print(f"Database initialization attempt {i+1} failed: {e}")
                if i < retries - 1:
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print("Failed to initialize database after multiple retries. EXITING.")
                    # sys.exit(1) # Do not exit here; let Gunicorn handle the error if it's fatal
                    return False
        return False
        
# --- Routes (Routes below are unchanged) ---
@app.route('/')
def home():
    # ... (rest of code)

# ... (all other routes are unchanged)

# --- Application Startup ---
# Initialize DB (with retries) and then create admin user
if initialize_db_with_retries():
    create_admin_user()

if __name__ == '__main__':
    app.run(debug=True)
