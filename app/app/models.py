# /app/app/models.py

from .app import db  # Import the db object initialized in app.py
from datetime import datetime
import json

# --- Example Models (REQUIRED FOR db.create_all) ---

class AuditReport(db.Model):
    __tablename__ = 'audit_reports'
    id = db.Column(db.Integer, primary_key=True)
    website_url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Store the JSON result blob from AuditService
    metrics_json = db.Column(db.Text, nullable=False) 

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
