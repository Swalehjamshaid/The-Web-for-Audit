from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from datetime import datetime
import json
from config import Config
from audit_service import AuditService
import sqlalchemy # Import SQLAlchemy to reference OperationalError
from tenacity import retry, stop_after_attempt, wait_exponential # Import tenacity

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

# >>> ADDED: Code to create all database tables on startup <<<
with app.app_context():
    db.create_all()
# <<< END ADDED SECTION <<<

bcrypt = Bcrypt(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ---------------- Models ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(50))
    company = db.Column(db.String(50))
    role = db.Column(db.String(20), default="client")
    is_active = db.Column(db.Boolean, default=True)
    scheduled_website = db.Column(db.String(255))

    @property
    def is_admin(self):
        return self.role == 'admin'

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

class AuditReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_url = db.Column(db.String(255), nullable=False)
    date_audited = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    metrics_json = db.Column(db.Text)
    performance_score = db.Column(db.Float)
    security_score = db.Column(db.Float)
    accessibility_score = db.Column(db.Float)

# ---------------- Login ----------------
@login_manager.user_loader
# Add retry logic for transient database connection issues
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except sqlalchemy.exc.OperationalError:
        # Re-raise the exception to allow 'tenacity' to handle the retry mechanism
        print("Database connection failed during load_user, retrying...")
        raise

# ---------------- Routes ----------------
@app.route('/')
def home():
    return redirect(url_for('dashboard')) if current_user.is_authenticated else render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    reports = AuditReport.query.filter_by(user_id=current_user.id).order_by(AuditReport.date_audited.desc()).all()
    return render_template('dashboard.html', reports=reports)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials','danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/run_audit', methods=['POST'])
@login_required
def run_audit():
    url = request.form['website_url']
    audit_data = AuditService.run_audit(url)
    report = AuditReport(
        website_url=url,
        user_id=current_user.id,
        metrics_json=json.dumps(audit_data['metrics']),
        performance_score=audit_data['scores']['performance_score'],
        security_score=audit_data['scores']['security_score'],
        accessibility_score=audit_data['scores']['accessibility_score']
    )
    db.session.add(report)
    db.session.commit()
    flash(f'Audit for {url} completed', 'success')
    return redirect(url_for('dashboard'))

@app.route('/report/<int:report_id>')
@login_required
def view_report(report_id):
    report = AuditReport.query.get_or_404(report_id)
    metrics = json.loads(report.metrics_json)
    audit_data = AuditService.organize_metrics(metrics)
    return render_template('report_detail.html', report=report, data=audit_data, scores={
        "performance": report.performance_score,
        "security": report.security_score,
        "accessibility": report.accessibility_score
    })

# ---------------- Admin ----------------
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    users = User.query.all()
    total_audits = AuditReport.query.count()
    return render_template('admin_dashboard.html', users=users, total_audits=total_audits)

@app.route('/admin/create_user', methods=['POST'])
@login_required
def admin_create_user():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    user = User(
        email=request.form['email'],
        name=request.form.get('name'),
        company=request.form.get('company'),
        role=request.form.get('role')
    )
    user.set_password(request.form['password'])
    db.session.add(user)
    db.session.commit()
    flash(f"User {user.email} created",'success')
    return redirect(url_for('admin_dashboard'))

if __name__=='__main__':
    # This block is only for local development/running python app.py
    # Gunicorn is used for the production environment.
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
