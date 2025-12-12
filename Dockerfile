
# ──────── Install system dependencies ────────
# WeasyPrint + PostgreSQL + Gunicorn compilation needs these
# ENSURE THIS SECTION IS RE-TYPED WITH STANDARD SPACES
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
