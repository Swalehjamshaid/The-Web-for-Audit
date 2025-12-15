# Use Python 3.10 slim as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# ---------------------------
# System dependencies
# ---------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    python3-dev \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpango1.0-dev \
    # FIX: Using the correct, modern package names for gdk-pixbuf
    libgdk-pixbuf-xlib-2.0-0 \
    libgdk-pixbuf-xlib-2.0-dev \
    libffi-dev \
    libjpeg-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------
# Copy requirements
# ---------------------------
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies (Ensures psycopg2-binary and Flask-SQLAlchemy are installed)
# ADDED tenacity here for database retry logic
RUN pip install --no-cache-dir -r requirements.txt tenacity

# ---------------------------
# Copy app code
# ---------------------------
COPY . .

# Set environment variables for Railway (Use 8080/PORT for Railway consistency)
ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=8080 \
    RQ_QUEUE=default

# Expose port
EXPOSE 8080

# The CMD is mainly a fallback; the actual start command is set in railway.toml
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT --workers 2"]
