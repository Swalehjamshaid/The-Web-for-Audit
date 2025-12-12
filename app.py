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
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
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

# --- AUDIT ENGINE (Simulated) with Max Metrics (45 Total) ---
class AuditService:
    METRICS = {
        "Performance (12 checks)": ["1. Page Load Speed (LCP)", "2. First Contentful Paint (FCP)", "3. Total Blocking Time (TBT)", "4. Cumulative Layout Shift (CLS)", "5. Time to Interactive (TTI)", "6. Server Response Time (TTFB)", "7. Image Optimization Status", "8. Render Blocking Resources", "9. Gzip/Brotli Compression", "10. Caching Policy", "11. Network Payload Size", "12. JavaScript Execution Time"],
        
        "Security (15 checks)": [
            "13. HTTPS Enforcement", "14. Content Security Policy", "15. XSS Protection", "16. Secure Headers", "17. HSTS Header", "18. CORS Policy", "19. OWASP Compliance", "20. Dependency Security", "21. Rate Limiting", "22. SQL Injection Protection",
            "23. Input Sanitization", "24. Server Patch Level", "25. Session Management", "26. Two-Factor Auth (2FA)", "27. Subdomain Takeover" 
        ],
        
        "Accessibility (10 checks)": [
            "28. WCAG 2.1 Compliance", "29. Mobile Responsiveness", "30. Alt Text on Images", "31. Contrast Ratio", "32. Keyboard Navigation", "33. Semantic HTML", "34. ARIA Labels",
            "35. Focus Indicators", "36. Language Declaration", "37. Error Identification" 
        ],
        
        "Usability & SEO (8 checks)": [
            "38. Meta Tags (Title/Desc)", "39. Viewport Config", "40. Broken Links", "41. Sitemap & robots.txt", "42. URL Structure (Canonical)", "43. Readability Score", "44. UX Flow (Journey)", "45. ISO 25010 Compliance"
        ]
    }

    @staticmethod
    def run_audit(url):
        time.sleep(2) # Simulate audit time
        detailed = {}
        all_metrics = [metric for sublist in AuditService.METRICS.values() for metric in sublist]
        
        for item in all_metrics:
            # Simulation for performance/size metrics
            if any(k in item.lower() for k in ["speed", "time", "load", "fcp", "lcp", "tti", "ttfb", "execution time"]):
                detailed[item] = f"{random.uniform(0.8, 4.5):.2f}s"
            elif "payload size" in item.lower():
                detailed[item] = f"{random.uniform(0.5, 3.0):.2f}MB"
            else:
                # Biased random choice for status results
                detailed[item] = random.choices(["Excellent", "Good", "Fair", "Poor"], weights=[40, 30, 20, 10], k=1)[0]
        
        return { 'metrics': detailed }

    @staticmethod
    def calculate_score(metrics):
        scores = {'performance': 0, 'security': 0, 'accessibility': 0, 'usability': 0}
        
        for category, items in AuditService.METRICS.items():
            # Map category name to score key
            key_map = {'performance': 'performance', 'security': 'security', 'accessibility': 'accessibility', 'usability': 'usability'}
            category_key = category.split(' ')[0].lower()
            score_key = key_map.get(category_key)
            
            if score_key:
                total_count = len(items)
                positive_count = 0
                
                for metric_name in items:
                    result = metrics.get(metric_name)
                    if result in ["Excellent", "Good"]:
                        positive_count += 1
                
                if total_count > 0:
                    scores[score_key] = round((positive_count / total_count) * 100)
        
        return scores

# --- Task Integration (CRITICAL FIX: Changed 'tasks' to 'worker') ---
try:
    from worker import send_report_email, run_scheduled_report
except ImportError:
    send_report_email = None
    run_scheduled_report = None


# --- Admin User Creation ---
def create_admin_user():
    with app.app_context():
        db.create_all()
        email = os.getenv('ADMIN_EMAIL', 'roy.jamshaid@gmail.com')
        password = os.getenv('ADMIN_PASSWORD', 'Jamshaid,1981')
        if not User.query.filter_by(email=email).first():
            hashed = bcrypt.generate_password_hash(password).decode('utf-8')
            admin = User(email=email, password=hashed, is_admin=True)
            db.session.add(admin)
            db.session.commit()

# --- Routes ---
@app.route('/')
def home():
    return redirect(url_for('dashboard')) if current_user.is_authenticated else render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    reports = AuditReport.query.filter_by(user_id=current_user.id).order_by(AuditReport.date_audited.desc()).limit(10).all()
    return render_template('dashboard.html', reports=reports)

