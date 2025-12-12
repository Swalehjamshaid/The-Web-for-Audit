# Dockerfile - FINAL ROBUST VERSION
FROM python:3.13-slim-bookworm

WORKDIR /app

ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Install system dependencies for WeasyPrint and PostgreSQL
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

# Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE $PORT

# CRITICAL FIX: Targets the 'application' instance, resolving the "Failed to find attribute 'app'" error.
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 300 "app:application"
