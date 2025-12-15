# /app/app/models.py

from datetime import datetime
import json
# CRITICAL FIX: Use the absolute package path to import 'db'. 
# This prevents the circular import problem when Gunicorn loads the application.
from app.app.app import db  

# --- Example Models ---

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
