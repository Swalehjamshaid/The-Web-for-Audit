import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///audit.db")

    # CRITICAL FIX for Railway PostgreSQL Connection
    if SQLALCHEMY_DATABASE_URI:
        # 1. Replace old 'postgres://' with 'postgresql://' (required by modern SQLAlchemy)
        if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
        # 2. Add required SSL mode for Railway proxy connections
        if "sslmode=" not in SQLALCHEMY_DATABASE_URI:
             # Append '?sslmode=require' if no existing query params, else append '&sslmode=require'
             SQLALCHEMY_DATABASE_URI += "?sslmode=require" if "?" not in SQLALCHEMY_DATABASE_URI else "&sslmode=require"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ADDED: SQLAlchemy engine options to prevent connection timeouts
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 600
    }
    
    # ... rest of your config file ...
