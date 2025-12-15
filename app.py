from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import pdfkit
import requests
import io
import matplotlib.pyplot as plt
import base64
from threading import Thread
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///audit.db'  # Use PostgreSQL in prod
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class AuditResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2083), nullable=False)
    status_code = db.Column(db.Integer)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)

# Load user callback

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes

@app.route('/')
def index():
    return "Welcome to the Web Audit App! Please login."

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Simple metric: count audits & average status code
    audits = AuditResult.query.all()
    count = len(audits)
    avg_status = sum([a.status_code for a in audits if a.status_code]) / (count or 1)

    # Create a simple graph - status code distribution
    status_codes = {}
    for audit in audits:
        status_codes[audit.status_code] = status_codes.get(audit.status_code, 0) + 1
    # Plot
    plt.bar(status_codes.keys(), status_codes.values())
    plt.xlabel('Status Code')
    plt.ylabel('Count')
    plt.title('Status Code Distribution')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    return render_template('dashboard.html', count=count, avg_status=avg_status, graph=img_base64)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/audit', methods=['GET', 'POST'])
@login_required
def audit():
    if request.method == 'POST':
        url = request.form['url']
        try:
            response = requests.get(url)
            status_code = response.status_code
            # Save result
            audit_result = AuditResult(url=url, status_code=status_code)
            db.session.add(audit_result)
            db.session.commit()
            flash(f'Audit done for {url}, status code: {status_code}')
        except Exception as e:
            flash(f'Error auditing {url}: {str(e)}')
        return redirect(url_for('dashboard'))
    return render_template('audit.html')

@app.route('/report/<int:audit_id>')
@login_required
def report(audit_id):
    audit = AuditResult.query.get_or_404(audit_id)
    rendered = render_template('report.html', audit=audit)
    pdf = pdfkit.from_string(rendered, False)
    return send_file(io.BytesIO(pdf), attachment_filename='report.pdf', as_attachment=True)

# Run scheduled audit example (very simple)

def scheduled_audit(url, interval_sec=60):
    while True:
        try:
            response = requests.get(url)
            audit_result = AuditResult(url=url, status_code=response.status_code)
            db.session.add(audit_result)
            db.session.commit()
            print(f"Scheduled audit done for {url}")
        except Exception as e:
            print(f"Error in scheduled audit: {e}")
        time.sleep(interval_sec)

@app.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    if request.method == 'POST':
        url = request.form['url']
        interval = int(request.form['interval'])
        # Start a thread for simplicity (not for prod!)
        thread = Thread(target=scheduled_audit, args=(url, interval))
        thread.daemon = True
        thread.start()
        flash(f'Scheduled audit started for {url} every {interval} seconds')
        return redirect(url_for('dashboard'))
    return render_template('schedule.html')

if __name__ == '__main__':
    with app.app_context():
        # Create admin user if not exist
        admin_email = "roy.jamshaid@gmail.com"
        admin_password = "Jamshaid,1981"
        if not User.query.filter_by(email=admin_email).first():
            hashed_pw = bcrypt.generate_password_hash(admin_password).decode('utf-8')
            admin = User(email=admin_email, password_hash=hashed_pw)
            db.session.add(admin)
            db.session.commit()
            print("Admin user created.")
    app.run(host='0.0.0.0', port=8080)
