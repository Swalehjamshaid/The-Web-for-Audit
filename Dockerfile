# Use a Python base image
FROM python:3.13-slim-bookworm 

# Install system dependencies required by WeasyPrint and Postgres/Gunicorn compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libgobject-2.0-0 \
    libglib2.0-0 \
    libxml2 \
    libxslt \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# CRITICAL FIX 1: Set the Python path permanently inside the container
ENV PYTHONPATH=/app:$PYTHONPATH 

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Do NOT define CMD or ENTRYPOINT; rely on Procfile
