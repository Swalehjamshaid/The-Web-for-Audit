import os

class Config:
    """Base configuration settings."""
    
    # --- General Flask Config ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
    
    # --- Database Config (PostgreSQL/SQLAlchemy) ---
    # Railway automatically provides DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///audit.db")

    # CRITICAL FIX for Railway PostgreSQL Connection
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres"):
        # 1. Replace deprecated 'postgres://' with 'postgresql://' (required by modern SQLAlchemy)
        if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
        # 2. Add required SSL mode for Railway proxy connections
        if "sslmode=" not in SQLALCHEMY_DATABASE_URI:
             # Append '?sslmode=require' if no existing query params, else append '&sslmode=require'
             SQLALCHEMY_DATABASE_URI += "?sslmode=require" if "?" not in SQLALCHEMY_DATABASE_URI else "&sslmode=require"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- SQLAlchemy Connection Pool Optimizations ---
    # These settings help prevent the connection timeout errors seen previously.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,    # Test connections before checkout
        'pool_recycle': 600,      # Recycle connections after 10 minutes
        'max_overflow': 10        # Maximum number of connections to allow in the pool's overflow
    }
    
    # --- Task Queue/Worker Config (for scheduler.py and worker.py) ---
    # Assuming you are using Redis Queue (RQ) for background tasks.
    # Railway automatically provides a REDIS_URL if you provision a Redis service.
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    # Define the queue name for audit tasks
    RQ_QUEUE_NAME = "audit_tasks"

    # --- Other Application Config ---
    # Example: Define the maximum number of seconds an audit can run before timing out
    MAX_AUDIT_TIMEOUT = 300 # 5 minutes

class DevelopmentConfig(Config):
    """Configuration for local development."""
    DEBUG = True

class ProductionConfig(Config):
    """Configuration for production deployment (Railway)."""
    DEBUG = False
    
    # Ensure SSL is strictly required in production
    if Config.SQLALCHEMY_DATABASE_URI.startswith("postgresql"):
        if "sslmode=require" not in Config.SQLALCHEMY_DATABASE_URI:
            Config.SQLALCHEMY_DATABASE_URI += "&sslmode=require" 


# Export a dictionary for easy config loading in app.py
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig # Or ProductionConfig if deploying immediately
}