@app.route('/run_audit', methods=['POST'])
@login_required
def run_audit():
    url = request.form.get('website_url', '').strip()
    email_recipient = request.form.get('email_recipient') 
    
    if not url.startswith(('http://', 'https://')):
        flash('Valid URL required', 'danger')
        return redirect(url_for('dashboard'))
    
    # 1. Run Audit
    result = AuditService.run_audit(url)
    detailed_metrics = result['metrics']
    
    # 2. Calculate Score
    scores = AuditService.calculate_score(detailed_metrics)
    
    # 3. Save Report
    report = AuditReport(
        website_url=url,
        performance_score=scores['performance'],
        security_score=scores['security'],
        accessibility_score=scores['accessibility'],
        metrics_json=json.dumps(detailed_metrics),
        user_id=current_user.id
    )
    db.session.add(report)
    db.session.commit()
    
    flash('Audit completed!', 'success')
    
    # 4. Immediately Queue Email Send (If recipient provided)
    if email_recipient and task_queue and send_report_email:
        task_queue.enqueue(send_report_email, report.id, email_recipient)
        flash(f'Report email queued for immediate send to {email_recipient}!', 'info')
        
    return redirect(url_for('view_report', report_id=report.id))


@app.route('/report/<int:report_id>')
@login_required
def view_report(report_id):
    report = AuditReport.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Prepare data for report_detail.html
    metrics_data = json.loads(report.metrics_json)
    scores = AuditService.calculate_score(metrics_data)
    metrics_by_cat = {cat: {k: metrics_data.get(k, 'N/A') for k in items} 
                      for cat, items in AuditService.METRICS.items()}
    
    return render_template('report_detail.html', report=report, metrics=metrics_by_cat, scores=scores)

@app.route('/report/pdf/<int:report_id>')
@login_required
def report_pdf(report_id):
    report = AuditReport.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Prepare data for report_pdf.html
    metrics_data = json.loads(report.metrics_json)
    scores = AuditService.calculate_score(metrics_data)
    metrics_by_cat = {cat: {k: metrics_data.get(k, 'N/A') for k in items} 
                      for cat, items in AuditService.METRICS.items()}
    
    def generate_pdf_content(report, metrics, scores):
        # Pass scores to report_pdf.html
        return render_template('report_pdf.html', report=report, metrics=metrics, scores=scores)
    
    html = generate_pdf_content(report, metrics_by_cat, scores)
    
    try:
        pdf = HTML(string=html).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 2cm } body { font-family: sans-serif; }')])
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=report_{report.id}.pdf'
        return response
    except Exception as e:
        print(f"PDF GENERATION ERROR: {e}") 
        flash('PDF generation failed. Check server logs for WeasyPrint/dependency issues.', 'danger')
        return redirect(url_for('view_report', report_id=report_id))

@app.route('/schedule', methods=['POST'])
@login_required
def schedule_report():
    url = request.form.get('scheduled_website')
    email = request.form.get('scheduled_email')
    
    if not url or not url.startswith(('http://', 'https://')):
        flash('Invalid URL', 'danger')
        return redirect(url_for('dashboard'))
        
    current_user.scheduled_website = url
    current_user.scheduled_email = email
    db.session.commit()
    
    # Queue an immediate run (test) via the worker, which handles the audit, save, and email.
    if task_queue and run_scheduled_report:
        task_queue.enqueue(run_scheduled_report, current_user.id, job_timeout='30m')
        flash('Schedule saved! An immediate test report has been queued for processing.', 'success')
    elif not task_queue:
        flash('Schedule saved, but Redis is not connected. Automated reports will not run.', 'warning')
    
    return redirect(url_for('dashboard'))

@app.route('/unschedule', methods=['POST'])
@login_required
def unschedule_report():
    current_user.scheduled_website = None
    current_user.scheduled_email = None
    db.session.commit()
    flash('Schedule cancelled', 'info')
    return redirect(url_for('dashboard'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Admin access required.', 'danger')
        return redirect(url_for('dashboard'))
    
    all_users = User.query.all()
    latest_reports = AuditReport.query.order_by(AuditReport.date_audited.desc()).limit(50).all()
    
    return render_template(
        'admin_dashboard.html', 
        users=all_users, 
        reports=latest_reports,
        title="Admin Panel"
    )

@app.route('/admin/create_user', methods=['POST'])
@login_required
def admin_create_user():
    if not current_user.is_admin:
        flash('Admin access required to create users.', 'danger')
        return redirect(url_for('dashboard'))
    
    email = request.form.get('new_user_email')
    password = request.form.get('new_user_password')
    is_admin_flag = request.form.get('is_admin_flag') == 'on' 
    
    if User.query.filter_by(email=email).first():
        flash(f'User with email {email} already exists.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    if email and password and len(password) >= 6: 
        try:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(email=email, password=hashed_password, is_admin=is_admin_flag)
            db.session.add(new_user)
            db.session.commit()
            flash(f'User {email} created successfully. Admin status: {is_admin_flag}', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {e}', 'danger')
    else:
        flash('Invalid email or password (must be at least 6 characters).', 'danger')
    
    return redirect(url_for('admin_dashboard'))


# --- Application Startup ---
with app.app_context():
    create_admin_user()

if __name__ == '__main__':
    app.run(debug=True)
