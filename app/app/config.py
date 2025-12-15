# /app/app/config.py

import os

class Config:
    """Base configuration settings."""
    
    # --- General Flask Config ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
    
    # --- Database Config (PostgreSQL/SQLAlchemy) ---
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///audit.db")

    # CRITICAL FIX for Railway PostgreSQL Connection
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres"):
        # 1. Replace deprecated 'postgres://' with 'postgresql://'
        if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
        # 2. Add required SSL mode for Railway proxy connections
        if "sslmode=" not in SQLALCHEMY_DATABASE_URI:
             SQLALCHEMY_DATABASE_URI += "?sslmode=require" if "?" not in SQLALCHEMY_DATABASE_URI else "&sslmode=require"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- SQLAlchemy Connection Pool Optimizations ---
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,    # Test connections before checkout
        'pool_recycle': 600,      # Recycle connections after 10 minutes
        'max_overflow': 10        # Limit connection spikes
    }
    
    # --- Task Queue/Worker Config ---
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    RQ_QUEUE_NAME = "audit_tasks"
    MAX_AUDIT_TIMEOUT = 300 

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    
# Export a dictionary for easy config loading in app.py
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
