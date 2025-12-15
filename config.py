import os

class Config:
    # ... other config ...
    
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///audit.db")

    # Fix for Railway's DATABASE_URL prefix AND force SSL
    if SQLALCHEMY_DATABASE_URI:
        if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
            # 1. FIX: Replace old 'postgres://' with 'postgresql://'
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
        # 2. FIX: Ensure sslmode=require is present for Railway proxy connections
        # The specific hostname might be different, but this general logic is key.
        # This check is safer than relying on a specific hostname:
        if "sslmode=" not in SQLALCHEMY_DATABASE_URI:
             SQLALCHEMY_DATABASE_URI += "?sslmode=require" if "?" not in SQLALCHEMY_DATABASE_URI else "&sslmode=require"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 3. FIX: SQLAlchemy engine options to prevent connection timeouts
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 600
    }
    
    # ... rest of config ...
