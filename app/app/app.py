# /app/app/app.py

import os
import click
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc

# --- CRITICAL IMPORTS FOR PACKAGE STRUCTURE FIX ---
from . import models          # Imports models for db.create_all
from . import audit_service   # FIX: Relative import for audit service
from .config import config_map
# from flask_mail import Mail # Uncomment if using email

# Initialize extensions globally
db = SQLAlchemy()
# mail = Mail()

# Function to create and configure the Flask application
def create_app(config_name=os.getenv('FLASK_ENV', 'default')):
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, 'default')) 

    # Initialize extensions with the application
    db.init_app(app)
    # mail.init_app(app)
    
    # --- Routes ---
    @app.route('/')
    def index():
        return "The Web For Audit application is running successfully."

    @app.route('/run-audit/<path:url>')
    def trigger_audit(url):
        results = audit_service.AuditService.run_audit(url)
        return jsonify(results)

    # Register CLI commands
    register_cli(app)

    return app

# --- CLI Commands for Database Management ---

def register_cli(app):
    @app.cli.group()
    def db_cli():
        """Database management commands (create, drop)."""
        pass

    @db_cli.command('create_all')
    @click.option('--drop-first', is_flag=True, help='Drop all tables first before creating.')
    def create_all_command(drop_first):
        """Creates all database tables defined in the models."""
        print("Attempting to connect to database and create all tables...")
        with app.app_context():
            try:
                if drop_first:
                    print("⚠️ Dropping existing tables...")
                    db.drop_all()
                
                # CRITICAL: This is the line that creates the tables in Railway
                db.create_all() 
                print("✅ Database tables created successfully.")
            except exc.OperationalError as e:
                print("❌ FAILED to connect to the database or create tables.")
                print("ACTION REQUIRED: Check your PostgreSQL server status and config.")
                exit(1)

# Entry point for Gunicorn
app = create_app()
