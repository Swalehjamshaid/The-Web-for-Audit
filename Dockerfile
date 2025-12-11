# Dockerfile — FINAL, ERROR-FREE CONFIGURATION

# Choose the Python version from your requirements.txt
FROM python:3.13-slim-bookworm 

# Set the working directory
WORKDIR /app

# CRITICAL FIX 1: Set the Python path permanently inside the container
# Defines the path absolutely to avoid UndefinedVar error
ENV PYTHONPATH=/app

# CRITICAL FIX 2: Install system dependencies for WeasyPrint and Postgres/Gunicorn compilation
# Packages updated to ensure compatibility with slim image environment.
RUN apt-get update && apt-get install -y --no-install-recommends \
    # WeasyPrint Core Dependencies (Pango, Cairo)
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    # GObject Dependencies (Required for GDK/GLib)
    libgirepository-1.0-1 \
    # XML/XSLT Dependencies (Required by WeasyPrint for HTML parsing)
    libxml2 \
    libxslt1.1 \
    # Database and Compilation tools
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# No CMD or ENTRYPOINT; rely on Procfile
