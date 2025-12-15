# ---------------------------
# Base image
# ---------------------------
FROM python:3.10-slim

# ---------------------------
# Set Working Directory
# ---------------------------
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
    # FIX: Updated libgdk-pixbuf package names to resolve build failure on Debian Trixie
    libgdk-pixbuf-xlib-2.0-0 \
    libgdk-pixbuf-xlib-2.0-dev \
    libffi-dev \
    libjpeg-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------
# Copy requirements and install
# ---------------------------
COPY requirements.txt .

# Upgrade pip first
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------
# Copy project files
# ---------------------------
COPY . .

# ---------------------------
# Environment variables for Railway
# ---------------------------
ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=8080 \
    RQ_QUEUE=default

# ---------------------------
# Expose port
# ---------------------------
EXPOSE 8080

# ---------------------------
# Start Flask + RQ (CMD is a fallback, but defines the image entry point)
# ---------------------------
CMD ["sh", "-c", "\
    echo 'Starting RQ worker...' & \
    rq worker $RQ_QUEUE & \
    echo 'Starting Flask web app with Gunicorn...' & \
    gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 300 \
"]
