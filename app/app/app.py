# /app/app/app.py (Updated for Robustness)

import os
import click
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc

# --- CRITICAL IMPORTS FOR PACKAGE STRUCTURE FIX ---
from . import audit_service   # FIX: Relative import for audit service
from .config import config_map

# 1. Initialize extensions globally
db = SQLAlchemy()
# mail = Mail() # Initialize other extensions globally here

# 2. Define a function to load models (prevents circular imports on startup)
def import_models():
    """Import models to ensure they are registered with SQLAlchemy."""
    from . import models
    # You can return models if needed, but the import itself registers them with db.Model.metadata
    pass

# Function to create and configure the Flask application
def create_app(config_name=os.getenv('FLASK_ENV', 'default')):
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, 'default')) 

    # 3. Initialize extensions with the application
    db.init_app(app)
    # mail.init_app(app)
    
    # 4. Load models now that 'db' is initialized with the app
    with app.app_context():
        import_models()
    
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

# --- CLI Commands for Database Management (Remains the same) ---
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
                
                db.create_all() 
                print("✅ Database tables created successfully.")
            except exc.OperationalError as e:
                print("❌ FAILED to connect to the database or create tables.")
                print("ACTION REQUIRED: Check your PostgreSQL server status and config.")
                exit(1)

# 5. Entry point for Gunicorn: This MUST be the last line that defines 'app'
app = create_app()
