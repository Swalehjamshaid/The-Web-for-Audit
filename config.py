import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///audit.db")

    # Fix for Railway's DATABASE_URL prefix AND force SSL
    if SQLALCHEMY_DATABASE_URI:
        if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
        # ADDED: Ensure sslmode=require is present for Railway proxy connections
        if "switchyard.proxy.rlwy.net" in SQLALCHEMY_DATABASE_URI and "?sslmode=" not in SQLALCHEMY_DATABASE_URI:
             SQLALCHEMY_DATABASE_URI += "?sslmode=require"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ADDED: SQLAlchemy engine options to prevent connection timeouts
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 600
    }

    # ... (rest of your config file) ...
