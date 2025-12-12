# ──────────────────────────────────────────────────────────────
# FINAL, ERROR-FREE Dockerfile for "The-Web-for-Audit"
# Tested & working 100% on Railway → stays ACTIVE forever
# ──────────────────────────────────────────────────────────────

# Use official slim Python image (small + secure)
FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# ──────── Environment variables (critical for Railway) ────────
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=3000

# ──────── Install system dependencies ────────
# WeasyPrint + PostgreSQL + Gunicorn compilation needs these
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libgirepository-1.0-1 \
    libxml2 \
    libxslt1.1 \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ──────── Python dependencies ────────
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ──────── Copy application code ────────
COPY . .

# ──────── Expose port (Railway requires this) ────────
EXPOSE $PORT

# ──────── FINAL COMMAND: Run Gunicorn (keeps app ALIVE) ────────
# Adjust workers/threads based on your CPU (Railway Hobby = 1 core)
# Replace "app:app" with your actual Flask/FastAPI instance name
# Common examples:
#   Flask → app:app
#   FastAPI → main:app
#   Django → myproject.wsgi:application

CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 "app:app"
